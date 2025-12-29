#!/usr/bin/env python3
"""
SIMPLIFIED OmniStream CLI - With max downloads support
"""

import sys
from simple_drive import SimpleDriveAPI
from simple_downloader import SimplifiedDownloader

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_bulk.py <youtube_url> [max_videos]")
        return 1
    
    url = sys.argv[1]
    max_downloads = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    print("="*70)
    print("OmniStream - Bulk Download Test")
    print("="*70)
    print(f"URL: {url}")
    if max_downloads:
        print(f"Max Downloads: {max_downloads}")
    print("="*70)
    print()
    
    # Initialize Drive API (OAuth)
    try:
        drive_api = SimpleDriveAPI()
    except Exception as e:
        print(f"Drive API failed: {e}")
        print("Continuing without Drive upload...")
        drive_api = None
    
    # Initialize downloader
    downloader = SimplifiedDownloader(drive_api=drive_api)
    
    # Download
    success, message = downloader.download(url, max_downloads=max_downloads)
    
    print()
    print("="*70)
    if success:
        print(f"✓ {message}")
        return 0
    else:
        print(f"✗ {message}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
