import os
import json
import pickle
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from utils import process_image, extract_lab_values, check_sufficient_values
from database import init_db, insert_report, get_all_reports
from agents import SimpleAgent

# Initialize Flask app
app = Flask(__name__)

# Upload folder for saving images
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Allowed file types for image uploads
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}

# Load ML model, scaler & label encoder
MODEL_PATH = os.path.join("model", "disease_model.pkl")
SCALER_PATH = os.path.join("model", "scaler.pkl")
ENCODER_PATH = os.path.join("model", "label_encoder.pkl")

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

with open(SCALER_PATH, "rb") as f:
    scaler = pickle.load(f)

with open(ENCODER_PATH, "rb") as f:
    label_encoder = pickle.load(f)

# Instantiate Agent
agent = SimpleAgent()

# Lab keys used in training
LAB_KEYS = ["TSH", "T3", "T4", "Glucose", "HbA1c", "Hemoglobin", "RBC", "Creatinine", "Urea"]


def allowed_file(filename):
    """Check if uploaded filename is valid."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def home():
    return jsonify({"message": "MediAI Backend Running Successfully"})


@app.route("/predict", methods=["POST"])
def predict():
    """Normal OCR + prediction API (not agentic)."""

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Empty file name"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        # Step 1: OCR
        extracted_text = process_image(filepath)

        # Step 2: Lab value extraction
        lab_values = extract_lab_values(extracted_text)

        # Step 3: Prediction
        values = []
        for key in LAB_KEYS:
            v = lab_values.get(key, None)
            if v is None:
                return jsonify({
                    "error": "Missing lab values for prediction",
                    "missing_key": key,
                    "lab_values": lab_values
                }), 400

            values.append(float(v))

        import pandas as pd
        df = pd.DataFrame([values], columns=LAB_KEYS)
        df_scaled = scaler.transform(df)
        prediction = model.predict(df_scaled)
        predicted_label = label_encoder.inverse_transform(prediction)[0]

        # Step 4: Save report
        from database import get_connection
        conn = get_connection()
        report_id = insert_report(conn, filename, extracted_text, predicted_label, lab_values)
        conn.close()

        return jsonify({
            "report_id": report_id,
            "filename": filename,
            "lab_values": lab_values,
            "prediction": predicted_label
        })

    return jsonify({"error": "Unsupported file format"}), 400


# ------------------------- AGENT ENDPOINTS -----------------------------

@app.route("/agent/run", methods=["POST"])
def run_agent():
    """
    Agentic AI endpoint:
    - If file uploaded -> run agent on file
    - If JSON with report_id -> run agent on saved report
    """

    # Case 1 → File upload
    if "file" in request.files:
        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            # Run agent
            plan = agent.run_on_file(filepath, filename)
            return jsonify(plan), 200

        return jsonify({"error": "Invalid file format"}), 400

    # Case 2 → JSON body with report_id
    data = request.get_json(silent=True)
    if data and "report_id" in data:
        report_id = int(data["report_id"])
        plan = agent.run_on_report(report_id)
        return jsonify(plan), 200

    return jsonify({
        "error": "Provide a file OR JSON {report_id: <id>}"
    }), 400


# ------------------------- ALERTS ENDPOINT -----------------------------

@app.route("/alerts", methods=["GET"])
def show_alerts():
    """List all urgent alerts triggered by the agent."""
    from database import get_alerts
    alerts = get_alerts(limit=100)

    formatted = [{
        "alert_id": a[0],
        "report_id": a[1],
        "level": a[2],
        "message": a[3],
        "created_at": a[4]
    } for a in alerts]

    return jsonify(formatted)


# ------------------------- REPORT LIST -----------------------------

@app.route("/reports", methods=["GET"])
def list_reports():
    """Show list of reports (simple)."""
    rows = get_all_reports()
    data = []
    for r in rows:
        data.append({
            "report_id": r[0],
            "filename": r[1],
            "analysis": r[2]
        })
    return jsonify(data)


# ------------------------- MAIN APP RUNNER -----------------------------

if __name__ == "__main__":
    # Initialize DB tables
    init_db()
    print("Database initialized. Starting MediAI server...")

    app.run(host="0.0.0.0", port=5000, debug=True)
