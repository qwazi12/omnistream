#!/usr/bin/env python3
"""
TikTok Retry Script - Browser-based fallback for failed downloads
Uses Playwright to download videos that yt-dlp couldn't access
"""

import sys
import os
import time
import random
from typing import List, Set
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from simple_drive import SimpleDriveAPI
from database import get_history
from config_loader import get_folder_id
import tempfile
import requests

def get_downloaded_video_ids() -> Set[str]:
    """Get set of already downloaded video IDs from database"""
    try:
        import sqlite3
        conn = sqlite3.connect('omnistream_history.db')
        cursor = conn.cursor()
        
        # Get all TikTok video IDs from history
        cursor.execute("SELECT video_id FROM download_history WHERE url LIKE '%tiktok%'")
        video_ids = {row[0] for row in cursor.fetchall()}
        
        conn.close()
        print(f"✓ Found {len(video_ids)} already downloaded videos in database")
        return video_ids
    except Exception as e:
        print(f"⚠️  Could not check database: {e}")
        return set()

def extract_video_id(url: str) -> str:
    """Extract video ID from TikTok URL"""
    if '/video/' in url:
        parts = url.split('/video/')
        if len(parts) > 1:
            return parts[1].split('?')[0].split('/')[0]
    return None

def download_with_browser(url: str, output_dir: str, drive_api=None) -> tuple:
    """
    Download TikTok video using browser automation
    
    Returns:
        (success: bool, message: str)
    """
    video_id = extract_video_id(url)
    if not video_id:
        return False, "Invalid URL - could not extract video ID"
    
    print(f"🌐 Loading {url} in browser...")
    
    try:
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # Load cookies if available
            if os.path.exists('cookies.txt'):
                try:
                    cookies = []
                    with open('cookies.txt', 'r') as f:
                        for line in f:
                            if line.startswith('#') or not line.strip():
                                continue
                            fields = line.strip().split('\t')
                            if len(fields) >= 7:
                                cookies.append({
                                    'domain': fields[0],
                                    'path': fields[2],
                                    'secure': fields[3].lower() == 'true',
                                    'expires': int(fields[4]) if fields[4] != '0' else -1,
                                    'name': fields[5],
                                    'value': fields[6]
                                })
                    if cookies:
                        context.add_cookies(cookies)
                        print("  🍪 Loaded cookies")
                except Exception as e:
                    print(f"  ⚠️  Cookie load failed: {e}")
            
            page = context.new_page()
            video_urls = []
            
            # Track network requests to find video URL - capture ALL .mp4 URLs
            def handle_response(response):
                nonlocal video_urls
                resp_url = response.url
                # Look for actual CDN video files (NOT blob URLs)
                if '.mp4' in resp_url and not resp_url.startswith('blob:'):
                    # Filter for TikTok CDN URLs
                    if any(x in resp_url for x in ['tiktok', 'muscdn', 'musical.ly']):
                        if 'watermark' not in resp_url.lower():
                            video_urls.append(resp_url)
                            print(f"  📹 Found CDN URL: {resp_url[:80]}...")
            
            page.on('response', handle_response)
            
            # Navigate to page
            print("  📄 Loading page...")
            page.goto(url, timeout=30000, wait_until='domcontentloaded')
            
            # Wait longer for video to load and network requests to complete
            time.sleep(8)
            
            # Scroll to ensure video loads
            try:
                page.evaluate("window.scrollTo(0, 300)")
                time.sleep(2)
            except:
                pass
            
            browser.close()
            
            # Use the first non-blob video URL found
            video_url = None
            if video_urls:
                video_url = video_urls[0]
                print(f"  ✓ Found {len(video_urls)} video URL(s), using first")
            
            if not video_url:
                return False, "Could not find video CDN URL (only blob URLs found)"
            
            # Skip blob URLs
            if video_url.startswith('blob:'):
                return False, "Only blob URL found - cannot download"
            
            # Download video
            print(f"  📥 Downloading video...")
            temp_file = os.path.join(output_dir, f"{video_id}.mp4")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Referer': 'https://www.tiktok.com/'
            }
            
            response = requests.get(video_url, headers=headers, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            file_size = os.path.getsize(temp_file)
            print(f"  ✓ Downloaded {file_size / 1024 / 1024:.2f} MB")
            
            # Upload to Drive
            if drive_api:
                print(f"  📤 Uploading to Google Drive...")
                
                channel_info = {
                    'handle': '@aura_snakes',
                    'name': 'aura_snakes',
                    'id': 'aura_snakes'
                }
                
                result = drive_api.upload_with_channel(
                    file_path=temp_file,
                    channel_info=channel_info,
                    base_folder_id=get_folder_id('tiktok_retry', '1rqUIlbpy_MR7Cm0FYCA5TmhECWIgWlIN'),
                    platform='TikTok'
                )
                
                if result:
                    print(f"  ✓ Uploaded to Drive")
                    
                    # Add to database
                    try:
                        video_info = {
                            'video_id': video_id,
                            'title': f'TikTok_Video_{video_id}',
                            'channel_name': 'aura_snakes',
                            'url': url,
                            'file_path': f'TikTok/@aura_snakes/{video_id}.mp4',
                            'file_size': file_size,
                            'platform': 'TikTok',
                            'format': 'mp4',
                            'duration': 0
                        }
                        get_history().add_to_history(video_info)
                    except Exception as e:
                        print(f"  ⚠️  Could not add to database: {e}")
                    
                    # Cleanup
                    os.remove(temp_file)
                    return True, "Successfully downloaded and uploaded"
                else:
                    os.remove(temp_file)
                    return False, "Upload to Drive failed"
            else:
                return True, f"Downloaded to {temp_file}"
    
    except PlaywrightTimeout:
        return False, "Page load timeout"
    except Exception as e:
        return False, f"Browser error: {str(e)}"

def main():
    if len(sys.argv) < 2:
        print("Usage: python retry_tiktok_failures.py <failed_urls_file> [max_retries]")
        print("\nOr provide URLs directly:")
        print("  python retry_tiktok_failures.py url1 url2 url3 ...")
        return 1
    
    print("=" * 70)
    print("TikTok Retry Script - Browser Fallback")
    print("=" * 70)
    
    # Parse arguments
    if os.path.exists(sys.argv[1]):
        # File provided
        print(f"Reading URLs from: {sys.argv[1]}")
        with open(sys.argv[1], 'r') as f:
            urls = [line.strip() for line in f if line.strip() and line.strip().startswith('http')]
        max_retries = int(sys.argv[2]) if len(sys.argv) > 2 else len(urls)
    else:
        # Direct URLs provided
        urls = sys.argv[1:]
        max_retries = len(urls)
    
    print(f"Found {len(urls)} URLs to retry")
    print(f"Will attempt: {min(max_retries, len(urls))} videos")
    print("=" * 70)
    
    # Get already downloaded IDs
    downloaded_ids = get_downloaded_video_ids()
    
    # Filter out already downloaded
    urls_to_retry = []
    for url in urls[:max_retries]:
        video_id = extract_video_id(url)
        if video_id and video_id not in downloaded_ids:
            urls_to_retry.append(url)
        else:
            print(f"⏭️  Skipping (already downloaded): {video_id}")
    
    print(f"\n📋 {len(urls_to_retry)} videos need retry after duplicate check")
    print("=" * 70)
    
    if not urls_to_retry:
        print("✓ All videos already downloaded!")
        return 0
    
    # Initialize Drive
    try:
        drive_api = SimpleDriveAPI()
    except Exception as e:
        print(f"⚠️  Drive API failed: {e}")
        drive_api = None
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix='tiktok_retry_')
    
    # Retry each video
    successful = 0
    failed = 0
    
    for i, url in enumerate(urls_to_retry, 1):
        print(f"\n[{i}/{len(urls_to_retry)}] {url}")
        
        # Anti-detection delay
        if i > 1:
            delay = random.uniform(5, 15)
            print(f"⏸️  Waiting {delay:.1f}s...")
            time.sleep(delay)
        
        success, msg = download_with_browser(url, temp_dir, drive_api)
        
        if success:
            successful += 1
            print(f"✓ Success")
        else:
            failed += 1
            print(f"✗ Failed: {msg}")
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)
    
    # Summary
    print("\n" + "=" * 70)
    print("RETRY SUMMARY")
    print("=" * 70)
    print(f"Videos attempted: {len(urls_to_retry)}")
    print(f"Successfully downloaded: {successful}")
    print(f"Failed: {failed}")
    print(f"Success rate: {successful/len(urls_to_retry)*100:.1f}%")
    print("=" * 70)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
