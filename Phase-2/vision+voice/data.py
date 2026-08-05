import sqlite3
import os

DB_PATH = "reports2.db"

def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_query_audio TEXT,        -- Path to original audio
                patient_query_text TEXT NOT NULL, -- Transcribed text
                doctor_response_text TEXT NOT NULL,
                doctor_response_audio TEXT,      -- Path to doctor's voice reply (MP3)
                image_path TEXT,                 -- Path to uploaded image
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

def save_to_db(
    patient_query_audio,
    patient_query_text,
    doctor_response_text,
    doctor_response_audio=None,
    image_path=None
):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        '''
        INSERT INTO reports (
            patient_query_audio,
            patient_query_text,
            doctor_response_text,
            doctor_response_audio,
            image_path
        ) VALUES (?, ?, ?, ?, ?)
        ''',
        (
            patient_query_audio,
            patient_query_text,
            doctor_response_text,
            doctor_response_audio,
            image_path
        )
    )
    conn.commit()
    conn.close()
