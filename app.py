import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import requests
from bs4 import BeautifulSoup
from io import BytesIO

# --- Configuration ---
try:
    client = genai.Client()
except Exception as e:
    st.error("Error initializing the client. Please ensure GEMINI_API_KEY is configured in your Secrets.")

# --- System Prompt ---
SYSTEM_PROMPT = """
# Role
You are an expert e-commerce product matching assistant. Your primary task is to help users find the exact equivalent of Amazon products on Noon.com (specifically Noon Egypt).

# Objective
Take user inputs (product images, titles, descriptions) identify the exact product, and return the direct, raw URL for that product on Noon.com.

# Instructions
1. **Analyze the Input:** Extract the brand, product name, variant (e.g., shade, color, flavor), and size/weight.
2. **Search and Match:** Locate the identical product on Noon.com matching the exact brand, model, size, and variant. 
3. **Format the Output:**
   - Always provide the direct, raw clickable URL (e.g., `https://www.noon.com/egypt-en/...`).
   - Do not bury the link in Markdown text.
   - List the matched product name clearly above its respective URL.
4. **Handle Missing Items:** If a product is completely unavailable on Noon, state clearly that it is out of stock or not carried by Noon.
"""

def fetch_amazon_details(url):
    """Scrape the product title and main image URL from an Amazon link."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Get Title
        title_tag = soup.find(id="productTitle")
        title = title_tag.get_text(strip=True) if title_tag else "Product title not found"
        
        # Get Main Image
        image_tag = soup.find(id="landingImage")
        image_url = image_tag.get("src") if image_tag else None
        
        return title, image_url
    except Exception as e:
        return None, None

# --- Streamlit UI ---
st.set_page_config(page_title="Amazon to Noon Matcher", page_icon="🛒", layout="centered")

st.title("🛒 Amazon to Noon Product Matcher")
st.write("Upload product images or paste an Amazon link to fetch details and get the direct Noon.com URL.")

input_method = st.radio("Choose Input Method:", ("Upload Product Images", "Paste Amazon Link"))

user_prompt = ""
images_to_process = []

if input_method == "Upload Product Images":
    uploaded_files = st.file_uploader("Upload product images (JPG/PNG)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    
    if uploaded_files:
        for file in uploaded_files:
            img = Image.open(file)
            images_to_process.append(img)
            st.image(img, caption=f"Uploaded: {file.name}", use_container_width=True)
            
        user_prompt = "Find these exact products on Noon Egypt and provide the raw direct link for each."

elif input_method == "Paste Amazon Link":
    amazon_link = st.text_input("Paste Amazon URL here:")
    if amazon_link:
        with st.spinner("Fetching product details from Amazon..."):
            title, image_url = fetch_amazon_details(amazon_link)
            
            if title:
                st.write(f"**Fetched Title:** {title}")
                user_prompt = f"Find the equivalent of this product on Noon Egypt and provide the raw direct link. Product Title: {title}"
                
                if image_url:
                    img_response = requests.get(image_url)
                    img = Image.open(BytesIO(img_response.content))
                    images_to_process.append(img)
                    st.image(img, caption="Fetched Amazon Image", use_container_width=True)
            else:
                st.warning("Could not fetch details from Amazon. The link might be invalid or Amazon blocked the request. Proceeding with the raw URL...")
                user_prompt = f"Find the equivalent of this Amazon product on Noon Egypt and provide the raw direct link: {amazon_link}"

# --- Processing ---
if st.button("Find on Noon"):
    if not user_prompt:
        st.warning("Please provide an image or a link first.")
    else:
        with st.spinner("Searching Noon for matches..."):
            try:
                contents = [user_prompt]
                if images_to_process:
                    contents.extend(images_to_process)
                
                response = client.models.generate_content(
                    model='gemini-3.5-flash-lite',
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                    )
                )
                
                st.success("Search Complete!")
                st.markdown("### Results:")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"An error occurred: {e}")

st.markdown("---")
st.markdown("<small>Powered by Streamlit and Google Gemini 3.5 Flash Lite.</small>", unsafe_allow_html=True)
