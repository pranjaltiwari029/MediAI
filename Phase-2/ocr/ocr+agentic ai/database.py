# database.py (updated)
import sqlite3
import os
import json

DB_PATH = 'ocr_lab_reports.db'

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    """Create the reports and alerts tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            ocr_text TEXT,
            lab_values TEXT,
            analysis TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER,
            level TEXT,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(report_id) REFERENCES reports(id)
        )
    ''')
    conn.commit()
    conn.close()

def insert_report(conn, filename, ocr_text, analysis, lab_values):
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
    return cursor.lastrowid

def get_report(report_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT filename, ocr_text, lab_values, analysis FROM reports WHERE id = ?', (report_id,))
    report = cursor.fetchone()
    conn.close()
    return report

def get_all_reports():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, filename, analysis FROM reports')
    reports = cursor.fetchall()
    conn.close()
    return reports

# Alerts helpers
def insert_alert(conn, report_id, level, message):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO alerts (report_id, level, message)
        VALUES (?, ?, ?)
    ''', (report_id, level, message))
    conn.commit()
    return cursor.lastrowid

def get_alerts(limit=50):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, report_id, level, message, created_at FROM alerts ORDER BY created_at DESC LIMIT ?', (limit,))
    alerts = cursor.fetchall()
    conn.close()
    return alerts
