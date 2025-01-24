from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
from PIL import Image
from reports_db import init_db, add_report, get_report, get_all_reports
import sqlite3
import os
import pytesseract

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Initialize SQLite database
DATABASE = 'reports_1.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS reports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        filename TEXT,
                        ocr_text TEXT,
                        analysis TEXT
                    )''')
    conn.commit()
    conn.close()

# Run the init_db function to create the table if it doesn't exist
init_db()

# Helper function for analyzing typhoid report text
def analyze_text(text):
    # Basic analysis example: checking for keywords related to typhoid diagnosis
    if 'typhoid' in text.lower() and ('positive' in text.lower() or 'detected' in text.lower()):
        return "Typhoid detected in report."
    elif 'typhoid' in text.lower() and 'negative' in text.lower():
        return "Typhoid not detected in report."
    else:
        return "No clear indication of typhoid in report."


    
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    # Perform OCR on the uploaded image
    image = Image.open(file_path)
    ocr_text = pytesseract.image_to_string(image)
    analysis_result = analyze_text(ocr_text)
    
    # Insert OCR text and analysis result into the database
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO reports (filename, ocr_text, analysis) VALUES (?, ?, ?)", 
                   (filename, ocr_text, analysis_result))
    report_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({"message": "File uploaded and processed", "id": report_id})

@app.route('/retrieve/<int:id>', methods=['GET'])
def retrieve_report(id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT filename, ocr_text, analysis FROM reports WHERE id = ?", (id,))
    report = cursor.fetchone()
    conn.close()
    
    if report:
        filename, ocr_text, analysis = report
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            return jsonify({
                "id": id,
                "filename": filename,
                "ocr_text": ocr_text,
                "analysis": analysis
            })
        else:
            return jsonify({"error": "File not found"}), 404
    else:
        return jsonify({"error": "Report not found"}), 404
    
# @app.route('/reports', methods=['GET'])
# def get_all_report_details():
#     reports = get_all_reports()
#     return jsonify([{
#         'id': report[0],
#         'filename': report[1],
#         'analysis': report[2]
#     } for report in reports])

if __name__ == '__main__':
    app.run(debug=True)


# database used = reports_1.db