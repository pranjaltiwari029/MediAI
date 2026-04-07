import gradio as gr
import requests
import pandas as pd
import json
import os
import textwrap
from datetime import datetime

# PDF generation
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from PIL import Image

# -----------------------------
# CONFIG
# -----------------------------
BACKEND_URL = "http://127.0.0.1:5000"
GENERATED_REPORTS_DIR = "generated_reports"

if not os.path.exists(GENERATED_REPORTS_DIR):
    os.makedirs(GENERATED_REPORTS_DIR)

# -----------------------------
# CUSTOM CSS
# -----------------------------
custom_css = """
body, .gradio-container {
    background: linear-gradient(135deg, #0b1220, #111827);
    font-family: 'Segoe UI', sans-serif;
}

.main-title {
    font-size: 2.2rem;
    font-weight: 800;
    color: white;
    margin-bottom: 0.3rem;
}

.subtitle {
    color: #cbd5e1;
    font-size: 1rem;
    margin-bottom: 1.2rem;
}

.section-title {
    font-size: 1.2rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 0.8rem;
}

.glass-card {
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 18px !important;
    padding: 18px !important;
    box-shadow: 0 8px 30px rgba(0,0,0,0.18) !important;
}

footer {display: none !important;}
"""

# -----------------------------
# GLOBAL STATE STORAGE
# -----------------------------
latest_agent_result = {}
latest_uploaded_image_path = None

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def safe_wrap_text(text, width=95):
    if not text:
        return []
    wrapped = []
    for paragraph in str(text).split("\n"):
        wrapped.extend(textwrap.wrap(paragraph, width=width))
        if paragraph.strip() == "":
            wrapped.append("")
    return wrapped


def draw_wrapped_text(c, text, x, y, max_width=95, line_height=14):
    lines = safe_wrap_text(text, width=max_width)
    for line in lines:
        c.drawString(x, y, line)
        y -= line_height
    return y


def format_agent_output(response_json):
    """
    Formats /agent/run response into clean UI outputs.
    """
    if not isinstance(response_json, dict):
        return "Invalid response format", "", "", "", "", "", "", "", "", "", None

    filename = response_json.get("input_filename", "N/A")
    status = response_json.get("status", "N/A")
    report_id = response_json.get("saved_report_id", "N/A")
    present_values = response_json.get("present_values_count", 0)
    missing_keys = response_json.get("missing_keys", [])

    actions = response_json.get("actions", [])
    recommended_steps = response_json.get("recommended_next_steps", [])
    alert = response_json.get("alert", {})

    disease = "N/A"
    explanation = "N/A"

    for action in actions:
        if action.get("action") == "prediction":
            disease = action.get("disease", "N/A")
            explanation = action.get("explanation", "N/A")

    missing_keys_text = ", ".join(missing_keys) if missing_keys else "None"
    steps_text = "\n".join([f"• {step}" for step in recommended_steps]) if recommended_steps else "No recommendations available."
    alert_text = f"{alert.get('level', '').upper()}: {alert.get('message', '')}" if alert else "No critical alert."

    return (
        filename,
        status,
        str(report_id),
        str(present_values),
        missing_keys_text,
        disease,
        explanation,
        steps_text,
        alert_text,
        json.dumps(response_json, indent=2),
        None
    )


def analyze_report_agent(file):
    """
    Calls /agent/run endpoint for smart agentic analysis.
    """
    global latest_agent_result, latest_uploaded_image_path

    if file is None:
        return ("No file uploaded", "", "", "", "", "", "", "", "", "", None)

    try:
        latest_uploaded_image_path = file.name

        with open(file.name, "rb") as f:
            files = {"file": (os.path.basename(file.name), f)}
            response = requests.post(f"{BACKEND_URL}/agent/run", files=files)

        if response.status_code == 200:
            data = response.json()
            latest_agent_result = data

            return format_agent_output(data)

        else:
            latest_agent_result = {}
            return (
                "Error",
                f"HTTP {response.status_code}",
                "",
                "",
                "",
                "",
                response.text,
                "",
                "",
                response.text,
                None
            )

    except Exception as e:
        latest_agent_result = {}
        return (
            "Exception",
            str(e),
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            str(e),
            None
        )


