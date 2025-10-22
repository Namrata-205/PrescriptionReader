import sqlite3
import json
from datetime import datetime
import bcrypt

class Database:
    def __init__(self, db_name="prescription_reader.db"):
        self.db_name = db_name
        self.init_db()
    
    def get_connection(self):
        return sqlite3.connect(self.db_name)
    
    def init_db(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Prescriptions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prescriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                image_path TEXT,
                raw_text TEXT,
                structured_data TEXT,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password):
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password, hashed):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def create_user(self, username, email, password):
        """Create new user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            hashed_pwd = self.hash_password(password)
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, hashed_pwd)
            )
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return True, user_id
        except sqlite3.IntegrityError:
            conn.close()
            return False, None
    
    def authenticate_user(self, username, password):
        """Authenticate user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()
        
        if result and self.verify_password(password, result[1]):
            return True, result[0]
        return False, None
    
    def get_user_by_username(self, username):
        """Get user by username"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()
        return result
    
    def save_prescription(self, user_id, image_path, raw_text, structured_data):
        """Save prescription data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        structured_json = json.dumps(structured_data)
        cursor.execute(
            "INSERT INTO prescriptions (user_id, image_path, raw_text, structured_data) VALUES (?, ?, ?, ?)",
            (user_id, image_path, raw_text, structured_json)
        )
        conn.commit()
        prescription_id = cursor.lastrowid
        conn.close()
        return prescription_id
    
    def get_user_prescriptions(self, user_id):
        """Get all prescriptions for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, image_path, raw_text, structured_data, upload_date FROM prescriptions WHERE user_id = ? ORDER BY upload_date DESC",
            (user_id,)
        )
        results = cursor.fetchall()
        conn.close()
        
        prescriptions = []
        for row in results:
            prescriptions.append({
                'id': row[0],
                'image_path': row[1],
                'raw_text': row[2],
                'structured_data': json.loads(row[3]),
                'upload_date': row[4]
            })
        return prescriptions
    
    def get_prescription_by_id(self, prescription_id):
        """Get specific prescription"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, user_id, image_path, raw_text, structured_data, upload_date FROM prescriptions WHERE id = ?",
            (prescription_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'user_id': row[1],
                'image_path': row[2],
                'raw_text': row[3],
                'structured_data': json.loads(row[4]),
                'upload_date': row[5]
            }
        return None
