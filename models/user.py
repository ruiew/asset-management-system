# models/user.py
import sqlite3
from config import Config

def get_db():
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

class User:
    @staticmethod
    def find_by_email(email):
        db = get_db()
        return db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    
    @staticmethod
    def find_by_id(user_id):
        db = get_db()
        return db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    
    @staticmethod
    def count_all():
        db = get_db()
        result = db.execute('SELECT COUNT(*) as count FROM users').fetchone()
        # ========== FIXED: Return 0 if no users ==========
        return result['count'] if result else 0
    
    @staticmethod
    def get_all():
        db = get_db()
        return db.execute('SELECT * FROM users').fetchall()
    
    @staticmethod
    def get_all_staff():
        db = get_db()
        return db.execute('SELECT * FROM users WHERE role = "staff"').fetchall()