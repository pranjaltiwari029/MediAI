
import os
import cv2
import pytesseract
from pdf2image import convert_from_path
from flask import Flask, request, render_template
from PIL import Image
import re

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def extract_text_from_image(image_path):
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    text = pytesseract.image_to_string(gray)
    return text

def extract_text_from_pdf(pdf_path):
    images = convert_from_path(pdf_path)
    full_text = ""
    for image in images:
        temp_image_path = os.path.join(UPLOAD_FOLDER, "temp_image.png")
        image.save(temp_image_path, "PNG")
        full_text += extract_text_from_image(temp_image_path)
    return full_text

def analyze_typhoid_report(text):
    keywords = {
        "typhi_o": r"Typhi[ -]?O.*(\d+)",
        "typhi_h": r"Typhi[ -]?H.*(\d+)",
        "paratyphi_a": r"Paratyphi[ -]?A.*(\d+)",
        "paratyphi_b": r"Paratyphi[ -]?B.*(\d+)",
        "normal_range": r"Normal Range.*:.*(\d+)[ -]?(\d+)"
    }

    results = {}
    for key, pattern in keywords.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            results[key] = match.group(1)

    analysis = "Analysis of Typhoid Report:\n"
    if results.get("typhi_o") and int(results["typhi_o"]) > 160:
        analysis += "Elevated Typhi O level detected, which may indicate active infection.\n"
    if results.get("typhi_h") and int(results["typhi_h"]) > 160:
        analysis += "Elevated Typhi H level detected, indicating past or current infection.\n"
    if results.get("paratyphi_a") and int(results["paratyphi_a"]) > 160:
        analysis += "Elevated Paratyphi A level detected, suggesting possible infection.\n"
    if results.get("paratyphi_b") and int(results["paratyphi_b"]) > 160:
        analysis += "Elevated Paratyphi B level detected, suggesting possible infection.\n"
    if not any(int(value) > 160 for value in results.values()):
        analysis += "All values appear within normal range. No signs of active typhoid infection detected.\n"

    return analysis

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["file"]
        if file:
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)

            if file.filename.lower().endswith(".pdf"):
                text = extract_text_from_pdf(file_path)
            else:
                text = extract_text_from_image(file_path)

            analysis = analyze_typhoid_report(text)
            return render_template("index.html", analysis=analysis, extracted_text=text)

    return render_template("index.html", analysis=None)

if __name__ == "__main__":
    app.run(debug=True)
