# used with app2.py (database= reports.db)

import sqlite3

DB_PATH = 'reports.db'

def init_db():
    """Initialize the database and create the reports table if it doesn't exist."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS reports (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            filename TEXT,
                            ocr_text TEXT,
                            analysis TEXT
                        )''')
        conn.commit()

def add_report(filename, ocr_text, analysis):
    """Add a new report entry to the database."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO reports (filename, ocr_text, analysis)
            VALUES (?, ?, ?)
        ''', (filename, ocr_text, analysis))
        conn.commit()
        return cursor.lastrowid  # Return the ID of the new report

def get_report(report_id):
    """Retrieve a report by its ID."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT filename, ocr_text, analysis FROM reports WHERE id = ?
        ''', (report_id,))
        result = cursor.fetchone()
        return result if result else None  # Return the report details if found

def get_all_reports():
    """Retrieve all reports from the database."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, filename, analysis FROM reports')
        return cursor.fetchall()  # Returns all reports' ID, filename, and analysis summary