def direct_predict(file):
    """
    Calls /predict endpoint for direct OCR + ML prediction.
    """
    if file is None:
        return "No file uploaded", "", "", pd.DataFrame(columns=["Lab Parameter", "Value"])

    try:
        with open(file.name, "rb") as f:
            files = {"file": (os.path.basename(file.name), f)}
            response = requests.post(f"{BACKEND_URL}/predict", files=files)

        if response.status_code == 200:
            data = response.json()
            report_id = data.get("report_id", "N/A")
            filename = data.get("filename", "N/A")
            prediction = data.get("prediction", "N/A")
            lab_values = data.get("lab_values", {})

            lab_df = pd.DataFrame(list(lab_values.items()), columns=["Lab Parameter", "Value"])
            return filename, str(report_id), prediction, lab_df

        else:
            try:
                err = response.json()
                return "Error", "", json.dumps(err, indent=2), pd.DataFrame(columns=["Lab Parameter", "Value"])
            except:
                return "Error", "", response.text, pd.DataFrame(columns=["Lab Parameter", "Value"])

    except Exception as e:
        return "Exception", "", str(e), pd.DataFrame(columns=["Lab Parameter", "Value"])


def fetch_reports():
    """
    Calls /reports endpoint and returns report history table.
    """
    try:
        response = requests.get(f"{BACKEND_URL}/reports")
        if response.status_code == 200:
            data = response.json()
            if not data:
                return pd.DataFrame(columns=["Report ID", "Filename", "Analysis"])
            df = pd.DataFrame(data)
            df = df.rename(columns={
                "report_id": "Report ID",
                "filename": "Filename",
                "analysis": "Analysis"
            })
            return df
        else:
            return pd.DataFrame([{
                "Report ID": "Error",
                "Filename": f"HTTP {response.status_code}",
                "Analysis": response.text
            }])
    except Exception as e:
        return pd.DataFrame([{
            "Report ID": "Exception",
            "Filename": "Connection Failed",
            "Analysis": str(e)
        }])


def fetch_alerts():
    """
    Calls /alerts endpoint and returns alerts table.
    """
    try:
        response = requests.get(f"{BACKEND_URL}/alerts")
        if response.status_code == 200:
            data = response.json()
            if not data:
                return pd.DataFrame(columns=["Alert ID", "Report ID", "Level", "Message", "Created At"])
            df = pd.DataFrame(data)
            df = df.rename(columns={
                "alert_id": "Alert ID",
                "report_id": "Report ID",
                "level": "Level",
                "message": "Message",
                "created_at": "Created At"
            })
            return df
        else:
            return pd.DataFrame([{
                "Alert ID": "Error",
                "Report ID": "",
                "Level": f"HTTP {response.status_code}",
                "Message": response.text,
                "Created At": ""
            }])
    except Exception as e:
        return pd.DataFrame([{
            "Alert ID": "Exception",
            "Report ID": "",
            "Level": "Connection Failed",
            "Message": str(e),
            "Created At": ""
        }])


