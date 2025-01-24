import os
import sqlite3
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
from reports_db import init_db, add_report, get_report, get_all_reports

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

# Process the uploaded image and extract text using OCR
def process_image(image_path):
    # Open the image using PIL
    image = Image.open(image_path)
    # Use pytesseract to extract text
    ocr_text = pytesseract.image_to_string(image)
    return ocr_text

# Analyze the text (you can implement a more sophisticated analysis here)
def analyze_text(ocr_text):
    # For simplicity, we're returning a basic analysis here
    if 'typhoid' in ocr_text.lower() and ('positive' in ocr_text.lower() or 'detected' in ocr_text.lower()):
        return "Typhoid detected in report."
    elif 'typhoid' in ocr_text.lower() and 'negative' in ocr_text.lower():
        return "Typhoid not detected in report."
    else:
        return "No clear indication of typhoid in report."

# API for uploading and processing medical reports
@app.route('/upload', methods=['POST'])
def upload_report():
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    # If no file is selected
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # If the file is allowed
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Perform OCR to extract text
        ocr_text = process_image(file_path)
        
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
