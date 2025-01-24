import os
import sqlite3
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import pytesseract
from pytesseract import Output
from PIL import Image
from reports_db_3 import init_db, add_report, get_report, get_all_reports
import re

# Initialize the Flask application
app = Flask(__name__)

# Configure the upload folder and allowed file extensions
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize the database
init_db()

# Check if file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Process the uploaded image and extract structured OCR data
def process_image(image_path):
    # Open the image using PIL
    image = Image.open(image_path)
    # Extract structured OCR data
    ocr_data = pytesseract.image_to_data(image, output_type=Output.DICT)
    return ocr_data

# Extract text from OCR data while maintaining line structure
def extract_values(ocr_data):
    """
    Combines OCR data into structured lines for easier processing.
    """
    lines = []
    current_line = []
    last_y = ocr_data['top'][0]  # Track the vertical position
    
    for i in range(len(ocr_data['text'])):
        text = ocr_data['text'][i].strip()
        if text:
            # Check if we are still on the same line
            if abs(ocr_data['top'][i] - last_y) > 10: 
                lines.append(" ".join(current_line))
                current_line = []
                last_y = ocr_data['top'][i]
            current_line.append(text)
    if current_line:
        lines.append(" ".join(current_line))
    
    return "\n".join(lines)


def extract_value_from_line(line):
    
    match = re.search(r'(\d+:\d+|\d+)', line)
    if match:
        return match.group(0)
    return None

# Analyze the text based on values
# def analyze_text(ocr_text):
#     """
#     Analyze the OCR text to detect typhoid based on specific values.
#     """
#     # Define thresholds for typhoid detection (replace with actual medical criteria)
#     thresholds = {
#         "Antigen O": 160 ,  # Example: 1:80
#         "Antigen H": 160  # Example: 1:160
#     }
#     findings = {}

#     for key, threshold in thresholds.items():
#         # Search for antigen levels in the OCR text
#         antigen_match = re.search(rf"{key}.*?(\d+:\d+|\d+)", ocr_text, re.IGNORECASE)
#         if antigen_match:
#             value = antigen_match.group(1)
#             if ":" in value:
#                 # Extract the denominator of the ratio, e.g., 1:80 -> 80
#                 _, denominator = value.split(":")
#                 if int(denominator) >= threshold:
#                     findings[key] = f"{key} level indicates typhoid (found: {value})."
#                 else:
#                     findings[key] = f"{key} level is below threshold (found: {value})."
#             else:
#                 # Handle standalone numeric values
#                 if int(value) >= threshold:
#                     findings[key] = f"{key} level indicates typhoid (found: {value})."
#                 else:
#                     findings[key] = f"{key} level is below threshold (found: {value})."

#     if findings:
#         return "Analysis Results:\n" + "\n".join(f"{k}: {v}" for k, v in findings.items())
#     else:
#         return "No specific typhoid-related antigen levels detected."

# def analyze_text(ocr_text):
#     """
#     Analyze the OCR text to detect typhoid based on antigen levels.
#     """
#     # Define thresholds for typhoid detection
#     thresholds = {
#         "O Antigen": 160,
#         "H Antigen": 160
#     }

#     findings = []

#     for antigen, threshold in thresholds.items():
#         # Search for antigen levels in the OCR text
#         match = re.search(rf"{antigen}.*?(\d+:\d+|\d+)", ocr_text, re.IGNORECASE)
#         if match:
#             value = match.group(1)
#             # Extract the numeric part (e.g., 1:160 -> 160)
#             level = int(value.split(":")[-1]) if ":" in value else int(value)
#             if level >= threshold:
#                 findings.append(f"{antigen}: Detected (level: {value}).")
#             else:
#                 findings.append(f"{antigen}: Not detected (level: {value}, below threshold).")

#     if findings:
#         return "Analysis Results:\n" + "\n".join(findings)
#     return "No typhoid-related antigen levels detected."

