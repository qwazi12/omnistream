#!/usr/bin/env python3
"""
OmniStream - Dedicated TikTok Engine
Uses TikTokApi for reliable bulk downloads with anti-detection
"""

import asyncio
import os
import time
import random
from TikTokApi import TikTokApi
from simple_drive import SimpleDriveAPI
from simple_downloader import SimplifiedDownloader


class TikTokEngine:
    """Dedicated TikTok download engine with anti-detection"""
    
    def __init__(self, folder_id=None):
        self.folder_id = folder_id or '1kuOKRQQRL0ws5aOVqwkdUzdnfj5KQGjo'
        try:
            self.drive_api = SimpleDriveAPI()
        except:
            self.drive_api = None
        self.downloader = SimplifiedDownloader(drive_api=self.drive_api, base_folder_id=self.folder_id)
    
    async def get_user_videos(self, username, max_videos=50):
        """
        Extract video URLs from a TikTok user profile
        
        Args:
            username: TikTok username (with or without @)
            max_videos: Maximum number of videos to extract
            
        Returns:
            List of video URLs
        """
        # Remove @ if present
        username = username.lstrip('@')
        
        print(f"🔍 Extracting videos from @{username}...")
        print(f"   Target: {max_videos} videos")
        
        video_urls = []
        
        try:
            async with TikTokApi() as api:
                # Create sessions with anti-detection
                await api.create_sessions(
                    num_sessions=1,
                    sleep_after=3,
                    headless=True,
                    suppress_resource_load_types=["image", "media", "font"]
                )
                
                # Get user object
                user = api.user(username)
                
                # Get user info
                try:
                    user_data = await user.info()
                    print(f"✓ Found user: {user_data.get('nickname', username)}")
                    print(f"   Followers: {user_data.get('followerCount', 'N/A'):,}")
                    print(f"   Videos: {user_data.get('videoCount', 'N/A'):,}")
                except Exception as e:
                    print(f"⚠️ Could not fetch user info: {e}")
                
                # Get videos
                print(f"\n📹 Fetching videos...")
                count = 0
                
                async for video in user.videos(count=max_videos):
                    try:
                        video_id = video.get('id')
                        if video_id:
                            video_url = f"https://www.tiktok.com/@{username}/video/{video_id}"
                            video_urls.append(video_url)
                            count += 1
                            
                            # Show progress
                            if count % 10 == 0:
                                print(f"   Extracted {count} videos...")
                            
                            if count >= max_videos:
                                break
                                
                    except Exception as e:
                        print(f"⚠️ Error processing video: {e}")
                        continue
                
                print(f"✓ Extracted {len(video_urls)} video URLs")
                
        except Exception as e:
            print(f"❌ TikTokApi extraction failed: {e}")
            print(f"   Falling back to yt-dlp extraction...")
            return None
        
        return video_urls
    
    async def download_videos(self, video_urls):
        """
        Download a list of TikTok videos
        
        Args:
            video_urls: List of TikTok video URLs
            
        Returns:
            Tuple of (successful_count, failed_count)
        """
        if not video_urls:
            print("❌ No videos to download")
            return 0, 0
        
        print(f"\n{'='*70}")
        print(f"📥 Starting download of {len(video_urls)} videos")
        print(f"{'='*70}\n")
        
        successful = 0
        failed = 0
        
        for i, url in enumerate(video_urls, 1):
            print(f"\n[{i}/{len(video_urls)}] {url}")
            
            # Anti-detection: Random delay between downloads
            if i > 1:
                delay = random.randint(4, 12)
                print(f"⏳ Anti-detection delay: {delay}s")
                time.sleep(delay)
            
            # Attempt download
            success, msg = self.downloader.download(url)
            
            if success:
                successful += 1
                print(f"✓ Success ({successful}/{i})")
            else:
                # Fallback: Try Browser Engine (Playwright)
                print(f"⚠️ Standard download failed. Trying Browser Fallback...")
                try:
                    # Run generic sync playwright in a separate thread to avoid "Sync API inside async loop" error
                    success_fallback, fallback_msg = await asyncio.to_thread(self._run_browser_fallback, url)
                    
                    if success_fallback:
                        successful += 1
                    else:
                        print(f"   ✗ Browser Fallback Failed: {fallback_msg}")
                        failed += 1
                except Exception as e:
                    print(f"   ✗ Browser Fallback Error: {e}")
                    failed += 1
        
        return successful, failed

    def _run_browser_fallback(self, url):
        """Helper to run synchronous Playwright fallback in a thread"""
        try:
            from playwright_engine import PlaywrightEngine
            import tempfile
            import shutil
            
            # Create a temp dir for the browser engine
            with tempfile.TemporaryDirectory() as temp_dir:
                print(f"   Initializing Browser Engine in {temp_dir}...")
                pw_engine = PlaywrightEngine(output_path=temp_dir)
                pw_success, pw_msg = pw_engine.download(url)
                
                if pw_success:
                    print(f"   ✓ Browser Fallback Successful")
                    
                    # Find the downloaded file
                    downloaded_file = None
                    for f in os.listdir(temp_dir):
                        if f.endswith('.mp4'):
                            downloaded_file = os.path.join(temp_dir, f)
                            break
                    
                    if downloaded_file and self.drive_api:
                        print(f"   📤 Uploading to Drive via Engine...")
                        try:
                            # TODO: SimplifiedDownloader has no _get_or_create_drive_folder.
                            # Upload directly to the configured base folder for now.
                            file_name = os.path.basename(downloaded_file)
                            self.drive_api.upload_file(
                                file_path=downloaded_file,
                                channel_info={'name': url.split('@')[-1].split('/')[0]},
                                base_folder_id=self.folder_id,
                                platform='TikTok',
                            )
                            print(f"   ✓ Uploaded to Drive: {file_name}")
                            return True, "Uploaded to Drive"

                        except Exception as e:
                            print(f"   ❌ Upload failed: {e}")
                            return False, str(e)
                    elif downloaded_file:
                        print(f"   ✓ File saved locally (no Drive API): {downloaded_file}")
                        dest_path = os.path.join(os.getcwd(), os.path.basename(downloaded_file))
                        shutil.copy(downloaded_file, dest_path)
                        return True, "Saved locally"
                    else:
                        print(f"   ❌ Browser download reported success but file not found")
                        return False, "File not found"
                else:
                    return False, pw_msg
        except Exception as e:
            return False, str(e)
        # NOTE: every branch above returns; this line is intentionally absent.
    
    async def download_user(self, username, max_videos=50):
        """
        Complete workflow: Extract and download videos from a user
        
        Args:
            username: TikTok username
            max_videos: Maximum number of videos to download
            
        Returns:
            Tuple of (successful_count, failed_count)
        """
        # Extract video URLs
        video_urls = await self.get_user_videos(username, max_videos)
        
        # Fallback to yt-dlp if TikTokApi fails
        if video_urls is None:
            print("⚡ Using yt-dlp fallback extraction...")
            import yt_dlp
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'playlistend': max_videos,
            }
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    result = ydl.extract_info(f"https://www.tiktok.com/@{username.lstrip('@')}", download=False)
                    if result and 'entries' in result:
                        video_urls = [entry['url'] for entry in result['entries'] if entry.get('url')]
                        print(f"✓ yt-dlp extracted {len(video_urls)} videos")
            except Exception as e:
                print(f"❌ yt-dlp extraction also failed: {e}")
                return 0, 0
        
        if not video_urls:
            print("❌ No videos found")
            return 0, 0
        
        # Download videos
        return await self.download_videos(video_urls)


