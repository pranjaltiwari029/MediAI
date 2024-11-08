import sqlite3


DB_PATH = 'image_DB.db'

def init_db():
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Create a table for storing images if it doesn't exist
        cursor.execute( "CREATE TABLE IF NOT EXISTS images ( id INTEGER PRIMARY KEY AUTOINCREMENT,image_hash TEXT UNIQUE,path TEXT,description TEXT)"
        )
        conn.commit()  

def add_image_description(image_hash, path, description):
    
     with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO images (image_hash, path, description)
            VALUES (?, ?, ?)
        ''', (image_hash, path, description))
        conn.commit()   

def get_image_description(image_hash):
    
     with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT description FROM images WHERE image_hash = ?
        ''', (image_hash,))
        result = cursor.fetchone()  # Fetch one result
        return result[0] if result else None  # Return the description if found 

def get_all_images():
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT path, description FROM images')
        return cursor.fetchall()  

    
