import sqlite3
import os
import json

DB_PATH = 'reports_1.db'

# --- Database Connection ---
def get_connection():
    return sqlite3.connect(DB_PATH)

# --- Initialize Database Table ---
def init_db():
    """Create the reports table if it doesn't exist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            ocr_text TEXT,
            lab_values TEXT,
            analysis TEXT
        )
    ''')
    conn.commit()
    conn.close()

# --- Insert New Report ---
def insert_report(conn, filename, ocr_text, analysis, lab_values):
    """
    Inserts a new report into the database.
    :param conn: sqlite3 connection object
    :param filename: Name of the file
    :param ocr_text: Extracted text from the report
    :param analysis: Predicted disease or message
    :param lab_values: Dictionary of lab values
    :return: report ID
    """
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO reports (filename, ocr_text, lab_values, analysis)
        VALUES (?, ?, ?, ?)
    ''', (
        filename,
        ocr_text,
        json.dumps(lab_values),
        analysis
    ))
    conn.commit()
    report_id = cursor.lastrowid
    print(f"[INFO] Report saved with ID: {report_id}")
    return report_id

# --- Fetch Single Report ---
def get_report(report_id):
    """Retrieve full report by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT filename, ocr_text, lab_values, analysis FROM reports WHERE id = ?', (report_id,))
    report = cursor.fetchone()
    conn.close()
    return report

# --- Fetch All Reports (Summary) ---
def get_all_reports():
    """Return ID, filename, and analysis for all reports."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, filename, analysis FROM reports')
    reports = cursor.fetchall()
    conn.close()
    return reports
