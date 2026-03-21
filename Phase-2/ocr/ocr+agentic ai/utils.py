import pytesseract
import re
import difflib
from PIL import Image

# Define expected test names and their regex patterns
EXPECTED_KEYS = {
    'TSH': r'TSH[:\s]*([\d.,]+)',
    'T3': r'T3[:\s]*([\d.,]+)',
    'T4': r'T4[:\s]*([\d.,]+)',
    'Glucose': r'Glucose[:\s]*([\d.,]+)',
    'HbA1c': r'HbA1c[:\s]*([\d.,]+)',
    'Hemoglobin': r'Hemoglobin[:\s]*([\d.,]+)',
    'RBC': r'RBC[:\s]*([\d.,]+)',
    'Creatinine': r'Creatinine[:\s]*([\d.,]+)',
    'Urea': r'Urea[:\s]*([\d.,]+)'
}

def clean_ocr_text(raw_text):
    """Clean and normalize OCR output for better extraction."""
    text = raw_text.replace('|', ':').replace('{', '').replace('}', '')
    text = re.sub(r'\s{2,}', ' ', text)  # Collapse multiple spaces
    return text

def fuzzy_find(text, keyword, cutoff=0.6):
    """Find closest match in OCR output for fuzzy keyword matching."""
    words = re.findall(r'\w+', text.lower())  # normalize text
    matches = difflib.get_close_matches(keyword.lower(), words, n=1, cutoff=cutoff)
    return matches[0] if matches else None




def extract_lab_values(text):
    """Extract lab test values using regex and fuzzy matching, supporting comma/period decimals."""
    results = {}
    text = text.replace(",", ".")  # Ensure uniform decimal format

    for key, pattern in EXPECTED_KEYS.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            results[key] = match.group(1).strip()
        else:
            fuzzy_key = fuzzy_find(text, key)
            if fuzzy_key:
                fallback_pattern = rf"{re.escape(fuzzy_key)}[^\d]*([\d.]+)"
                match = re.search(fallback_pattern, text, re.IGNORECASE)
                results[key] = match.group(1).strip() if match else None
            else:
                results[key] = None

    print("\n=== Extracted Lab Values ===")
    for k, v in results.items():
        print(f"{k}: {v}")
    return results

    

def process_image(image_path):
    """Perform OCR on image and return extracted & cleaned text."""
    print("[INFO] Processing image:", image_path)
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)

        print("\n=== OCR Text Extracted ===\n")
        print(text)

        cleaned_text = clean_ocr_text(text)
        return cleaned_text
    except Exception as e:
        print("[ERROR] Failed to process image:", e)
        return ""



def check_sufficient_values(lab_values, min_required=5):
    """Check if at least `min_required` lab values are present (not None)."""
    present_values = [v for v in lab_values.values() if v is not None]
    return len(present_values) >= min_required