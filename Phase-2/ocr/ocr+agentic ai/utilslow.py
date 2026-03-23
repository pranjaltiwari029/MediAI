import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re

def process_image(image_path):
    image = Image.open(image_path)
    gray = image.convert('L')
    enhanced = ImageEnhance.Contrast(gray).enhance(2)
    sharpened = enhanced.filter(ImageFilter.SHARPEN)
    text = pytesseract.image_to_string(sharpened)
    print("\n=== OCR TEXT ===\n", text)
    return text

def extract_lab_values(ocr_text):
    patterns = {
        "TSH": r"(TSH).{0,10}?([\d.]+)",
        "T3": r"(T3).{0,10}?([\d.]+)",
        "T4": r"(T4).{0,10}?([\d.]+)",
        "Glucose": r"(Glucose|Sugar).{0,10}?([\d.]+)",
        "Hemoglobin": r"(Hemoglobin|Hb).{0,10}?([\d.]+)",
        "Creatinine": r"(Creatinine).{0,10}?([\d.]+)",
        "WBC": r"(WBC).{0,10}?([\d.]+)",
        "RBC": r"(RBC).{0,10}?([\d.]+)",
        "Platelets": r"(Platelets).{0,10}?([\d.]+)"
    }

    extracted = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, ocr_text, re.IGNORECASE)
        if match:
            try:
                extracted[key] = float(match.group(2))
            except:
                extracted[key] = None
        else:
            extracted[key] = None

    print("\n=== Extracted Lab Values ===\n", extracted)
    return extracted
