#!/usr/bin/env python3
"""
Instagram Reels Downloader Engine
Proven method: Playwright (URL extraction) + yt-dlp (download) + Drive upload
"""

import subprocess
import time
import random
import os
import shutil
from pathlib import Path
from typing import List, Tuple
from playwright.sync_api import sync_playwright


class InstagramEngine:
    """Instagram downloader using Playwright + yt-dlp method"""
    
    def __init__(self, cookies_file: str = "Instagramcookies.txt"):
        self.cookies_file = cookies_file
        
    def extract_reel_urls(self, username: str, max_reels: int = 100) -> List[str]:
        """
        Extract reel URLs from Instagram profile using Playwright
        
        Args:
            username: Instagram username (without @)
            max_reels: Maximum number of reels to extract
            
        Returns:
            List of reel URLs
        """
        print(f"🌐 Extracting {max_reels} reel URLs from @{username}...\n")
        
        reel_urls = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
            )
            page = context.new_page()
            
            try:
                url = f"https://www.instagram.com/{username}/reels/"
                print(f"📱 Opening {url}")
                page.goto(url, wait_until="networkidle")
                
                print("\n⏸️  Waiting for page to load reels...")
                time.sleep(5)
                
                print(f"🔄 Scrolling to load {max_reels} reels...")
                scroll_count = 60
                
                for i in range(scroll_count):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(3)
                    
                    current_links = page.query_selector_all('a[href*="/reel/"]')
                    unique_count = len(set([
                        l.get_attribute("href") 
                        for l in current_links 
                        if l.get_attribute("href")
                    ]))
                    print(f"   Scroll {i+1}/{scroll_count}: Found {unique_count} unique reels", end="\r")
                    
                    if unique_count >= max_reels + 10:
                        print(f"\n✅ Loaded enough reels ({unique_count})")
                        break
                
                print(f"\n\n📹 Extracting reel links...")
                links = page.query_selector_all('a[href*="/reel/"]')
                
                for link in links:
                    href = link.get_attribute("href")
                    if href and "/reel/" in href:
                        full_url = f"https://www.instagram.com{href}" if href.startswith("/") else href
                        clean_url = full_url.split("?")[0]
                        
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
    
    def download_reel(self, url: str, output_dir: Path) -> Tuple[bool, str]:
        """
        Download a single reel using yt-dlp
        
        Args:
            url: Instagram reel URL
            output_dir: Directory to save the file
            
        Returns:
            (success, filepath or error message)
        """
        cmd = [
            "yt-dlp",
            "--cookies", self.cookies_file,
            "-o", str(output_dir / "%(title)s_%(id)s.%(ext)s"),
            "--user-agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "--quiet",
            "--no-warnings",
            url
        ]
        
        try:
            result = subprocess.run(cmd, cwd=os.getcwd(), timeout=60)
            
            if result.returncode == 0:
                # Find the downloaded file
                files = list(output_dir.glob("*"))
                if files:
                    latest = max(files, key=lambda x: x.stat().st_mtime)
                    return True, str(latest)
            
            return False, "Download failed"
            
        except Exception as e:
            return False, str(e)
    
    def download_reels_to_drive(
        self,
        username: str,
        drive_folder_id: str,
        max_reels: int = 100,
        drive_api=None
    ) -> dict:
        """
        Complete workflow: Extract URLs → Download → Upload to Drive
        
        Args:
            username: Instagram username (without @)
            drive_folder_id: Google Drive folder ID to upload to
            max_reels: Maximum number of reels to download
            drive_api: GoogleDriveAPI instance (optional)
            
        Returns:
            Dict with statistics: {successful, failed, skipped}
        """
        print("=" * 70)
        print(f"🚀 Instagram Reels Downloader")
        print(f"📺 Account: @{username}")
        print(f"🎯 Target: {max_reels} reels")
        print("=" * 70 + "\n")
        
        # Extract URLs
        reel_urls = self.extract_reel_urls(username, max_reels)
        
        if not reel_urls:
            print("\n❌ No reels found!")
            return {"successful": 0, "failed": 0, "skipped": 0}
        
        print(f"\n✅ Extracted {len(reel_urls)} reel URLs\n")
        print("=" * 70)
        
        # Setup temp directory
        temp_dir = Path.home() / "Downloads/instagram_temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup Drive
        if drive_api is None:
            from drive_api import GoogleDriveAPI
            drive_api = GoogleDriveAPI()
        
        target_folder_id = drive_api.find_or_create_folder(drive_folder_id, username)
        
        # Get existing files for duplicate detection
        print("🔍 Checking for existing files in Drive...")
        try:
            existing_files = drive_api.service.files().list(
                q=f"'{target_folder_id}' in parents and trashed=false",
                fields="files(name)"
            ).execute().get('files', [])
            existing_names = {f['name'] for f in existing_files}
            print(f"   Found {len(existing_names)} existing files\n")
        except:
            existing_names = set()
            print("   Could not check existing files\n")
        
        # Download and upload
        successful = 0
        failed = 0
        skipped = 0
        
        for i, url in enumerate(reel_urls, 1):
            reel_id = url.split("/reel/")[1].rstrip("/")
            
            # Check duplicates
            if any(reel_id in name for name in existing_names):
                print(f"\n[{i}/{len(reel_urls)}] ⏭️  Skipping (already in Drive): {reel_id}")
                skipped += 1
                continue
            
            print(f"\n[{i}/{len(reel_urls)}] ⬇️  {url}")
            
            success, result = self.download_reel(url, temp_dir)
            
            if success:
                filepath = result
                filename = Path(filepath).name
                print(f"   ⬆️  Uploading {filename}")
                drive_api.upload_file(filepath, target_folder_id, filename)
                Path(filepath).unlink()
                successful += 1
            else:
                print(f"   ❌ {result}")
                failed += 1
            
            # Anti-detection delay
            if i < len(reel_urls):
                delay = random.randint(4, 8)
                print(f"   ⏳ {delay}s...")
                time.sleep(delay)
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 COMPLETE")
        print("=" * 70)
        print(f"✅ Successful: {successful}")
        print(f"⏭️  Skipped (duplicates): {skipped}")
        print(f"❌ Failed: {failed}")
        print(f"🔗 https://drive.google.com/drive/folders/{target_folder_id}")
        print("=" * 70)
        
        return {
            "successful": successful,
            "failed": failed,
            "skipped": skipped
        }


if __name__ == "__main__":
    import sys
    
    # Simple CLI for testing
    username = sys.argv[1] if len(sys.argv) > 1 else "entrepreneurbeingentrepreneur"
    max_reels = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    engine = InstagramEngine()
    
    # Example: Just extract URLs
    urls = engine.extract_reel_urls(username, max_reels)
    print(f"\n✅ Extracted {len(urls)} URLs")
    for url in urls:
        print(f"  - {url}")