# -----------------------------
# PDF REPORT GENERATION
# -----------------------------
def generate_pdf_report():
    """
    Generates a downloadable PDF clinical summary from latest agent result.
    """
    global latest_agent_result, latest_uploaded_image_path

    if not latest_agent_result or not latest_uploaded_image_path:
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename_only = os.path.splitext(os.path.basename(latest_uploaded_image_path))[0]
    output_pdf = os.path.join(GENERATED_REPORTS_DIR, f"MediAI_Clinical_Report_{filename_only}_{timestamp}.pdf")

    c = canvas.Canvas(output_pdf, pagesize=A4)
    width, height = A4
    y = height - 50

    # -----------------------------
    # HEADER
    # -----------------------------
    c.setFont("Helvetica-Bold", 20)
    c.drawString(40, y, "MediAI - AI Clinical Summary Report")
    y -= 25

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.grey)
    c.drawString(40, y, f"Generated on: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
    c.setFillColor(colors.black)
    y -= 30

    # -----------------------------
    # METADATA
    # -----------------------------
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "1. Report Metadata")
    y -= 20

    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Filename: {latest_agent_result.get('input_filename', 'N/A')}")
    y -= 16
    c.drawString(50, y, f"Report ID: {latest_agent_result.get('saved_report_id', 'N/A')}")
    y -= 16
    c.drawString(50, y, f"Status: {latest_agent_result.get('status', 'N/A')}")
    y -= 16
    c.drawString(50, y, f"Extracted Values Count: {latest_agent_result.get('present_values_count', 'N/A')}")
    y -= 25

    # -----------------------------
    # IMAGE PREVIEW
    # -----------------------------
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "2. Uploaded Medical Report Preview")
    y -= 20

    try:
        img = Image.open(latest_uploaded_image_path)
        img_width, img_height = img.size

        max_width = 5.5 * inch
        max_height = 3.8 * inch

        ratio = min(max_width / img_width, max_height / img_height)
        new_width = img_width * ratio
        new_height = img_height * ratio

        c.drawImage(
            latest_uploaded_image_path,
            50,
            y - new_height,
            width=new_width,
            height=new_height,
            preserveAspectRatio=True,
            mask='auto'
        )
        y = y - new_height - 25
    except Exception:
        c.setFont("Helvetica", 11)
        c.drawString(50, y, "Unable to render uploaded report image.")
        y -= 25

    # New page if too low
    if y < 220:
        c.showPage()
        y = height - 50

    # -----------------------------
    # LAB VALUES
    # -----------------------------
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "3. OCR Extraction Summary")
    y -= 20

    missing_keys = latest_agent_result.get("missing_keys", [])
    missing_keys_text = ", ".join(missing_keys) if missing_keys else "None"

    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Missing Lab Keys: {missing_keys_text}")
    y -= 25

    # -----------------------------
    # DISEASE + EXPLANATION
    # -----------------------------
    disease = "N/A"
    explanation = "N/A"

    for action in latest_agent_result.get("actions", []):
        if action.get("action") == "prediction":
            disease = action.get("disease", "N/A")
            explanation = action.get("explanation", "N/A")

    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "4. AI Clinical Finding")
    y -= 20

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"Predicted Disease: {disease}")
    y -= 20

    c.setFont("Helvetica", 11)
    y = draw_wrapped_text(c, f"Clinical Explanation: {explanation}", 50, y, max_width=90)
    y -= 15

    # -----------------------------
    # NEXT STEPS
    # -----------------------------
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "5. Recommended Next Steps")
    y -= 20

    c.setFont("Helvetica", 11)
    for step in latest_agent_result.get("recommended_next_steps", []):
        wrapped_lines = safe_wrap_text(f"• {step}", width=90)
        for line in wrapped_lines:
            c.drawString(50, y, line)
            y -= 14
        y -= 4

    # -----------------------------
    # ALERT
    # -----------------------------
    y -= 10
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "6. Alert Status")
    y -= 20

    alert = latest_agent_result.get("alert", {})
    alert_text = f"{alert.get('level', '').upper()}: {alert.get('message', '')}" if alert else "No critical alert generated."

    c.setFont("Helvetica", 11)
    y = draw_wrapped_text(c, alert_text, 50, y, max_width=90)
    y -= 20

    # -----------------------------
    # DISCLAIMER
    # -----------------------------
    if y < 120:
        c.showPage()
        y = height - 50

    c.setFont("Helvetica-Bold", 13)
    c.drawString(40, y, "7. Disclaimer")
    y -= 20

    disclaimer = (
        "This report is AI-assisted and intended for decision support purposes only. "
        "It should not be considered a final medical diagnosis. All clinical findings "
        "must be reviewed and confirmed by a licensed healthcare professional."
    )

    c.setFont("Helvetica", 10)
    y = draw_wrapped_text(c, disclaimer, 50, y, max_width=95)

    c.save()
    return output_pdf


