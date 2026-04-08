import pytesseract
import re
import difflib
from PIL import Image

# ----------------------------
# CONFIG
# ----------------------------

LAB_KEYS = ["TSH", "T3", "T4", "Glucose", "HbA1c", "Hemoglobin", "RBC", "Creatinine", "Urea"]

ALIASES = {
    "TSH": [r"\bTSH\b"],
    "T3": [r"\bT3\b"],
    "T4": [r"\bT4\b"],
    "Glucose": [r"\bGlucose\b"],
    "HbA1c": [r"\bHbA1c\b", r"\bHDAIC\b", r"\bHbAlc\b", r"\bHBA1C\b"],
    "Hemoglobin": [r"\bHemoglobin\b", r"\bHemogloblin\b", r"\bHemogioblin\b"],
    "RBC": [r"\bRBC\b"],
    "Creatinine": [r"\bCreatinine\b"],
    "Urea": [r"\bUrea\b"]
}

SANITY_RANGES = {
    "TSH": (0, 100),
    "T3": (0, 20),
    "T4": (0, 30),
    "Glucose": (20, 600),
    "HbA1c": (2, 20),
    "Hemoglobin": (3, 25),
    "RBC": (1, 10),
    "Creatinine": (0, 20),
    "Urea": (1, 300)
}

METADATA_SKIP_NUMBERS = {
    "2025", "2026", "09", "15", "14", "13", "12", "11", "10",
    "60", "59", "58", "57", "56", "55"
}


# ----------------------------
# OCR TEXT CLEANING
# ----------------------------

