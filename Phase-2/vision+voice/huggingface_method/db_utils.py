# db_utils.py

import sqlite3
import os
from datetime import datetime

DB_PATH = "reports.db"

def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                response TEXT NOT NULL,
                audio TEXT,
                image_path TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

def save_to_db(query, response, audio_path=None, image_path=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        "INSERT INTO reports (query, response, audio, image_path) VALUES (?, ?, ?, ?)",
        (query, response, audio_path, image_path)
    )
    conn.commit()
    conn.close()
