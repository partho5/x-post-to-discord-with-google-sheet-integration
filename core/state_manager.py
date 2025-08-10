"""
State management for the X-Discord-Google-Sheet Bot using SQLite.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any
from contextlib import contextmanager


class StateManager:
    """Manages persistent state using SQLite database."""
    
    def __init__(self, db_path: Path):
        """
        Initialize state manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize database tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Create accounts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    username TEXT PRIMARY KEY,
                    last_tweet_id TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create errors table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_type TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    username TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create pending posts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pending_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tweet_id TEXT NOT NULL,
                    tweet_text TEXT NOT NULL,
                    username TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    ai_summary TEXT NOT NULL,
                    ai_decision TEXT NOT NULL,
                    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create pipeline state table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            self.logger.info("Database initialized successfully")
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper error handling."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            yield conn
        except sqlite3.Error as e:
            self.logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def get_last_tweet_id(self, username: str) -> Optional[str]:
        """
        Get the last tweet ID for a username.
        
        Args:
            username: Twitter username
            
        Returns:
            Last tweet ID or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT last_tweet_id FROM accounts WHERE username = ?",
                (username,)
            )
            result = cursor.fetchone()
            return result['last_tweet_id'] if result else None
    
    def update_last_tweet_id(self, username: str, tweet_id: str) -> None:
        """
        Update the last tweet ID for a username.
        
        Args:
            username: Twitter username
            tweet_id: Latest tweet ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO accounts (username, last_tweet_id, last_updated)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (username, tweet_id))
            conn.commit()
            self.logger.debug(f"Updated last tweet ID for {username}: {tweet_id}")
    
    def get_all_accounts(self) -> List[Dict]:
        """
        Get all tracked accounts with their last tweet IDs.
        
        Returns:
            List of account dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT username, last_tweet_id, last_updated
                FROM accounts
                ORDER BY username
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def log_error(self, error_type: str, error_message: str, username: Optional[str] = None) -> None:
        """
        Log an error to the database.
        
        Args:
            error_type: Type of error (e.g., 'api_error', 'processing_error')
            error_message: Error message
            username: Optional username associated with the error
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO errors (error_type, error_message, username)
                VALUES (?, ?, ?)
            """, (error_type, error_message, username))
            conn.commit()
            self.logger.error(f"Logged error: {error_type} - {error_message}")
    
    def log_message(self, level: str, message: str) -> None:
        """
        Log a message to the database.
        
        Args:
            level: Log level (INFO, WARNING, ERROR, etc.)
            message: Log message
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO logs (level, message)
                VALUES (?, ?)
            """, (level, message))
            conn.commit()
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict]:
        """
        Get recent errors from the database.
        
        Args:
            limit: Maximum number of errors to return
            
        Returns:
            List of error dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT error_type, error_message, username, timestamp
                FROM errors
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def cleanup_old_logs(self, days: int = 30) -> None:
        """
        Clean up old log entries.
        
        Args:
            days: Number of days to keep logs
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM logs
                WHERE timestamp < datetime('now', '-{} days')
            """.format(days))
            cursor.execute("""
                DELETE FROM errors
                WHERE timestamp < datetime('now', '-{} days')
            """.format(days))
            conn.commit()
            self.logger.info(f"Cleaned up logs older than {days} days")
    
    def save_pending_post(self, tweet_data: Dict[str, Any], analysis_result: Dict[str, Any]) -> bool:
        """
        Save a processed tweet for later posting.
        
        Args:
            tweet_data: Tweet information dictionary
            analysis_result: AI analysis result dictionary
            
        Returns:
            True if saved successfully, False if already exists
        """
        tweet_id = tweet_data.get('id', '')
        
        # Check if tweet is already saved
        if self.is_tweet_already_saved(tweet_id):
            self.logger.debug(f"Tweet {tweet_id} already saved, skipping")
            return False
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO pending_posts 
                (tweet_id, tweet_text, username, created_at, ai_summary, ai_decision)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                tweet_id,
                tweet_data.get('text', ''),
                tweet_data.get('username', ''),
                tweet_data.get('created_at', ''),
                analysis_result.get('summary', ''),
                analysis_result.get('decision', '')
            ))
            conn.commit()
            self.logger.info(f"Saved pending post for tweet {tweet_id}")
            return True
    
    def get_pending_posts(self) -> List[Dict[str, Any]]:
        """
        Get all pending posts.
        
        Returns:
            List of pending post dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT tweet_id, tweet_text, username, created_at, ai_summary, ai_decision, created_timestamp
                FROM pending_posts
                ORDER BY created_timestamp ASC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_latest_pending_post(self) -> Optional[Dict[str, Any]]:
        """
        Get the latest pending post by timestamp.
        
        Returns:
            Latest pending post dictionary or None if no posts exist
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT tweet_id, tweet_text, username, created_at, ai_summary, ai_decision, created_timestamp
                FROM pending_posts
                ORDER BY created_timestamp DESC
                LIMIT 1
            """)
            result = cursor.fetchone()
            return dict(result) if result else None
    
    def delete_pending_post(self, tweet_id: str) -> None:
        """
        Delete a pending post after it has been posted.
        
        Args:
            tweet_id: Tweet ID to delete
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM pending_posts WHERE tweet_id = ?", (tweet_id,))
            conn.commit()
            self.logger.debug(f"Deleted pending post for tweet {tweet_id}")
    
    def clear_pending_posts(self) -> None:
        """
        Clear all pending posts (use with caution).
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM pending_posts")
            deleted_count = cursor.rowcount
            conn.commit()
            self.logger.info(f"Cleared {deleted_count} pending posts")
    
    def is_tweet_already_saved(self, tweet_id: str) -> bool:
        """
        Check if a tweet is already saved in pending posts.
        
        Args:
            tweet_id: Tweet ID to check
            
        Returns:
            True if tweet is already saved, False otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM pending_posts WHERE tweet_id = ?", (tweet_id,))
            count = cursor.fetchone()[0]
            return count > 0
    
    def get_last_processed_account_index(self) -> int:
        """
        Get the index of the last processed account.
        
        Returns:
            Index of last processed account (0 if none)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT value FROM pipeline_state WHERE key = 'last_processed_account_index'"
            )
            result = cursor.fetchone()
            return int(result['value']) if result else 0
    
    def set_last_processed_account_index(self, index: int) -> None:
        """
        Set the index of the last processed account.
        
        Args:
            index: Index of the processed account
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO pipeline_state (key, value, updated_timestamp)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, ('last_processed_account_index', str(index)))
            conn.commit()
            self.logger.debug(f"Updated last processed account index to {index}")
    
    def reset_pipeline_state(self) -> None:
        """
        Reset pipeline state (start from beginning).
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM pipeline_state WHERE key = 'last_processed_account_index'")
            conn.commit()
            self.logger.info("Reset pipeline state - will start from first account") 