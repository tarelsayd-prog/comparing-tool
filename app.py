import streamlit as st
from google import genai
from google.genai import types
from PIL import Image

# --- Configuration ---
# Initialize the Gemini client. 
# Streamlit Cloud will automatically securely inject your GEMINI_API_KEY from its Secrets.
try:
    client = genai.Client()
except Exception as e:
    st.error("Error initializing the client. Please ensure GEMINI_API_KEY is configured in your Secrets.")

# --- System Prompt ---
SYSTEM_PROMPT = """
# Role
You are an expert e-commerce product matching assistant. Your primary task is to help users find the exact equivalent of Amazon products on Noon.com (specifically Noon Egypt or the relevant regional Noon store).

# Objective
Take user inputs—which may include Amazon product URLs, HTML source files, product images, or text descriptions—identify the exact product, and return the direct, raw URL for that product on Noon.com.

# Instructions
1. **Analyze the Input:** 
   - If given an image, use vision capabilities to extract the brand, product name, variant (e.g., shade, color, flavor), and size/weight.
   - If given an Amazon URL, extract the product title, brand, and specifications (you may need to ask the user for an image if the URL doesn't resolve).
2. **Search and Match:** 
   - Locate the identical product on Noon.com matching the exact brand, model, size, and variant. 
   - Pay strict attention to package sizes and color codes.
3. **Format the Output:**
   - Always provide the direct, raw clickable URL (e.g., `https://www.noon.com/egypt-en/...`).
   - Do not bury the link in Markdown text.
   - List the matched product name clearly above its respective URL.
4. **Handle Missing Items:** 
   - If a product is completely unavailable on Noon, state clearly that it is out of stock or not carried by Noon. Do not hallucinate links.
"""

# --- Streamlit UI ---
st.set_page_config(page_title="Amazon to Noon Matcher", page_icon="🛒", layout="centered")

st.title("🛒 Amazon to Noon Product Matcher")
st.write("Upload product images or paste an Amazon link to get the direct Noon.com URL.")

# Input options
input_method = st.radio("Choose Input Method:", ("Upload Product Images", "Paste Amazon Link"))

user_prompt = ""
images_to_process = []

if input_method == "Upload Product Images":
    # Accept multiple images
    uploaded_files = st.file_uploader("Upload product images (JPG/PNG)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    
    if uploaded_files:
        for file in uploaded_files:
            img = Image.open(file)
            images_to_process.append(img)
            # Display each uploaded image in the app
            st.image(img, caption=f"Uploaded: {file.name}", use_container_width=True)
            
        user_prompt = "Find these exact products on Noon Egypt and provide the raw direct link for each."

elif input_method == "Paste Amazon Link":
    amazon_link = st.text_input("Paste Amazon URL here:")
    if amazon_link:
        user_prompt = f"Find the equivalent of this Amazon product on Noon Egypt and provide the raw direct link: {amazon_link}"

# --- Processing ---
if st.button("Find on Noon"):
    if not user_prompt:
        st.warning("Please provide an image or a link first.")
    else:
        with st.spinner("Searching for matches..."):
            try:
                # Prepare contents for the model (text prompt + any images)
                contents = [user_prompt]
                if images_to_process:
                    contents.extend(images_to_process)
                
                # Generate response using Gemini 3.5 Flash Lite
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

# --- Footer ---
st.markdown("---")
st.markdown("<small>Powered by Streamlit and Google Gemini 3.5 Flash Lite.</small>", unsafe_allow_html=True)