def clean_ocr_text(raw_text):
    """Clean and normalize OCR output for better extraction."""
    text = raw_text.replace("|", " ")
    text = text.replace("{", "").replace("}", "")
    text = text.replace("—", " ").replace("–", " ")
    text = text.replace(":", " : ")
    text = text.replace("(", " ").replace(")", " ")
    text = text.replace("[", " ").replace("]", " ")

    # keep line structure but normalize spaces
    text = re.sub(r"[^\S\r\n]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)

    return text.strip()


# ----------------------------
# FUZZY MATCH
# ----------------------------

def fuzzy_find(text, keyword, cutoff=0.75):
    """Find closest fuzzy match for OCR keyword errors."""
    words = re.findall(r'\w+', text.lower())
    matches = difflib.get_close_matches(keyword.lower(), words, n=1, cutoff=cutoff)
    return matches[0] if matches else None


# ----------------------------
# NUMERIC CLEANING
# ----------------------------

def clean_numeric(value):
    """Extract and clean first valid numeric token."""
    if not value:
        return None

    value = value.strip()

    # OCR decimal fixes
    value = value.replace(",", ".")
    value = value.replace("O", "0").replace("o", "0")

    # Fix isolated OCR noise
    value = value.replace("..", ".")
    value = value.replace(". .", ".")
    value = value.replace(" ", "")

    match = re.search(r"\d+(?:\.\d+)?", value)
    if match:
        return match.group(0)

    return None


def is_valid_range(key, value):
    """Check if extracted value falls in medically plausible range."""
    try:
        f = float(value)
        low, high = SANITY_RANGES[key]
        return low <= f <= high
    except:
        return False


# ----------------------------
# EXTRACTION HELPERS
# ----------------------------

def extract_number_after_keyword(line, keyword_pattern):
    """
    Extract the first numeric value AFTER a keyword match in the line.
    This prevents wrong values from earlier parts of the line.
    """
    match = re.search(keyword_pattern, line, re.IGNORECASE)
    if not match:
        return None

    remainder = line[match.end():]
    num_match = re.search(r"[-]?\d+(?:[.,]\d+)?", remainder)
    if num_match:
        return clean_numeric(num_match.group(0))

    return None


def extract_all_candidate_numbers(text):
    """Extract all numeric tokens from OCR text."""
    nums = re.findall(r"\d+(?:[.,]\d+)?", text)
    cleaned = [clean_numeric(n) for n in nums if clean_numeric(n)]
    return cleaned


# ----------------------------
# MAIN LAB EXTRACTION
# ----------------------------

def extract_lab_values(text):
    """
    Robust lab value extraction:
    1. Line-by-line strict extraction
    2. Fuzzy OCR misspelling recovery
    3. Ordered fallback for broken table OCR
    """
    results = {key: None for key in LAB_KEYS}

    text = text.replace(",", ".")
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    print("\n=== OCR LINES ===")
    for i, line in enumerate(lines):
        print(f"{i+1}: {line}")

    # -----------------------------------
    # STEP 1: STRICT LINE-BY-LINE MATCHING
    # -----------------------------------
    for line in lines:
        for key, patterns in ALIASES.items():
            if results[key] is not None:
                continue

            for pat in patterns:
                num = extract_number_after_keyword(line, pat)
                if num and is_valid_range(key, num):
                    results[key] = num
                    break

    # -----------------------------------
    # STEP 2: FUZZY LINE MATCHING
    # -----------------------------------
    for key in LAB_KEYS:
        if results[key] is not None:
            continue

        fuzzy_key = fuzzy_find(text, key)
        if fuzzy_key:
            for line in lines:
                if fuzzy_key.lower() in line.lower():
                    idx = line.lower().find(fuzzy_key.lower())
                    remainder = line[idx + len(fuzzy_key):]

                    num_match = re.search(r"[-]?\d+(?:[.,]\d+)?", remainder)
                    if num_match:
                        num = clean_numeric(num_match.group(0))
                        if num and is_valid_range(key, num):
                            results[key] = num
                            break

    # -----------------------------------
    # STEP 3: ORDERED TABLE FALLBACK
    # -----------------------------------
    missing_keys = [k for k, v in results.items() if v is None]

    if missing_keys:
        print("\n[INFO] Trying ordered fallback extraction...")

        all_numbers = extract_all_candidate_numbers(text)
        print("[INFO] All OCR numbers found:", all_numbers)

        filtered_numbers = [n for n in all_numbers if n not in METADATA_SKIP_NUMBERS]
        print("[INFO] Filtered candidate values:", filtered_numbers)

        # If enough likely lab values exist, assume last 9 belong to table
        if len(filtered_numbers) >= 9:
            ordered_values = filtered_numbers[-9:]
            print("[INFO] Ordered fallback values used:", ordered_values)

            for key, val in zip(LAB_KEYS, ordered_values):
                if results[key] is None and is_valid_range(key, val):
                    results[key] = val

    # -----------------------------------
    # STEP 4: FINAL SANITY CLEANUP
    # -----------------------------------
    for key, val in results.items():
        if val is not None and not is_valid_range(key, val):
            print(f"[WARNING] {key} -> {val} rejected as implausible")
            results[key] = None

    print("\n=== Extracted Lab Values ===")
    for k, v in results.items():
        print(f"{k}: {v}")

    return results


# ----------------------------
# OCR IMAGE PROCESSING
# ----------------------------

def process_image(image_path):
    """Perform OCR on image and return extracted & cleaned text."""
    print("[INFO] Processing image:", image_path)

    try:
        img = Image.open(image_path)

        # Convert to grayscale for slightly better OCR consistency
        img = img.convert("L")

        # OCR
        text = pytesseract.image_to_string(img)

        print("\n=== OCR Text Extracted ===\n")
        print(text)

        cleaned_text = clean_ocr_text(text)
        return cleaned_text

    except Exception as e:
        print("[ERROR] Failed to process image:", e)
        return ""


# ----------------------------
# SUFFICIENCY CHECK
# ----------------------------

def check_sufficient_values(lab_values, min_required=5):
    """Check if at least `min_required` lab values are present (not None)."""
    present_values = [v for v in lab_values.values() if v is not None]
    return len(present_values) >= min_required