#!/usr/bin/env python3
"""
OmniStream Smart Batch Downloader (Hybrid Edition)
1. Fast Path: Standard yt-dlp extraction
2. Smart Path: Playwright browser automation (visual extraction)
"""

import sys
import time
import os
import yt_dlp
from typing import List
from simple_drive import SimpleDriveAPI
from simple_downloader import SimplifiedDownloader

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Warning: Playwright not found. Browser fallback disabled.")

def extract_standard(channel_url, max_videos=None):
    """Standard yt-dlp extraction (Fast)"""
    print(f"⚡ Trying Fast Extraction: {channel_url}")
    
    urls_to_try = [
        channel_url.rstrip('/') + '/shorts',  # Priority 1: Force Shorts tab
        channel_url,                          # Priority 2: As provided
    ]
    
    for try_url in urls_to_try:
        try:
            print(f"  Checking: {try_url}")
            opts = {
                'quiet': True,
                'extract_flat': 'in_playlist',
                'playlistend': max_videos,
                'ignoreerrors': True,
                'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None
            }
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(try_url, download=False)
                if info and 'entries' in info:
                    videos = []
                    for entry in info['entries']:
                        if not entry: continue
                        
                        # Skip channel IDs
                        if entry.get('id', '').startswith('UC'): continue
                        
                        url = entry.get('webpage_url') or entry.get('url')
                        if not url and entry.get('id'):
                            url = f"https://youtube.com/watch?v={entry['id']}"
                            
                        if url and url not in videos:
                            videos.append(url)
                            
                    if len(videos) > 0:
                        print(f"  ✓ Fast extraction found {len(videos)} videos")
                        return videos
        except Exception:
            pass
            
    print("  ✗ Fast extraction yielded no results (or anti-bot blocked)")
    return []

