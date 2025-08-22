"""
Database operations for X to Discord posting pipeline.
Provides simple CRUD operations for x_posts and process_states tables.
"""

import sqlite3
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from .config import Config

logger = logging.getLogger(__name__)

class DatabaseOperations:
    """Handles all database operations for the pipeline."""
    
    def __init__(self, config: Config):
        """Initialize database connection."""
        self.db_path = config.database_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database and create tables if they don't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create x_posts table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS x_posts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tweet_id TEXT UNIQUE,
                        content TEXT,
                        username TEXT,
                        post_link TEXT,
                        status TEXT,
                        processed_at DATETIME,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create process_states table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS process_states (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        last_processed_account TEXT
                    )
                """)
                
                # Insert default process state if empty
                cursor.execute("SELECT COUNT(*) FROM process_states")
                if cursor.fetchone()[0] == 0:
                    cursor.execute("INSERT INTO process_states (last_processed_account) VALUES (?)", ("",))
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def save_post(self, post_data: Dict[str, Any]) -> int:
        """Save a new post to the database. Returns the post ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO x_posts (tweet_id, content, username, post_link, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    post_data['tweet_id'],
                    post_data['content'],
                    post_data['username'],
                    post_data['post_link'],
                    post_data['status']
                ))
                
                post_id = cursor.lastrowid
                conn.commit()
                logger.info(f"Saved post {post_data['tweet_id']} with ID {post_id}")
                return post_id
                
        except sqlite3.IntegrityError:
            logger.warning(f"Post {post_data['tweet_id']} already exists")
            return self.get_post_by_tweet_id(post_data['tweet_id'])['id']
        except Exception as e:
            logger.error(f"Failed to save post: {e}")
            raise
    
    def get_post_by_id(self, post_id: int) -> Optional[Dict[str, Any]]:
        """Get a post by its ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM x_posts WHERE id = ?", (post_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_dict(cursor, row)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get post by ID {post_id}: {e}")
            raise
    
    def get_post_by_tweet_id(self, tweet_id: str) -> Optional[Dict[str, Any]]:
        """Get a post by its tweet ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM x_posts WHERE tweet_id = ?", (tweet_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_dict(cursor, row)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get post by tweet ID {tweet_id}: {e}")
            raise
    
    def get_posts_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get all posts with a specific status."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM x_posts WHERE status = ? ORDER BY created_at DESC", (status,))
                rows = cursor.fetchall()
                
                return [self._row_to_dict(cursor, row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get posts by status {status}: {e}")
            raise
    
    def update_post_status(self, post_id: int, status: str):
        """Update the status of a post."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if status == 'processed':
                    cursor.execute("""
                        UPDATE x_posts 
                        SET status = ?, processed_at = CURRENT_TIMESTAMP 
                        WHERE id = ?
                    """, (status, post_id))
                else:
                    cursor.execute("""
                        UPDATE x_posts 
                        SET status = ? 
                        WHERE id = ?
                    """, (status, post_id))
                
                conn.commit()
                logger.info(f"Updated post {post_id} status to {status}")
                
        except Exception as e:
            logger.error(f"Failed to update post {post_id} status: {e}")
            raise
    
    def delete_post(self, post_id: int):
        """Delete a post by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM x_posts WHERE id = ?", (post_id,))
                conn.commit()
                logger.info(f"Deleted post {post_id}")
                
        except Exception as e:
            logger.error(f"Failed to delete post {post_id}: {e}")
            raise
    
    def get_last_processed_account(self) -> str:
        """Get the last processed account username."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT last_processed_account FROM process_states WHERE id = 1")
                row = cursor.fetchone()
                
                return row[0] if row else ""
                
        except Exception as e:
            logger.error(f"Failed to get last processed account: {e}")
            raise
    
    def update_last_processed_account(self, username: str):
        """Update the last processed account username."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE process_states SET last_processed_account = ? WHERE id = 1", (username,))
                conn.commit()
                logger.info(f"Updated last processed account to {username}")
                
        except Exception as e:
            logger.error(f"Failed to update last processed account: {e}")
            raise
    
    def get_all_posts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all posts with optional limit."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM x_posts ORDER BY created_at DESC LIMIT ?", (limit,))
                rows = cursor.fetchall()
                
                return [self._row_to_dict(cursor, row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get all posts: {e}")
            raise
    
    def _row_to_dict(self, cursor: sqlite3.Cursor, row: tuple) -> Dict[str, Any]:
        """Convert a database row to a dictionary."""
        columns = [description[0] for description in cursor.description]
        return dict(zip(columns, row))



