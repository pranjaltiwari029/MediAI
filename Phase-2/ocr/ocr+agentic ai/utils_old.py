import re
import cv2
import pytesseract
import numpy as np
import difflib
from PIL import Image
# --- Flexible lab value extractor ---

# def process_image(image_path):
#     """
#     Preprocesses the image and extracts text using OCR.
#     """
#     image = cv2.imread(image_path)

#     if image is None:
#         raise ValueError(f"Unable to load image from path: {image_path}")

#     # Convert to grayscale
#     gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

#     # Apply adaptive thresholding
#     thresh = cv2.adaptiveThreshold(
#         gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, 9
#     )

#     # Morphological operations to clean noise
#     kernel = np.ones((1, 1), np.uint8)
#     cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

#     # Perform OCR
#     custom_config = r'--oem 3 --psm 6'
#     text = pytesseract.image_to_string(cleaned, config=custom_config)

#     print("\n=== OCR Extracted Text ===")
#     print(text)

#     return text


def process_image(image_path):
    """OCR the uploaded image and return raw text."""
    image = cv2.imread(image_path)

    # Optional: preprocess to enhance clarity
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(gray, 255,
                                   cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 11, 2)

    # Run OCR with layout analysis
    custom_config = r'--oem 3 --psm 6'
    ocr_text = pytesseract.image_to_string(thresh, config=custom_config)

    print("[OCR TEXT] >>>", ocr_text)  # debug output

    return ocr_text

def extract_lab_values(text):
    # Normalize OCR text
    text = text.replace(":", " : ").replace("=", " = ").replace("-", " - ")
    text = re.sub(r'\s+', ' ', text)  # Collapse multiple spaces

    # Define only the lab tests used by the model
    lab_values = {
        "TSH": None,
        "T3": None,
        "T4": None,
        "Glucose": None,
        "Hemoglobin": None,
        "Creatinine": None,
        "Urea": None
    }

    # Custom regex patterns for more robustness
    patterns = {
        "TSH": r"(TSH|Thyroid[- ]?Stimulating[- ]?Hormone)[^\d]{0,10}([\d.]+)",
        "T3": r"(T3|Triiodothyronine)[^\d]{0,10}([\d.]+)",
        "T4": r"(T4|Thyroxine)[^\d]{0,10}([\d.]+)",
        "Glucose": r"(Glucose|Blood[- ]?Sugar)[^\d]{0,10}([\d.]+)",
        "Hemoglobin": r"(Hemoglobin|Hgb)[^\d]{0,10}([\d.]+)",
        "Creatinine": r"(Creatinine)[^\d]{0,10}([\d.]+)",
        "Urea": r"(Urea|BUN)[^\d]{0,10}([\d.]+)"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                value = float(match.group(2))
                lab_values[key] = value
            except ValueError:
                pass

    # Debugging output
    print("\n=== Extracted Lab Values ===")
    for k, v in lab_values.items():
        print(f"{k}: {v}")

    # Warn about missing ones
    missing = [k for k, v in lab_values.items() if v is None]
    if missing:
        print("\n[Warning] Could not extract values for:", ", ".join(missing))

    return lab_values



# def extract_lab_values(text):
#     # Normalize common formatting issues in OCR output
#     text = text.replace(":", " : ").replace("=", " = ").replace("-", " - ")
#     text = re.sub(r'\s+', ' ', text)  # collapse multiple spaces

#     lab_values = {
#         "TSH": None,
#         "T3": None,
#         "T4": None,
#         "Glucose": None,
#         "HbA1c": None,
#         "Hemoglobin": None,
#         "RBC": None,
#         "Creatinine": None,
#         "Urea": None
#     }

#     lines = text.split('\n')
#     for line in lines:
#         line = line.strip()
#         for key in lab_values.keys():
#             if key.lower() in line.lower():
#                 # Flexible pattern: Match number after keyword (allow colon, equal sign, etc.)
#                 match = re.search(rf"{key}\s*[:=\-]?\s*([\d.]+)", line, re.IGNORECASE)
#                 if match:
#                     try:
#                         lab_values[key] = float(match.group(1))
#                     except ValueError:
#                         pass

#     print("\n=== Extracted Lab Values ===")
#     for k, v in lab_values.items():
#         print(f"{k}: {v}")

#     return lab_values


# --- Check if enough data is present ---
def check_sufficient_values(lab_values):
    non_none_values = [v for v in lab_values.values() if v is not None]
    if len(non_none_values) < 4:
        print("[WARNING] Insufficient lab values:")
        for k, v in lab_values.items():
            print(f"{k}: {v}")
    return len(non_none_values) >= 4


# --- Create input vector for ML model from lab values ---
def create_feature_vector(lab_values, feature_order):
    return [lab_values.get(feature, 0.0) if lab_values.get(feature) is not None else 0.0 for feature in feature_order]
