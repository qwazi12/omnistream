#!/usr/bin/env python3
"""
Instagram Batch Downloader using Instaloader + yt-dlp
Approach: Use instaloader to get post URLs, then yt-dlp to download individual posts
"""

import sys
import os
import time
import random
from typing import List

# Try importing instaloader
try:
    import instaloader
    INSTALOADER_AVAILABLE = True
except ImportError:
    INSTALOADER_AVAILABLE = False
    print("ERROR: instaloader not installed. Run: pip3 install instaloader")
    sys.exit(1)

from simple_drive import SimpleDriveAPI
from simple_downloader import SimplifiedDownloader

def extract_instagram_posts(username: str, max_posts: int = 50) -> List[str]:
    """
    Extract post URLs from Instagram profile using Instaloader
    
    Args:
        username: Instagram username (without @)
        max_posts: Maximum number of posts to extract
        
    Returns:
        List of Instagram post URLs
    """
    print(f"[*] Extracting posts from @{username} using Instaloader...")
    
    # Initialize Instaloader
    L = instaloader.Instaloader()
    
    # Try to load session from cookies.txt if it exists
    # Instaloader can use session files, but for now we'll proceed without login for public profiles
    # For private profiles, user would need to login via instaloader CLI first
    
    urls = []
    
    try:
        # Load profile
        profile = instaloader.Profile.from_username(L.context, username)
        
        print(f"   Profile: {profile.full_name}")
        print(f"   Posts: {profile.mediacount}")
        print(f"   Extracting up to {max_posts} post URLs...")
        
        # Iterate through posts
        count = 0
        for post in profile.get_posts():
            if count >= max_posts:
                break
            
            # Construct post URL
            post_url = f"https://www.instagram.com/p/{post.shortcode}/"
            urls.append(post_url)
            count += 1
            
            # Print progress every 10 posts
            if count % 10 == 0:
                print(f"   Extracted {count} post URLs...")
            
            # Small random delay to avoid rate limiting
            time.sleep(random.uniform(1, 3))
        
        print(f"\u2713 Successfully extracted {len(urls)} post URLs")
        return urls
        
    except instaloader.exceptions.ProfileNotExistsException:
        print(f"\u274c Error: Profile @{username} does not exist")
        return []
    except instaloader.exceptions.PrivateProfileNotFollowedException:
        print(f"\u274c Error: Profile @{username} is private")
        print("   You need to login with: instaloader --login YOUR_USERNAME")
        return []
    except instaloader.exceptions.ConnectionException as e:
        print(f"\u274c Error: Connection failed - {e}")
        print("   Instagram may be rate-limiting. Try again later.")
        return []
    except Exception as e:
        print(f"\u274c Error extracting posts: {e}")
        return []

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Download Instagram videos in batch')
    parser.add_argument('--username', type=str, help='Instagram username (without @)')
    parser.add_argument('--url', type=str, help='Instagram profile URL')
    parser.add_argument('--max', type=int, default=50, help='Maximum number of videos to download')
    parser.add_argument('--test', action='store_true', help='Test mode: download only 1 video')
    
    args = parser.parse_args()
    
    # Extract username from URL if provided
    username = args.username
    if args.url and not username:
        # Extract username from URL
        parts = args.url.rstrip('/').split('/')
        for part in parts:
            if part and not part.startswith('?') and part not in ['http:', 'https:', 'www.instagram.com', 'instagram.com']:
                username = part.split('?')[0]
                break
    
    # Default to beyondstartup.s if nothing provided
    if not username:
        username = "beyondstartup.s"
    
    # Remove @ if present
    username = username.lstrip('@')
    
    # Test mode: download just 1 post
    max_posts = 1 if args.test else args.max
    
    print("="*70)
    print("🎬 OmniStream Instagram Batch Downloader (Instaloader Edition)")
    print("="*70)
    print(f"📍 Target: @{username}")
    print(f"🎯 Max Posts: {max_posts}")
    if args.test:
        print("🧪 TEST MODE: Downloading 1 post to verify setup")
    print("="*70)
    
    # Step 1: Extract post URLs using Instaloader
    post_urls = extract_instagram_posts(username, max_posts)
    
    if not post_urls:
        print("\n\u274c No posts found or extraction failed")
        return 1
    
    print(f"\n[*] Found {len(post_urls)} posts to download")
    
    # Step 2: Download each post using yt-dlp (via SimplifiedDownloader)
    print("\n" + "="*70)
    print("[*] Starting downloads...")
    print("="*70)
    
    try:
        drive_api = SimpleDriveAPI()
    except:
        drive_api = None
        print("   Warning: Google Drive API not available, using local storage")
    
    downloader = SimplifiedDownloader(drive_api=drive_api)
    
    successful = 0
    failed = 0
    
    for i, url in enumerate(post_urls, 1):
        print(f"\n[{i}/{len(post_urls)}] {url}")
        
        try:
            success, msg = downloader.download(url)
            if success:
                successful += 1
                print(f"   \u2713 {msg}")
            else:
                failed += 1
                print(f"   \u2717 {msg}")
        except Exception as e:
            failed += 1
            print(f"   \u2717 Error: {e}")
        
        # Stealth delay between downloads (Instagram high-risk)
        if i < len(post_urls):
            delay = random.uniform(4, 10)
            print(f"   [*] Stealth delay: {delay:.1f}s...")
            time.sleep(delay)
    
    print("\n" + "="*70)
    print(f"[+] Download Complete: {successful} successful, {failed} failed")
    print("="*70)
    
    # Check storage location
    drive_path = "/Volumes/GoogleDrive/My Drive/Travis/Instagram/"
    local_path = os.path.expanduser("~/Downloads/OmniDownloads/Instagram/")
    
    if os.path.exists(drive_path):
        print(f"[*] Files saved to Google Drive: {drive_path}")
    elif os.path.exists(local_path):
        print(f"[*] Files saved locally: {local_path}")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