def extract_browser(channel_url, max_videos=None):
    """Browser-based extraction using Playwright (Smart)"""
    if not PLAYWRIGHT_AVAILABLE:
        return []
    
    # Handle None (unlimited) by setting a very high limit
    effective_limit = max_videos if max_videos is not None else 9999
        
    print(f"\n🧠 Switch to Browser Engine applied: {channel_url}")
    print("  Launching headless browser... (this takes a few seconds)")
    
    # Extract strict handle for filtering (e.g. 'CinemaTweets1')
    target_handle = None
    if 'x.com/' in channel_url or 'twitter.com/' in channel_url:
        parts = channel_url.rstrip('/').split('/')
        if parts:
            target_handle = parts[-1]
            print(f"  🎯 Strict filtering active: Only tweets from @{target_handle}")
    elif 'tiktok.com/@' in channel_url:
        parts = channel_url.rstrip('/').split('@')
        if len(parts) > 1:
            target_handle = parts[-1].split('/')[0]
            print(f"  🎯 Strict filtering active: Only videos from @{target_handle}")
    elif 'instagram.com/' in channel_url:
        parts = channel_url.rstrip('/').split('/')
        if parts:
            # Get username from URL (handle query params like ?igsh=...)
            username = parts[-1].split('?')[0]
            target_handle = username
            print(f"  🎯 Strict filtering active: Only posts from @{target_handle}")
    
    videos = []
    
    try:
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=True)
            
            # Load cookies if available (Crucial for X/Twitter)
            context = browser.new_context(user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            if os.path.exists('cookies.txt'):
                try:
                    # Simple Netscape parser
                    cookies = []
                    with open('cookies.txt', 'r') as f:
                        for line in f:
                            if line.startswith('#') or not line.strip(): continue
                            fields = line.strip().split('\t')
                            if len(fields) >= 7:
                                cookies.append({
                                    'domain': fields[0],
                                    'path': fields[2],
                                    'secure': fields[3].lower() == 'true',
                                    'expires': int(fields[4]) if fields[4] else 0,
                                    'name': fields[5],
                                    'value': fields[6]
                                })
                    if cookies:
                        context.add_cookies(cookies)
                        print("  🍪 Loaded cookies from cookies.txt")
                except Exception as e:
                    print(f"  Warning: Failed to load cookies: {e}")

            page = context.new_page()
            
            # Go to URL
            print(f"  Navigating to page...")
            page.goto(channel_url, timeout=60000)
            
            # Special wait for X/Twitter
            if 'x.com' in channel_url or 'twitter.com' in channel_url:
                time.sleep(5) # Wait for hydration
            elif 'tiktok.com' in channel_url:
                 time.sleep(5) # Wait for TikTok hydration
            
            # Scroll loop
            last_count = 0
            retries = 0
            
            print(f"  Scanning for videos (Goal: {'All' if max_videos is None else max_videos})...")
            
            # We increase retries/buffer since we might discard many retweets
            while len(videos) < effective_limit and retries < 15:
                # Scroll down
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(3)  # Wait for load
                
                # Extract links
                links = page.evaluate("""() => {
                    const results = [];
                    const anchors = Array.from(document.querySelectorAll('a'));
                    anchors.forEach(a => {
                        const href = a.href;
                        // YouTube Checks
                        if (href && (href.includes('/shorts/') || href.includes('/watch?v='))) {
                            if (!href.includes('&list=') && !href.includes('&index=')) {
                                results.push(href);
                            }
                        }
                        // Twitter/X Checks
                        if (href && (href.includes('/status/'))) {
                             results.push(href);
                        }
                        // TikTok Checks
                        if (href && href.includes('/video/')) {
                             results.push(href);
                        }
                        // Instagram Checks
                        if (href && (href.includes('/p/') || href.includes('/reel/') || href.includes('/tv/'))) {
                             results.push(href);
                        }
                    });
                    return results;
                }""")
                
                # Deduplicate and clean (Preserving Order: Latest -> Oldest)
                # 'links' contains new links found in this scroll. They appear top-down.
                for link in links:
                    base = None
                    # Clean URL query params
                    if '/shorts/' in link:
                         base = link.split('?')[0]
                    elif '/watch?v=' in link:
                         base = link.split('&')[0]
                    elif '/status/' in link:
                         # Normalize X urls
                         parts = link.split('/')
                         if 'status' in parts:
                             idx = parts.index('status')
                             if idx + 1 < len(parts):
                                 user_part = parts[idx-1]
                                 id_part = parts[idx+1].split('?')[0]
                                 
                                 # STRICT FILTERS for X
                                 if target_handle and user_part.lower() != target_handle.lower():
                                     continue
                                     
                                 base = f"https://x.com/{user_part}/status/{id_part}"
                    elif '/video/' in link and 'tiktok.com' in link:
                         # Normalize TikTok urls
                         # user/video/id
                         parts = link.split('/')
                         if 'video' in parts:
                             idx = parts.index('video')
                             if idx + 1 < len(parts):
                                 id_part = parts[idx+1].split('?')[0]
                                 user_part = parts[idx-1]
                                 
                                 # STRICT FILTERS for TikTok
                                 if target_handle and target_handle.lstrip('@').lower() not in user_part.lower():
                                      continue
                                 
                                 base = f"https://www.tiktok.com/{user_part}/video/{id_part}"
                    
                    # Add if new (Order Preserved)
                    if base and base not in videos:
                        videos.append(base)

                print(f"  Found {len(videos)} unique matching videos so far...")
                
                if len(videos) == last_count:
                    retries += 1
                else:
                    retries = 0
                    
                last_count = len(videos)
                
            browser.close()
            
    except Exception as e:
        print(f"  ✗ Browser extraction failed: {e}")
        return []
        
    print(f"  ✓ Browser engine found {len(videos)} videos")
    return videos if max_videos is None else videos[:max_videos]

def main():
    if len(sys.argv) < 2:
        print("Usage: python smart_batch.py <channel_url> [max_videos] [folder_id]")
        return 1
        
    channel_url = sys.argv[1]
    max_videos = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else None  # Default to unlimited
    from config_loader import get_folder_id
    folder_id = sys.argv[3] if len(sys.argv) > 3 else get_folder_id('movie_clips', '1kuOKRQQRL0ws5aOVqwkdUzdnfj5KQGjo')
    
    print("="*70)
    print("OmniStream - Smart Batch (Hybrid)")
    print("="*70)
    
    # STEP 1: Fast Extraction
    video_urls = extract_standard(channel_url, max_videos)
    
    # STEP 2: Smart Auto-Switch
    if not video_urls or len(video_urls) < 1:  # Only switch if 0 found, or user can force?
        # Let's be aggressive: if FAST finds nothing, switch to SMART
        video_urls = extract_browser(channel_url, max_videos)
    
    if not video_urls:
        print("\n❌ All extraction methods failed.")
        return 1
        
    print(f"\n📋 Final List: {len(video_urls)} videos found")
    
    # STEP 3: Download
    print("\n" + "="*70)
    try:
        drive_api = SimpleDriveAPI()
    except:
        drive_api = None
        
    downloader = SimplifiedDownloader(drive_api=drive_api, base_folder_id=folder_id)
    
    successful = 0
    failed = 0
    
    for i, url in enumerate(video_urls, 1):
        print(f"\n[{i}/{len(video_urls)}] {url}")
        success, msg = downloader.download(url)
        if success:
            print(f"  ✓ [Engine: standard yt-dlp] {msg}")
            successful += 1
        else:
            # ── FALLBACK 1: Playwright browser engine ─────────────────────────
            if PLAYWRIGHT_AVAILABLE:
                print(f"  ⚠️ Standard download failed ({msg}). Trying Browser Fallback...")
                try:
                    from playwright_engine import PlaywrightEngine
                    import tempfile
                    with tempfile.TemporaryDirectory() as temp_dir:
                        pw_engine = PlaywrightEngine(output_path=temp_dir)
                        pw_success, pw_msg = pw_engine.download(url)

                        if pw_success:
                            print(f"  ✓ [Engine: playwright] {pw_msg}")
                            successful += 1
                        else:
                            # ── FALLBACK 2 & 3: platform-specific bypasses ─────
                            # Only reached when BOTH standard and Playwright failed.
                            print(f"  ✗ Browser Fallback Failed: {pw_msg}")
                            bypass_success = False

                            if 'tiktok.com' in url:
                                print(f"  ⚠️ Trying Snaptik Bypass (TikTok)...")
                                try:
                                    from download_snaptik import download_snaptik_direct
                                    if download_snaptik_direct(url, drive_api):
                                        print(f"  ✓ [Engine: snaptik] success")
                                        successful += 1
                                        bypass_success = True
                                    else:
                                        print(f"  ✗ Snaptik Bypass Failed")
                                except Exception as e:
                                    print(f"  ✗ Snaptik Error: {e}")

                            elif 'youtube.com' in url or 'youtu.be' in url:
                                print(f"  ⚠️ Trying Web Bypass / 10Downloader (YouTube)...")
                                try:
                                    from download_cobalt import download_cobalt_direct
                                    if download_cobalt_direct(url, drive_api, folder_id):
                                        print(f"  ✓ [Engine: cobalt/10dl] success")
                                        successful += 1
                                        bypass_success = True
                                    else:
                                        print(f"  ✗ Web Bypass Failed")
                                except Exception as e:
                                    print(f"  ✗ Web Bypass Error: {e}")

                            if not bypass_success:
                                failed += 1

                except Exception as e:
                    print(f"  ✗ Browser Fallback Error: {e}")
                    failed += 1
            else:
                print(f"  ✗ Failed (Playwright not available): {msg}")
                failed += 1
            
    print(f"\nCompleted: {successful} success, {failed} failed")
    return 0

if __name__ == "__main__":
    sys.exit(main())
