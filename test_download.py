#!/usr/bin/env python3
"""
SIMPLIFIED OmniStream CLI - Test with single video
"""

import sys
from simple_drive import SimpleDriveAPI
from simple_downloader import SimplifiedDownloader

def main():
    url = sys.argv[1] if len(sys.argv) > 1 else None
    
    if not url:
        print("Usage: python test_download.py <youtube_url>")
        return 1
    
    print("="*70)
    print("OmniStream - Simplified Test")
    print("="*70)
    print(f"URL: {url}")
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
    success, message = downloader.download(url)
    
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
