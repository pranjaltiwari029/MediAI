import os
import pickle
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
from database import init_db, insert_report, get_report, get_all_reports,get_connection
# from utils_old import  process_image,extract_lab_values,check_sufficient_values,create_feature_vector
from utils import  process_image,extract_lab_values,check_sufficient_values

# Initialize Flask app
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize database
init_db()

# Load trained model, label encoder, and scaler
with open("model/disease_model.pkl", "rb") as f:
    model = pickle.load(f)

with open("model/label_encoder.pkl", "rb") as f:
    label_encoder = pickle.load(f)

with open("model/scaler.pkl", "rb") as f:
    scaler = pickle.load(f)

# Lab value mapping for diseases
LAB_KEYS = ["TSH", "T3", "T4", "Glucose", "HbA1c", "Hemoglobin", "RBC", "Creatinine", "Urea"]

# Function to check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Predict disease
def predict_disease(lab_values):
    values = list(lab_values.values())
    if None in values:
        print("[WARNING] Insufficient lab values:")
        for key, value in lab_values.items():
            print(f"{key}: {value}")
        return "Insufficient lab values for prediction"

    df = pd.DataFrame([values], columns=LAB_KEYS)
    print("[INFO] Lab values as DataFrame:")
    print(df)

    df_scaled = scaler.transform(df)
    prediction = model.predict(df_scaled)
    return label_encoder.inverse_transform(prediction)[0]

def get_disease_explanation(prediction):
    descriptions = {
        "Diabetes": "The lab results indicate a high likelihood of Diabetes based on elevated glucose and HbA1c levels.",
        "Thyroid": "The lab results suggest potential Thyroid dysfunction, likely due to irregular TSH, T3, or T4 levels.",
        "Anemia": "The test results point towards Anemia, indicated by low Hemoglobin or RBC count.",
        "Kidney Disease": "The analysis suggests possible Kidney dysfunction due to abnormal Creatinine and Urea values.",
        "Healthy": "No significant abnormalities detected. Lab values appear within normal range.",
        "Insufficient lab values for prediction :-": "Not enough lab values were extracted to make a reliable prediction."
    }
    return descriptions.get(prediction, f"Possible indication of {prediction}, further analysis required.")

# Upload Endpoint
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

        print("[INFO] Image saved to:", file_path)

        ocr_text = process_image(file_path)
        print("\n=== OCR Text Extracted ===\n")
        print(ocr_text)

        lab_values_full = extract_lab_values(ocr_text)
        lab_values = {k: lab_values_full.get(k) for k in LAB_KEYS}

        print("\n=== Extracted Lab Values ===\n")
        for k, v in lab_values.items():
            print(f"{k}: {v}")

        if not check_sufficient_values(lab_values, min_required=6):
            prediction = "Insufficient lab values for prediction :-"
            explanation = "Not enough lab values were extracted to make a reliable prediction."
        else:
            prediction = predict_disease(lab_values)
            # Add a human-readable explanation
            descriptions = {
                "Diabetes": "The lab results indicate a high likelihood of Diabetes based on elevated glucose and HbA1c levels.",
                "Thyroid": "The lab results suggest potential Thyroid dysfunction, likely due to irregular TSH, T3, or T4 levels.",
                "Anemia": "The test results point towards Anemia, indicated by low Hemoglobin or RBC count.",
                "Kidney Disease": "The analysis suggests possible Kidney dysfunction due to abnormal Creatinine and Urea values.",
                "Healthy": "No significant abnormalities detected. Lab values appear within normal range."
            }
            explanation = descriptions.get(prediction, f"Possible indication of {prediction}, further analysis required.")

        # Save report in DB
        conn = get_connection()
        report_id = insert_report(conn, filename, ocr_text, prediction, lab_values)
        conn.close()

        return jsonify({
            'message': 'Report uploaded successfully',
            'report_id': report_id,
            'disease_prediction': explanation , # Now it's descriptive
            
        }), 201

    return jsonify({'error': 'Invalid file format'}), 400



# Get Report by ID

@app.route('/report/<int:report_id>', methods=['GET'])
def get_report_details(report_id):
    report = get_report(report_id)
    if report:
        filename, ocr_text, lab_values, analysis = report
        return jsonify({
            'filename': filename,
            'ocr_text': ocr_text,
            'lab_values': lab_values,
            'analysis': analysis,
            'disease_prediction': get_disease_explanation(analysis)
        })
    return jsonify({'error': 'Report not found'}), 404


# Get All Reports
@app.route('/reports', methods=['GET'])
def get_all_report_details():
    reports = get_all_reports()
    return jsonify([{
        'id': report[0],
        'filename': report[1],
        'analysis': report[2],
        'disease_prediction': get_disease_explanation(report[2])
    } for report in reports])

# Main Entry
if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
