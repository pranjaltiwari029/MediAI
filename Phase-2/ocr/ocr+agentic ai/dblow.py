import sqlite3
import json

DB_NAME = "reports2.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                ocr_text TEXT,
                lab_values TEXT,
                analysis TEXT
            )
        ''')
        conn.commit()

def add_report(filename, ocr_text, lab_values, analysis):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO reports (filename, ocr_text, lab_values, analysis)
            VALUES (?, ?, ?, ?)
        ''', (filename, ocr_text, json.dumps(lab_values), analysis))
        conn.commit()
        return c.lastrowid

def get_report(report_id):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('SELECT filename, ocr_text, lab_values, analysis FROM reports WHERE id = ?', (report_id,))
        row = c.fetchone()
        if row:
            return row[0], row[1], json.loads(row[2]), row[3]
        return None

def get_all_reports():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('SELECT id, filename, analysis FROM reports')
        return c.fetchall()
