import sqlite3
import os

# Consistent DB path
DB_PATH = " database.db"

def init_db():
    print("Initializing database...")
    print("Using database at:", os.path.abspath(DB_PATH))

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            response TEXT NOT NULL,
            image_filepath TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("Database initialized and table created if not exists.")

def save_to_db(query, response, image_path=None):
    print("Saving to database...")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO reports (query, response, image_filepath) VALUES (?, ?, ?)",
        (query, response, image_path)
    )
    conn.commit()
    conn.close()
    print("Data saved successfully.")