def main():
    """CLI interface for TikTok engine"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python tiktok_engine.py <username> [max_videos] [folder_id]")
        print("\nExamples:")
        print("  python tiktok_engine.py @bicboiclips")
        print("  python tiktok_engine.py bicboiclips 50")
        print("  python tiktok_engine.py @bicboiclips 50 1-uLwByo0LzAteTyFaTSSOvACcT_liIWJ")
        return 1
    
    username = sys.argv[1]
    max_videos = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    folder_id = sys.argv[3] if len(sys.argv) > 3 else None
    
    print("="*70)
    print("OmniStream - TikTok Engine")
    print("="*70)
    print(f"User: @{username.lstrip('@')}")
    print(f"Max Videos: {max_videos}")
    print(f"Target Folder: {folder_id or 'Default (Movie Clips)'}")
    print("="*70)
    
    # Create engine
    engine = TikTokEngine(folder_id=folder_id)
    
    # Run async download
    successful, failed = asyncio.run(engine.download_user(username, max_videos))
    
    # Summary
    print(f"\n{'='*70}")
    print(f"📊 Download Summary")
    print(f"{'='*70}")
    print(f"✓ Successful: {successful}")
    print(f"✗ Failed: {failed}")
    print(f"📈 Success Rate: {(successful/(successful+failed)*100):.1f}%" if (successful+failed) > 0 else "N/A")
    print(f"{'='*70}")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())
