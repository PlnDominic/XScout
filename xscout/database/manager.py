import sqlite3
import datetime
import os

class DatabaseManager:
    def __init__(self, db_path="xscout/xscout.db"):
        self.db_path = db_path
        self._initialize_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _initialize_db(self):
        # Create DB file if it doesn't exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Leads Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                username TEXT,
                profile_url TEXT,
                post_text TEXT NOT NULL,
                post_id TEXT UNIQUE NOT NULL,
                matched_keyword TEXT,
                intent_score INTEGER,
                intent_label TEXT,
                contact_info TEXT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notified BOOLEAN DEFAULT 0
            )
        ''')

        # Logs Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                level TEXT,
                message TEXT
            )
        ''')
        
        conn.commit()
        conn.close()

    def add_lead(self, lead_data):
        """
        lead_data: dict containing platform, username, profile_url, post_text, post_id, matched_keyword, intent_score
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO leads (platform, username, profile_url, post_text, post_id, matched_keyword, intent_score, intent_label, contact_info)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                lead_data.get('platform'),
                lead_data.get('username'),
                lead_data.get('profile_url'),
                lead_data.get('post_text'),
                lead_data.get('post_id'),
                lead_data.get('matched_keyword'),
                lead_data.get('intent_score'),
                lead_data.get('intent_label'),
                lead_data.get('contact_info')
            ))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Duplicate entry
            return False
        finally:
            conn.close()

    def lead_exists(self, post_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM leads WHERE post_id = ?', (post_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def mark_notified(self, post_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE leads SET notified = 1 WHERE post_id = ?', (post_id,))
        conn.commit()
        conn.close()
    
    def log(self, level, message):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO logs (level, message) VALUES (?, ?)', (level, message))
        conn.commit()
        conn.close()

# Global instance
db_manager = DatabaseManager()
