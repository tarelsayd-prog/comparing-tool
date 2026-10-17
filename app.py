import streamlit as st
from google import genai
from google.genai import types
from PIL import Image

# Initialize Gemini Client (automatically reads GEMINI_API_KEY from Streamlit Secrets)
try:
    client = genai.Client()
except Exception as e:
    st.error("Please configure GEMINI_API_KEY in your Streamlit Secrets.")

SYSTEM_PROMPT = """
# Role
You are an expert e-commerce product matching assistant. Your primary task is to help users find the exact equivalent of Amazon products on Noon.com (specifically Noon Egypt or the relevant regional Noon store).

# Objective
Take user inputs—which may include Amazon product URLs, HTML source files, product images, or text descriptions—identify the exact product, and return the direct, raw URL for that product on Noon.com.

# Instructions
1. Analyze the input (extract brand, model, size, color/variant).
2. Locate the identical product on Noon.com matching the exact variant.
3. Provide the direct, raw URL (e.g., https://www.noon.com/egypt-en/...).
4. State clearly if a product is unavailable on Noon.
"""

st.set_page_config(page_title="Amazon to Noon Matcher", page_icon="🛒", layout="centered")
st.title("🛒 Amazon to Noon Product Matcher")

input_method = st.radio("Choose Input Method:", ("Upload Product Image", "Paste Amazon Link"))

user_prompt = ""
image_to_process = None

if input_method == "Upload Product Image":
    uploaded_file = st.file_uploader("Upload product image", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        image_to_process = Image.open(uploaded_file)
        st.image(image_to_process, caption="Uploaded Product", use_column_width=True)
        user_prompt = "Find this exact product on Noon Egypt and provide the raw direct link."

elif input_method == "Paste Amazon Link":
    amazon_link = st.text_input("Paste Amazon URL here:")
    if amazon_link:
        user_prompt = f"Find the equivalent of this Amazon product on Noon Egypt and provide the raw direct link: {amazon_link}"

if st.button("Find on Noon"):
    if not user_prompt:
        st.warning("Please provide an image or a link first.")
    else:
        with st.spinner("Searching for matches..."):
            try:
                contents = [user_prompt]
                if image_to_process:
                    contents.append(image_to_process)
                
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
