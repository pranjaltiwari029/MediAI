# agent.py
import os
import json
import pickle
import datetime

from utils import process_image, extract_lab_values, check_sufficient_values
from database import get_connection, insert_report, insert_alert, get_report
import pandas as pd

MODEL_DIR = "model"
MODEL_PATH = os.path.join(MODEL_DIR, "disease_model.pkl")
ENCODER_PATH = os.path.join(MODEL_DIR, "label_encoder.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.pkl")

LAB_KEYS = ["TSH", "T3", "T4", "Glucose", "HbA1c", "Hemoglobin", "RBC", "Creatinine", "Urea"]

class SimpleAgent:
    def __init__(self):
        # load model artifacts (these are already used in app.py)
        with open(MODEL_PATH, "rb") as f:
            self.model = pickle.load(f)
        with open(ENCODER_PATH, "rb") as f:
            self.label_encoder = pickle.load(f)
        with open(SCALER_PATH, "rb") as f:
            self.scaler = pickle.load(f)

        self.urgent_conditions = {"Kidney Disease", "Diabetes"}  # can extend

    def _predict(self, lab_values):
        # lab_values: dict of LAB_KEYS -> string or numeric
        values = []
        for k in LAB_KEYS:
            v = lab_values.get(k)
            try:
                values.append(float(v))
            except Exception:
                return None, "Insufficient or invalid numeric values for prediction"

        df = pd.DataFrame([values], columns=LAB_KEYS)
        df_scaled = self.scaler.transform(df)
        pred = self.model.predict(df_scaled)
        return self.label_encoder.inverse_transform(pred)[0], None

    def run_on_file(self, file_path, filename=None):
        # Orchestrates: OCR -> extract -> check -> predict -> save -> plan
        ocr_text = process_image(file_path)
        lab_values_full = extract_lab_values(ocr_text)
        lab_values = {k: lab_values_full.get(k) for k in LAB_KEYS}

        present_count = len([v for v in lab_values.values() if v is not None])
        sufficient = check_sufficient_values(lab_values, min_required=6)

        plan = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "input_filename": filename or os.path.basename(file_path),
            "present_values_count": present_count,
            "missing_keys": [k for k, v in lab_values.items() if v is None],
            "actions": []
        }

        if not sufficient:
            plan["actions"].append({
                "action": "request_more_data",
                "reason": "Not enough lab values extracted for reliable prediction",
                "missing_fields": plan["missing_keys"],
                "suggestion": "Ask user to upload a clearer image or provide missing lab values manually."
            })
            # Save partial report and return plan
            conn = get_connection()
            report_id = insert_report(conn, plan["input_filename"], ocr_text, "Insufficient lab values for prediction :-", lab_values)
            conn.close()
            plan["saved_report_id"] = report_id
            plan["status"] = "incomplete"
            return plan

        # else run prediction
        prediction, err = self._predict(lab_values)
        if err:
            plan["actions"].append({"action": "prediction_failed", "reason": err})
            conn = get_connection()
            report_id = insert_report(conn, plan["input_filename"], ocr_text, "Prediction error", lab_values)
            conn.close()
            plan["saved_report_id"] = report_id
            plan["status"] = "error"
            return plan

        # Create friendly explanation
        descriptions = {
            "Diabetes": "High likelihood of Diabetes (elevated glucose/HbA1c). Recommend fasting glucose, HbA1c confirmatory tests and endocrine consult.",
            "Thyroid": "Possible Thyroid dysfunction (abnormal TSH/T3/T4). Recommend repeat thyroid panel and endocrine consult.",
            "Anemia": "Findings suggest Anemia (low Hemoglobin/RBC). Recommend CBC repeat, iron studies and physician review.",
            "Kidney Disease": "Possible kidney dysfunction (abnormal creatinine/urea). Recommend nephrology referral and repeat renal function tests.",
            "Healthy": "No significant abnormalities."
        }
        explanation = descriptions.get(prediction, f"Indication: {prediction}. Advise clinical correlation.")

        plan["actions"].append({"action": "prediction", "disease": prediction, "explanation": explanation})

        # If urgent, insert an alert
        if prediction in self.urgent_conditions:
            alert_msg = f"URGENT: {prediction} indicated. Immediate clinical follow-up recommended."
            conn = get_connection()
            report_id = insert_report(conn, plan["input_filename"], ocr_text, prediction, lab_values)
            insert_alert(conn, report_id, level="high", message=alert_msg)
            conn.close()
            plan["saved_report_id"] = report_id
            plan["alert"] = {"level": "high", "message": alert_msg}
            plan["status"] = "alerted"
        else:
            conn = get_connection()
            report_id = insert_report(conn, plan["input_filename"], ocr_text, prediction, lab_values)
            conn.close()
            plan["saved_report_id"] = report_id
            plan["status"] = "completed"

        # Add a recommended next steps list
        plan["recommended_next_steps"] = [
            explanation,
            "If report image is low quality, request clearer image or manual lab value input.",
            "If urgent, call the patient and arrange immediate consult."
        ]

        return plan

    def run_on_report(self, report_id):
        # Load a saved report, re-evaluate or generate plan
        report = get_report(report_id)
        if not report:
            return {"error": "report not found", "report_id": report_id}
        filename, ocr_text, lab_values_json, analysis = report
        try:
            lab_values = json.loads(lab_values_json) if isinstance(lab_values_json, str) else lab_values_json
        except Exception:
            # fallback: try to extract again
            lab_values = extract_lab_values(ocr_text)

        # reuse run_on_file style logic by temporarily saving OCR->file if needed.
        # But we'll just predict directly:
        present_count = len([v for v in lab_values.values() if v is not None])
        plan = {
            "report_id": report_id,
            "filename": filename,
            "present_values_count": present_count,
            "missing_keys": [k for k, v in lab_values.items() if v is None],
            "actions": []
        }

        if present_count < 6:
            plan["actions"].append({"action": "insufficient_values", "suggestion": "Ask for missing lab values manually or upload clearer report."})
            plan["status"] = "incomplete"
            return plan

        prediction, err = self._predict(lab_values)
        if err:
            plan["actions"].append({"action": "prediction_failed", "reason": err})
            plan["status"] = "error"
            return plan

        plan["actions"].append({"action": "prediction", "disease": prediction})
        plan["recommended_next_steps"] = [f"Explanation: {prediction} — clinical correlation recommended."]
        plan["status"] = "completed"
        return plan