# -----------------------------
# UI
# -----------------------------
with gr.Blocks(title="MediAI OCR Dashboard", theme=gr.themes.Soft(), css=custom_css) as demo:
    gr.Markdown("""
    <div class="main-title">🏥 MediAI – Clinical OCR Intelligence Dashboard</div>
    <div class="subtitle">
    AI-powered medical report analysis with OCR, ML-based disease prediction, agentic reasoning, and clinical alert monitoring.
    </div>
    """)

    with gr.Tabs():

        # ==========================================================
        # TAB 1 - SMART REPORT ANALYSIS
        # ==========================================================
        with gr.Tab("🧠 Smart Analysis"):
            with gr.Group(elem_classes="glass-card"):
                gr.Markdown('<div class="section-title">Upload Report for Agentic Clinical Analysis</div>')

                agent_file = gr.File(
                    label="Upload Medical Report (Image)",
                    file_types=[".png", ".jpg", ".jpeg"]
                )
                analyze_btn = gr.Button("🚀 Run Smart Analysis", variant="primary")

            with gr.Row():
                filename_out = gr.Textbox(label="Filename")
                status_out = gr.Textbox(label="Status")
                report_id_out = gr.Textbox(label="Saved Report ID")

            with gr.Row():
                present_values_out = gr.Textbox(label="Extracted Values Count")
                missing_keys_out = gr.Textbox(label="Missing Lab Keys")

            with gr.Row():
                disease_out = gr.Textbox(label="Predicted Disease")
                explanation_out = gr.Textbox(label="Clinical Explanation", lines=4)

            with gr.Group(elem_classes="glass-card"):
                recommended_steps_out = gr.Textbox(label="Recommended Next Steps", lines=6)
                alert_out = gr.Textbox(label="Critical Alert", lines=2)

            with gr.Group(elem_classes="glass-card"):
                gr.Markdown("### 📄 Download AI Clinical Summary")
                generate_pdf_btn = gr.Button("Generate Downloadable PDF Summary")
                pdf_file_out = gr.File(label="Download Clinical Report")

            with gr.Accordion("🔍 View Raw JSON Response", open=False):
                raw_json_out = gr.Code(label="Raw JSON Response", language="json")

            analyze_btn.click(
                fn=analyze_report_agent,
                inputs=[agent_file],
                outputs=[
                    filename_out,
                    status_out,
                    report_id_out,
                    present_values_out,
                    missing_keys_out,
                    disease_out,
                    explanation_out,
                    recommended_steps_out,
                    alert_out,
                    raw_json_out,
                    pdf_file_out
                ]
            )

            generate_pdf_btn.click(
                fn=generate_pdf_report,
                inputs=[],
                outputs=[pdf_file_out]
            )

        # ==========================================================
        # TAB 2 - DIRECT ML PREDICTION
        # ==========================================================
        with gr.Tab("📊 Direct Prediction"):
            with gr.Group(elem_classes="glass-card"):
                gr.Markdown('<div class="section-title">Standard OCR + ML Prediction</div>')

                predict_file = gr.File(
                    label="Upload Medical Report (Image)",
                    file_types=[".png", ".jpg", ".jpeg"]
                )
                predict_btn = gr.Button("🔬 Run Direct Prediction", variant="primary")

            with gr.Row():
                pred_filename_out = gr.Textbox(label="Filename")
                pred_report_id_out = gr.Textbox(label="Report ID")
                pred_prediction_out = gr.Textbox(label="Prediction")

            with gr.Group(elem_classes="glass-card"):
                pred_lab_table = gr.Dataframe(label="Extracted Lab Values", interactive=False)

            predict_btn.click(
                fn=direct_predict,
                inputs=[predict_file],
                outputs=[
                    pred_filename_out,
                    pred_report_id_out,
                    pred_prediction_out,
                    pred_lab_table
                ]
            )

        # ==========================================================
        # TAB 3 - REPORT HISTORY
        # ==========================================================
        with gr.Tab("📁 Report History"):
            with gr.Group(elem_classes="glass-card"):
                gr.Markdown('<div class="section-title">Previously Analyzed Reports</div>')
                refresh_reports_btn = gr.Button("🔄 Refresh Reports")
                reports_table = gr.Dataframe(label="Saved Reports", interactive=False)

            refresh_reports_btn.click(
                fn=fetch_reports,
                inputs=[],
                outputs=[reports_table]
            )

        # ==========================================================
        # TAB 4 - CRITICAL ALERTS
        # ==========================================================
        with gr.Tab("🚨 Critical Alerts"):
            with gr.Group(elem_classes="glass-card"):
                gr.Markdown('<div class="section-title">Urgent Clinical Alerts</div>')
                refresh_alerts_btn = gr.Button("🔄 Refresh Alerts")
                alerts_table = gr.Dataframe(label="Critical Alerts", interactive=False)

            refresh_alerts_btn.click(
                fn=fetch_alerts,
                inputs=[],
                outputs=[alerts_table]
            )

# -----------------------------
# LAUNCH
# -----------------------------
if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7862)