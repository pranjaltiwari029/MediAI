import os
import pandas as pd
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from dblow import init_db, add_report, get_report, get_all_reports
from utilslow import process_image, extract_lab_values

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

init_db()

LAB_KEYS = ["TSH", "T3", "T4", "Glucose", "Hemoglobin", "Creatinine", "WBC", "RBC", "Platelets"]

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



def predict_disease(lab_values):
    try:
        glucose = lab_values.get("Glucose")
        tsh = lab_values.get("TSH")
        t3 = lab_values.get("T3")
        t4 = lab_values.get("T4")
        hb = lab_values.get("Hemoglobin")
        creatinine = lab_values.get("Creatinine")
        wbc = lab_values.get("WBC")
        rbc = lab_values.get("RBC")
        platelets = lab_values.get("Platelets")

        # Rules
        if glucose and glucose > 140:
            return "Likely Diabetes - High Glucose"
        
        if tsh and tsh > 4.5:
            if t3 and t3 < 0.8 or t4 and t4 < 5.0:
                return "Likely Hypothyroidism - High TSH + Low T3/T4"
            return "Possible Hypothyroidism - Elevated TSH"

        if tsh and tsh < 0.4:
            if t3 and t3 > 2.0 or t4 and t4 > 12.0:
                return "Likely Hyperthyroidism - Low TSH + High T3/T4"

        if hb and hb < 10:
            return "Likely Anemia - Low Hemoglobin"

        if creatinine and creatinine > 1.3:
            return "Possible Kidney Dysfunction - High Creatinine"

        if wbc and wbc > 11.0:
            return "Possible Infection - Elevated WBC Count"

        if platelets and platelets < 150:
            return "Possible Thrombocytopenia - Low Platelet Count"

        if rbc and rbc < 3.5:
            return "Possible Anemia - Low RBC Count"

        return "Insufficient lab values or all values in normal range"

    except Exception as e:
        return f"Error in prediction: {str(e)}"


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

        ocr_text = process_image(file_path)
        lab_values = extract_lab_values(ocr_text)
        prediction = predict_disease(lab_values)
        report_id = add_report(filename, ocr_text, lab_values, prediction)

        return jsonify({
            'message': 'Report uploaded successfully',
            'report_id': report_id,
            'disease_prediction': prediction
        }), 201
    return jsonify({'error': 'Invalid file format'}), 400

@app.route('/report/<int:report_id>', methods=['GET'])
def get_report_details(report_id):
    report = get_report(report_id)
    if report:
        filename, ocr_text, lab_values, analysis = report
        return jsonify({
            'filename': filename,
            'ocr_text': ocr_text,
            'lab_values': lab_values,
            'analysis': analysis
        })
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
