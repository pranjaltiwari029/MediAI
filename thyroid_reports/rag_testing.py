import os
import sqlite3
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import pytesseract
from pytesseract import Output
from PIL import Image
from reports_db_3 import init_db, add_report, get_report, get_all_reports
import re
from transformers import RagTokenizer, RagRetriever, RagSequenceForGeneration

# Initialize the Flask application
app = Flask(__name__)

# Configure the upload folder and allowed file extensions
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize the database
init_db()

# Load RAG components
rag_tokenizer = RagTokenizer.from_pretrained("facebook/rag-token-nq")
rag_retriever = RagRetriever.from_pretrained("facebook/rag-token-nq")
rag_model = RagSequenceForGeneration.from_pretrained("facebook/rag-token-nq")

# Check if file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Process the uploaded image and extract structured OCR data
def process_image(image_path):
    image = Image.open(image_path)
    ocr_data = pytesseract.image_to_data(image, output_type=Output.DICT)
    return ocr_data

# Extract text from OCR data
def extract_values(ocr_data):
    lines = []
    current_line = []
    last_y = ocr_data['top'][0]  # Track vertical position
    for i in range(len(ocr_data['text'])):
        text = ocr_data['text'][i].strip()
        if text:
            if abs(ocr_data['top'][i] - last_y) > 10:
                lines.append(" ".join(current_line))
                current_line = []
                last_y = ocr_data['top'][i]
            current_line.append(text)
    if current_line:
        lines.append(" ".join(current_line))
    return "\n".join(lines)

# Function to query RAG for additional insights
def query_rag(ocr_text):
    inputs = rag_tokenizer(ocr_text, return_tensors="pt", truncation=True, padding=True)
    # Retrieve relevant documents based on the query (OCR text)
    retrieved_docs = rag_retriever(input_ids=inputs['input_ids'], return_tensors="pt")
    
    # Generate a response using the model and retrieved documents
    generated_ids = rag_model.generate(input_ids=inputs['input_ids'], context_input_ids=retrieved_docs['context_input_ids'])
    generated_text = rag_tokenizer.decode(generated_ids[0], skip_special_tokens=True)
    return generated_text

# Analyze the OCR text based on thyroid conditions
def analyze_text(ocr_text):
    # Predefined thresholds for thyroid markers
    thresholds = {
        "T3": {"low": 0.69, "high": 2.15},
        "T4": {"low": 52, "high": 127},
        "TSH": {"low": 0.3, "high": 4.5}
    }

    findings = []
    thyroid_detected = False

    def analyze_parameter(parameter, thresholds):
        match = re.search(rf"{parameter}.*?(\d+(\.\d+)?)", ocr_text, re.IGNORECASE)
        if match:
            value = float(match.group(1))  # Extract numeric value
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

    for param, threshold in thresholds.items():
        if analyze_parameter(param, threshold):
            thyroid_detected = True

    if thyroid_detected:
        findings.append("Thyroid detected based on abnormal T3, T4, or TSH levels.")
    else:
        findings.append("Thyroid not detected; all levels are within the normal range.")

    # Now, query RAG to provide additional insights based on the OCR text
    rag_analysis = query_rag(ocr_text)
    findings.append(f"RAG Insights: {rag_analysis}")

    return "\n".join(findings)

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

        ocr_data = process_image(file_path)
        ocr_text = extract_values(ocr_data)

        # Analyze the extracted text and include RAG-based insights
        analysis = analyze_text(ocr_text)

        # Add the report details to the database
        report_id = add_report(filename, ocr_text, analysis)

        return jsonify({'message': 'Report uploaded successfully', 'report_id': report_id}), 201

    return jsonify({'error': 'Invalid file format'}), 400

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

@app.route('/reports', methods=['GET'])
def get_all_report_details():
    reports = get_all_reports()
    return jsonify([{
        'id': report[0],
        'filename': report[1],
        'analysis': report[2]
    } for report in reports])

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
