import sqlite3
import os
import logging
from datetime import datetime

class Database:
    def __init__(self, db_path="telegram_bot.db"):
        """Initialize database connection."""
        self.db_path = db_path
        self._create_tables()

    def _create_tables(self):
        """Create database tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Channels table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS channels (
            channel_id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            welcome_message TEXT,
            approval_message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Admins table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY,
            added_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Channel admins mapping
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS channel_admins (
            channel_id INTEGER,
            user_id INTEGER,
            PRIMARY KEY (channel_id, user_id),
            FOREIGN KEY (channel_id) REFERENCES channels(channel_id),
            FOREIGN KEY (user_id) REFERENCES admins(user_id)
        )
        ''')
        
        # Join requests tracking
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS join_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id INTEGER,
            user_id INTEGER,
            requested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            approved_at DATETIME,
            FOREIGN KEY (channel_id) REFERENCES channels(channel_id)
        )
        ''')
        
        conn.commit()
        conn.close()

    def add_channel(self, channel_id, title, admin_id):
        """Add a new channel to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Add channel
            cursor.execute(
                "INSERT OR REPLACE INTO channels (channel_id, title) VALUES (?, ?)",
                (channel_id, title)
            )
            
            # Make sure the admin exists
            cursor.execute(
                "INSERT OR IGNORE INTO admins (user_id) VALUES (?)",
                (admin_id,)
            )
            
            # Associate admin with channel
            cursor.execute(
                "INSERT OR IGNORE INTO channel_admins (channel_id, user_id) VALUES (?, ?)",
                (channel_id, admin_id)
            )
            
            conn.commit()
            return True
        except Exception as e:
            logging.error(f"Database error: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def add_admin(self, user_id):
        """Add a new admin to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO admins (user_id) VALUES (?)",
                (user_id,)
            )
            conn.commit()
            return True
        except Exception as e:
            logging.error(f"Database error: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def is_admin(self, user_id):
        """Check if a user is an admin."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT 1 FROM admins WHERE user_id = ?", 
            (user_id,)
        )
        result = cursor.fetchone() is not None
        conn.close()
        
        return result

    def get_admins(self):
        """Get all admins."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT user_id FROM admins")
        result = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return result

    def set_welcome_message(self, channel_id, message):
        """Set a welcome message for a channel."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "UPDATE channels SET welcome_message = ? WHERE channel_id = ?",
                (message, channel_id)
            )
            conn.commit()
            return True
        except Exception as e:
            logging.error(f"Database error: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def set_approval_message(self, channel_id, message):
        """Set an approval message for a channel."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "UPDATE channels SET approval_message = ? WHERE channel_id = ?",
                (message, channel_id)
            )
            conn.commit()
            return True
        except Exception as e:
            logging.error(f"Database error: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_channel(self, channel_id):
        """Get channel info."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM channels WHERE channel_id = ?",
            (channel_id,)
        )
        result = cursor.fetchone()
        conn.close()
        
        return dict(result) if result else None

    def get_admin_channels(self, admin_id):
        """Get all channels administered by a user."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT c.* FROM channels c
            JOIN channel_admins ca ON c.channel_id = ca.channel_id
            WHERE ca.user_id = ?
            """,
            (admin_id,)
        )
        
        result = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return result

    def log_join_request(self, channel_id, user_id):
        """Log a join request."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO join_requests (channel_id, user_id) VALUES (?, ?)",
                (channel_id, user_id)
            )
            conn.commit()
            return True
        except Exception as e:
            logging.error(f"Database error: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def approve_join_request(self, channel_id, user_id):
        """Mark a join request as approved."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "UPDATE join_requests SET approved_at = ? WHERE channel_id = ? AND user_id = ? AND approved_at IS NULL",
                (datetime.now().isoformat(), channel_id, user_id)
            )
            conn.commit()
            return True
        except Exception as e:
            logging.error(f"Database error: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_approval_count(self, channel_id):
        """Get count of approved join requests for a channel."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT COUNT(*) FROM join_requests WHERE channel_id = ? AND approved_at IS NOT NULL",
            (channel_id,)
        )
        
        result = cursor.fetchone()[0]
        conn.close()
        
        return result