# def analyze_text(ocr_text):
#     """
#     Analyze the OCR text to detect thyroid issues based on T3 levels.
#     """
#     # Define thresholds for T3 detection (replace these values with actual medical criteria)
#     t3_thresholds = {
#         "low": 0.69,   # Example lower threshold for T3
#         "high": 2.15  # Example upper threshold for T3
#     }

#     findings = []

#     # Search for T3 levels in the OCR text
#     match = re.search(r"T3.*?(\d+:\d+|\d+)", ocr_text, re.IGNORECASE)
#     if match:
#         value = match.group(1)
#         # Extract the numeric part (e.g., 1:160 -> 160)
#         t3_level = int(value.split(":")[-1]) if ":" in value else int(value)

#         # Analyze T3 level
#         if t3_level < t3_thresholds["low"]:
#             findings.append(f"T3: Below normal (level: {t3_level}, expected ≥ {t3_thresholds['low']}).")
#         elif t3_level > t3_thresholds["high"]:
#             findings.append(f"T3: Above normal (level: {t3_level}, expected ≤ {t3_thresholds['high']}).")
#         else:
#             findings.append(f"T3: Normal (level: {t3_level}).")
#     else:
#         findings.append("T3 levels not detected in the report.")

#     # Return the findings
#     return "\n".join(findings)

def analyze_text(ocr_text):
    """
    Analyze the OCR text to detect thyroid issues based on T3, T4, and TSH levels.
    """
    # Define thresholds for T3, T4, and TSH detection (replace these values with actual medical criteria)
    thresholds = {
        "T3": {"low": 0.69, "high": 2.15},  # Example thresholds for T3
        "T4": {"low": 52, "high": 127},  # Example thresholds for T4
        "TSH": {"low": 0.3, "high": 4.5}   # Example thresholds for TSH
    }

    findings = []
    thyroid_detected = False

    # Function to analyze a specific parameter
    def analyze_parameter(parameter, thresholds):
        match = re.search(rf"{parameter}.*?(\d+(\.\d+)?)", ocr_text, re.IGNORECASE)
        if match:
            value = float(match.group(1))  # Extract the numeric value
            if value < thresholds["low"]:
                findings.append(f"{parameter}: Below normal (level: {value}, expected ≥ {thresholds['low']}).")
                return True
            elif value > thresholds["high"]:
                findings.append(f"{parameter}: Above normal (level: {value}, expected ≤ {thresholds['high']}).")
                return True
            else:
                findings.append(f"{parameter}: Normal (level: {value}).")
        else:
            findings.append(f"{parameter} levels not detected in the report.")
        return False

    # Analyze T3, T4, and TSH
    for param, threshold in thresholds.items():
        if analyze_parameter(param, threshold):
            thyroid_detected = True

    # Add final conclusion
    if thyroid_detected:
        findings.append("Thyroid detected based on abnormal T3, T4, or TSH levels.")
    else:
        findings.append("Thyroid not detected; all levels are within the normal range.")

    return "\n".join(findings)

# API for uploading and processing medical reports
@app.route('/upload', methods=['POST'])
def upload_report():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Extract structured OCR data
        ocr_data = process_image(file_path)
        ocr_text = extract_values(ocr_data)

        # Analyze the extracted text
        analysis = analyze_text(ocr_text)

        # Add the report details to the database
        report_id = add_report(filename, ocr_text, analysis)

        return jsonify({'message': 'Report uploaded successfully', 'report_id': report_id}), 201

    return jsonify({'error': 'Invalid file format'}), 400

# API to retrieve a specific report by ID
@app.route('/report/<int:report_id>', methods=['GET'])
def get_report_details(report_id):
    report = get_report(report_id)
    if report:
        filename, ocr_text, analysis = report
        return jsonify({
            'filename': filename,
            'ocr_text': ocr_text,
            'analysis': analysis
        })
    else:
        return jsonify({'error': 'Report not found'}), 404

# API to retrieve all uploaded reports
@app.route('/reports', methods=['GET'])
def get_all_report_details():
    reports = get_all_reports()
    return jsonify([{
        'id': report[0],
        'filename': report[1],
        'analysis': report[2]
    } for report in reports])

# Run the app
if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
