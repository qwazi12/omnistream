"""
Utility functions for OmniStream Archiver
"""

import os
import logging
from datetime import datetime
from typing import Tuple


def detect_google_drive() -> Tuple[bool, str]:
    """
    Auto-detect Google Drive for Desktop mount point.
    Check paths in priority order and return first found.
    
    Returns:
        (is_connected: bool, base_path: str)
    """
    import glob
    
    drive_paths = [
        # macOS CloudStorage (new Google Drive for Desktop)
        *glob.glob(os.path.expanduser("~/Library/CloudStorage/GoogleDrive-*/My Drive/")),
        
        # Windows
        "G:/My Drive/",
        "H:/My Drive/",
        "D:/My Drive/",
        
        # macOS (legacy mount points)
        "/Volumes/GoogleDrive/My Drive/",
        "/Volumes/Google Drive/My Drive/",
        
        # Linux
        os.path.expanduser("~/Google Drive/"),
        os.path.expanduser("~/GoogleDrive/"),
    ]
    
    for path in drive_paths:
        if os.path.exists(path) and os.path.isdir(path):
            # Test write permissions
            try:
                test_file = os.path.join(path, ".omnistream_test")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                
                # Success! Create base path
                base_path = os.path.join(path, "OmniStream_Downloads")
                os.makedirs(base_path, exist_ok=True)
                return True, base_path
            except (PermissionError, OSError):
                # No write permission, try next path
                continue
    
    # Fallback to local storage with warning
    fallback = os.path.expanduser("~/Downloads/OmniStream_Local")
    os.makedirs(fallback, exist_ok=True)
    return False, fallback


def setup_logging(log_dir: str = "logs"):
    """Configure application logging"""
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"omnistream_{datetime.now().strftime('%Y%m%d')}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)


def sanitize_filename(filename: str) -> str:
    """Remove invalid characters from filename"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename[:255]  # Max filename length
