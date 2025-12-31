#!/usr/bin/env python3
"""
Download Instagram Reels - Proven Method
1. Playwright extracts reel URLs from profile
2. yt-dlp downloads each reel individually  
3. Upload to Google Drive
"""

import subprocess
import time
import random
import sys
import os
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright
from drive_api import GoogleDriveAPI


def extract_reel_urls_playwright(username, max_reels=100):
    """Extract reel URLs using Playwright - PROVEN METHOD"""
    print(f"🌐 Extracting {max_reels} reel URLs from @{username}...\n")
    
    reel_urls = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")
        page = context.new_page()
        
        try:
            url = f"https://www.instagram.com/{username}/reels/"
            print(f"📱 Opening {url}")
            page.goto(url, wait_until="networkidle")
            
            print("\n⏸️  Waiting for page to load reels...")
            time.sleep(5)
            
            print(f"🔄 Scrolling to load {max_reels} reels...")
            # Instagram loads slowly - need more wait time between scrolls
            scroll_count = 60
            for i in range(scroll_count):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(3)  # Longer wait for Instagram to load
                
                # Count reels found so far
                current_links = page.query_selector_all('a[href*="/reel/"]')
                unique_count = len(set([l.get_attribute("href") for l in current_links if l.get_attribute("href")]))
                print(f"   Scroll {i+1}/{scroll_count}: Found {unique_count} unique reels", end="\r")
                
                if unique_count >= max_reels + 10:  # Extra buffer
                    print(f"\n✅ Loaded enough reels ({unique_count})")
                    break
            
            print(f"\n\n📹 Extracting reel links...")
            links = page.query_selector_all('a[href*="/reel/"]')
            
            for link in links:
                href = link.get_attribute("href")
                if href and "/reel/" in href:
                    url = f"https://www.instagram.com{href}" if href.startswith("/") else href
                    clean_url = url.split("?")[0]
                    if clean_url not in reel_urls:
                        reel_urls.append(clean_url)
                        if len(reel_urls) <= 5:
                            print(f"   ✓ {clean_url}")
                        
                if len(reel_urls) >= max_reels:
                    break
            
            if len(reel_urls) > 5:
                print(f"   ... and {len(reel_urls) - 5} more")
                    
        finally:
            browser.close()
    
    return reel_urls[:max_reels]


def main():
    username = "entrepreneurbeingentrepreneur"
    drive_folder_id = "1A7Gk8FvdQD9waeo8fgrL_OiNRcIQHYR0"
    max_reels = 100
    
    temp_dir = Path.home() / "Downloads/instagram_temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print(f"🚀 Instagram Reels Downloader (Playwright + yt-dlp)")
    print(f"📺 @{username}")
    print(f"🎯 Target: {max_reels} reels")
    print("=" * 70 + "\n")
    
    # Extract URLs
    reel_urls = extract_reel_urls_playwright(username, max_reels)
    
    if not reel_urls:
        print("\n❌ No reels found!")
        return 1
    
    print(f"\n✅ Extracted {len(reel_urls)} reel URLs\n")
    print("=" * 70)
    
    # Setup Drive - upload directly to the folder user specified, NO subfolders
    drive = GoogleDriveAPI()
    target_folder_id = drive_folder_id  # Use their folder directly
    
    # Get existing files in Drive to avoid duplicates
    print("🔍 Checking for existing files in Drive...")
    try:
        existing_files = drive.service.files().list(
            q=f"'{target_folder_id}' in parents and trashed=false",
            fields="files(name)"
        ).execute().get('files', [])
        existing_names = {f['name'] for f in existing_files}
        print(f"   Found {len(existing_names)} existing files")
    except:
        existing_names = set()
        print("   Could not check existing files, will proceed anyway")
    
    # Download each reel
    successful = 0
    failed = 0
    skipped = 0
    cookies = "Instagramcookies.txt"
    
    for i, url in enumerate(reel_urls, 1):
        # Extract reel ID to check for duplicates
        reel_id = url.split("/reel/")[1].rstrip("/")
        
        # Check if already downloaded
        already_exists = any(reel_id in name for name in existing_names)
        if already_exists:
            print(f"\n[{i}/{len(reel_urls)}] ⏭️  Skipping (already in Drive): {reel_id}")
            skipped += 1
            continue
        
        print(f"\n[{i}/{len(reel_urls)}] ⬇️  {url}")
        
        cmd = [
            "yt-dlp",
            "--cookies", cookies,
            "-o", str(temp_dir / "%(title)s_%(id)s.%(ext)s"),
            "--user-agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "--quiet",
            "--no-warnings",
            url
        ]
        
        try:
            result = subprocess.run(cmd, cwd=os.getcwd(), timeout=60)
            
            if result.returncode == 0:
                # Find and upload
                files = list(temp_dir.glob("*"))
                if files:
                    latest = max(files, key=lambda x: x.stat().st_mtime)
                    print(f"   ⬆️  Uploading {latest.name}")
                    drive.upload_file(str(latest), target_folder_id, latest.name)
                    latest.unlink()
                    successful += 1
                else:
                    failed += 1
            else:
                failed += 1
                
        except Exception as e:
            print(f"   ❌ {e}")
            failed += 1
        
        # Anti-detection delay
        if i < len(reel_urls):
            delay = random.randint(4, 8)
            print(f"   ⏳ {delay}s...")
            time.sleep(delay)
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)
    
    print("\n" + "=" * 70)
    print("📊 COMPLETE")
    print("=" * 70)
    print(f"✅ Successful: {successful}")
    print(f"⏭️  Skipped (duplicates): {skipped}")
    print(f"❌ Failed: {failed}")
    print(f"🔗 https://drive.google.com/drive/folders/{target_folder_id}")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
