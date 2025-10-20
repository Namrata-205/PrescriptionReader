import streamlit as st
from google.cloud import vision
import os
from google.genai import Client
import re

load_dotenv()  # Make sure you have a .env file in the same folder
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error("Gemini API key not found! Please set GEMINI_API_KEY in .env file.")
# ------------------- GOOGLE API SETUP -------------------
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "client_secret_code1.json"
vision_client = vision.ImageAnnotatorClient()
gemini_client = Client(api_key=GEMINI_API_KEY)  # Replace with your Gemini API key

# ------------------- STREAMLIT UI -------------------
st.set_page_config(page_title="Prescription Parser", page_icon="💊")
st.title("💊 Prescription OCR + Parsing + Autocorrect (Gemini Flash 200)")
st.write(
    "Upload a prescription image. Text will be extracted using Vision AI, autocorrected, and structured using Gemini Flash 200."
)

uploaded_file = st.file_uploader("Upload Prescription Image", type=["png", "jpg", "jpeg"])

if uploaded_file:
    st.image(uploaded_file, caption="Uploaded Prescription", use_column_width=True)

    # ------------------- OCR -------------------
    content = uploaded_file.read()
    image = vision.Image(content=content)
    ocr_response = vision_client.text_detection(image=image)
    texts = ocr_response.text_annotations

    if ocr_response.error.message:
        st.error(f"Vision API Error: {ocr_response.error.message}")
    elif texts:
        extracted_text = texts[0].description

        # ------------------- Pre-filter OCR text -------------------
        filtered_lines = []
        for line in extracted_text.split("\n"):
            line_lower = line.lower()
            if (
                "dr." in line_lower
                or "hospital" in line_lower
                or "ayurvedics" in line_lower
                or re.search(r"\d{2,4}/\d{1,2}/\d{2,4}", line)  # date
                or re.search(r"\d{4,}", line)  # long numbers (phone, IDs)
                or re.search(r"mob|res|main road|edavilangu|kodungallur", line_lower)
            ):
                continue
            if line.strip():  # only non-empty lines
                filtered_lines.append(line.strip())

        filtered_text = "\n".join(filtered_lines)
        st.text_area("Filtered Prescription Text", filtered_text, height=200)

        # ------------------- Parsing & Autocorrect with Gemini -------------------
        prompt = f"""
You are a medical assistant. The following prescription text may contain OCR errors.
1. Correct any misread words (e.g., "in the every" → "in the evening").
2. Extract only medicine names, dosages, and instructions for taking the medicine.
3. Only include "How to take" if it is explicitly mentioned.
4. Output must be in this format exactly:

Medicine name:
Dosage:
How to take: (if explicitly mentioned)

Prescription Text:
{filtered_text}
"""

        try:
            gemini_response = gemini_client.generate_text(
                model="gemini-flash-200",
                prompt=prompt,
                temperature=0.0,
                max_output_tokens=500
            )

            parsed_output = gemini_response.text
            st.subheader("📝 Parsed & Autocorrected Medicines")
            st.text_area("Structured Output", parsed_output, height=300)

        except Exception as e:
            st.error(f"Gemini API Error: {e}")
    else:
        st.warning("No text detected in the image.")
