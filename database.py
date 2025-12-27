#!/usr/bin/env python3
"""
OmniStream Download History Database
Tracks all downloaded videos to prevent duplicates
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class DownloadHistory:
    """SQLite-based download history tracker"""
    
    def __init__(self, db_path: str = "omnistream_history.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Create tables if they don't exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Main download history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS download_history (
                    video_id TEXT PRIMARY KEY,
                    title TEXT,
                    channel_name TEXT,
                    url TEXT,
                    download_date TEXT,
                    file_path TEXT,
                    file_size INTEGER,
                    platform TEXT,
                    format TEXT,
                    duration INTEGER
                )
            ''')
            
            # Statistics table for quick queries
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stats (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_date TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info(f"Database initialized: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def is_downloaded(self, video_id: str) -> bool:
        """
        Check if video has been downloaded before
        
        Args:
            video_id: Unique video identifier (e.g., YouTube video ID)
            
        Returns:
            True if video exists in history, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT video_id FROM download_history WHERE video_id = ?',
                (video_id,)
            )
            
            result = cursor.fetchone()
            conn.close()
            
            return result is not None
            
        except Exception as e:
            logger.error(f"Error checking download history: {e}")
            return False
    
    def add_to_history(self, video_info: Dict) -> bool:
        """
        Add downloaded video to history
        
        Args:
            video_info: Dictionary containing video metadata
                Required keys: video_id, title, url
                Optional: channel_name, file_path, file_size, platform, format, duration
                
        Returns:
            True if successfully added, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO download_history 
                (video_id, title, channel_name, url, download_date, 
                 file_path, file_size, platform, format, duration)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                video_info.get('video_id'),
                video_info.get('title'),
                video_info.get('channel_name'),
                video_info.get('url'),
                datetime.now().isoformat(),
                video_info.get('file_path'),
                video_info.get('file_size', 0),
                video_info.get('platform', 'Unknown'),
                video_info.get('format'),
                video_info.get('duration')
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Added to history: {video_info.get('video_id')} - {video_info.get('title')}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding to history: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """
        Get download statistics
        
        Returns:
            Dictionary with stats: total_downloads, total_size, platforms, etc.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total downloads
            cursor.execute('SELECT COUNT(*) FROM download_history')
            total_downloads = cursor.fetchone()[0]
            
            # Total size
            cursor.execute('SELECT SUM(file_size) FROM download_history')
            total_size = cursor.fetchone()[0] or 0
            
            # By platform
            cursor.execute('''
                SELECT platform, COUNT(*) 
                FROM download_history 
                GROUP BY platform
            ''')
            platforms = dict(cursor.fetchall())
            
            # Recent downloads (last 7 days)
            cursor.execute('''
                SELECT COUNT(*) FROM download_history
                WHERE date(download_date) >= date('now', '-7 days')
            ''')
            recent_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_downloads': total_downloads,
                'total_size_gb': total_size / (1024**3),
                'platforms': platforms,
                'recent_7days': recent_count
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {
                'total_downloads': 0,
                'total_size_gb': 0,
                'platforms': {},
                'recent_7days': 0
            }
    
    def get_recent(self, limit: int = 20) -> List[Tuple]:
        """
        Get recent downloads
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of tuples with download records
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT video_id, title, channel_name, platform, download_date
                FROM download_history
                ORDER BY download_date DESC
                LIMIT ?
            ''', (limit,))
            
            results = cursor.fetchall()
            conn.close()
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting recent downloads: {e}")
            return []
    
    def clear_history(self) -> bool:
        """
        Clear all download history (use with caution)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM download_history')
            conn.commit()
            conn.close()
            
            logger.warning("Download history cleared!")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing history: {e}")
            return False


# Singleton instance
_history_instance = None

def get_history() -> DownloadHistory:
    """Get or create singleton database instance"""
    global _history_instance
    if _history_instance is None:
        _history_instance = DownloadHistory()
    return _history_instance
