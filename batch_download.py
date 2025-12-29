#!/usr/bin/env python3
"""
OmniStream Batch Downloader
Reads video URLs from a text file and downloads them all
"""

import sys
from simple_drive import SimpleDriveAPI
from simple_downloader import SimplifiedDownloader

def main():
    if len(sys.argv) < 2:
        print("Usage: python batch_download.py <url_list_file.txt>")
        print("\nExample url_list.txt format:")
        print("https://youtube.com/shorts/abc123")
        print("https://youtube.com/watch?v=xyz789")
        print("...")
        return 1
    
    url_file = sys.argv[1]
    
    # Read URLs from file
    try:
        with open(url_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        print(f"Error: File '{url_file}' not found")
        return 1
    
    if not urls:
        print("Error: No URLs found in file")
        return 1
    
    print("="*70)
    print("OmniStream - Batch Download")
    print("="*70)
    print(f"Found {len(urls)} URLs to download")
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
    
    # Download each URL
    successful = 0
    failed = 0
    
    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] Processing: {url}")
        print("-" * 70)
        
        success, message = downloader.download(url)
        
        if success:
            successful += 1
            print(f"✓ {message}")
        else:
            failed += 1
            print(f"✗ {message}")
    
    # Summary
    print("\n" + "="*70)
    print("BATCH DOWNLOAD COMPLETE")
    print("="*70)
    print(f"✓ Successful: {successful}/{len(urls)}")
    if failed > 0:
        print(f"✗ Failed: {failed}/{len(urls)}")
    print("="*70)
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
