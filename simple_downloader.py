#!/usr/bin/env python3
"""
SIMPLIFIED: Vertex-style downloader
- Merged video+audio MP4
- OAuth Drive upload
- Duplicate detection
- Zero local storage
"""

import yt_dlp
import tempfile
import shutil
import os
import time
import random
from typing import Tuple
from fake_useragent import UserAgent
from database import get_history

class SimplifiedDownloader:
    def __init__(self, drive_api=None, log_callback=None):
        self.drive_api = drive_api
        self.log_callback = log_callback
        self.ua = UserAgent()
    
    def log(self, message, level="INFO"):
        """Log message"""
        if self.log_callback:
            self.log_callback(message, level)
        else:
            print(f"[{level}] {message}")
    
    def download(self, url: str, max_downloads: int = None) -> Tuple[bool, str]:
        """
        SIMPLIFIED: Download video - Vertex style
        1. Check if already downloaded (duplicate detection)
        2. Download merged MP4 to temp folder3. Upload to Drive: Travis/YouTube/ChannelName/
        4. Delete temp file
        5. Save to database
        """
        self.log(f"Starting download: {url}")
        
        # STEP 1: Duplicate check & Pre-flight Drive Check
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                video_id = info.get('id')
                title = info.get('title', 'Unknown')
                
                # 1. Local DB Check
                if video_id and get_history().is_downloaded(video_id):
                    self.log(f"⏭️  Skipping: Already downloaded (ID: {video_id})", "WARNING")
                    return True, f"Already in history: {title}"
                
                # 2. Drive-Side Check (Source of Truth)
                if self.drive_api:
                    # Construct metadata for folder resolution
                    channel_info = {
                        'handle': None,
                        'name': info.get('uploader') or info.get('channel'),
                        'id': info.get('channel_id') or info.get('uploader_id')
                    }
                    if info.get('uploader_id', '').startswith('@'):
                        channel_info['handle'] = info.get('uploader_id')
                    elif '/@' in info.get('channel_url', ''):
                        channel_info['handle'] = '@' + info.get('channel_url').split('/@')[-1].split('/')[0]
                        
                    # Target Folder ID check
                    base_id = '1DQDRFQtl7fkgyXoP-sqRENau2WCLJH18'
                    yt_folder_id = self.drive_api.find_or_create_folder(["YouTube"], base_id)
                    
                    if yt_folder_id:
                        potential_names = []
                        if channel_info.get('handle'): potential_names.append(channel_info['handle'])
                        if channel_info.get('name'): potential_names.append(channel_info['name'])
                        if channel_info.get('id'): potential_names.append(channel_info['id'])
                        
                        channel_folder_id = self.drive_api.find_or_create_folder(potential_names, yt_folder_id)
                        
                        if channel_folder_id:
                            # Check if file exists in Drive (checking video_id in name is safest)
                            query = f"name contains '{video_id}' and '{channel_folder_id}' in parents and trashed=false"
                            results = self.drive_api.service.files().list(q=query, fields='files(id, name)').execute()
                            if results.get('files'):
                                existing_file = results['files'][0]['name']
                                self.log(f"☁️  Skipping: Found in Drive ({existing_file})", "WARNING")
                                # Add to local DB to sync state
                                try:
                                    video_info_db = {
                                        'video_id': video_id,
                                        'title': title,
                                        'channel_name': channel_info.get('name', 'Unknown'),
                                        'url': info.get('webpage_url') or url,
                                        'file_path': f"Travis/YouTube/{channel_info.get('name')}/{existing_file}",
                                        'file_size': 0,
                                        'platform': 'YouTube',
                                        'format': 'mp4',
                                        'duration': 0
                                    }
                                    get_history().add_to_history(video_info_db)
                                except: pass
                                
                                return True, f"Already in Drive: {existing_file}"
        except Exception as e:
            # self.log(f"Pre-check failed: {e}", "DEBUG")
            pass
        
        # STEP 2: Create temp directory
        temp_dir = tempfile.mkdtemp(prefix='omnistream_')
        self.log(f"📥 Downloading to temp: {temp_dir}")
        
        # STEP 3: Download with yt-dlp (SIMPLIFIED)
        # Dynamic template: Use description (Tweet text) for X/Twitter
        if 'x.com' in url or 'twitter.com' in url:
             out_tmpl = os.path.join(temp_dir, '%(description).100s_%(id)s.%(ext)s')
        elif 'instagram.com' in url:
             out_tmpl = os.path.join(temp_dir, '%(title).100s_%(id)s.%(ext)s')
        else:
             out_tmpl = os.path.join(temp_dir, '%(title)s_%(id)s.%(ext)s')

        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',  # Merged MP4
            'merge_output_format': 'mp4',
            'outtmpl': out_tmpl,
            'no_warnings': True,
            'ignoreerrors': True,
            'http_headers': {
                'User-Agent': self.ua.random,
            }
        }
        
        # Max downloads for channels/playlists
        if max_downloads and max_downloads > 0:
            ydl_opts['playlistend'] = max_downloads
            self.log(f"📊 Limiting to {max_downloads} videos")
        
        # Add cookies if present
        if os.path.exists('cookies.txt'):
            ydl_opts['cookiefile'] = 'cookies.txt'
            self.log("Using cookies.txt for authentication")
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                if not info:
                    return False, "Failed to extract video information"
                
                title = info.get('title', 'Unknown')
                
                # Extract rich channel metadata for smart folder merging
                channel_info = {
                    'handle': None,
                    'name': info.get('uploader') or info.get('channel'),
                    'id': info.get('channel_id') or info.get('uploader_id')
                }
                
                # Try to find handle (often in uploader_id if it starts with @, or uploader_url)
                if info.get('uploader_id') and info.get('uploader_id').startswith('@'):
                    channel_info['handle'] = info.get('uploader_id')
                elif info.get('channel_url'):
                    # Extract handle from https://www.youtube.com/@Handle
                    if '/@' in info.get('channel_url'):
                         channel_info['handle'] = '@' + info.get('channel_url').split('/@')[-1].split('/')[0]
                
                # Fallback if handle missing but name exists
                if not channel_info['handle'] and channel_info['name']:
                    # Construct a handle-like name but don't fake the @
                    pass 

                self.log(f"Channel Info: {channel_info}")
                self.log(f"Title: {title}")
                
                # Detect platform from URL
                platform = 'YouTube'  # default
                if 'instagram.com' in url:
                    platform = 'Instagram'
                elif 'tiktok.com' in url:
                    platform = 'TikTok'
                elif 'x.com' in url or 'twitter.com' in url:
                    platform = 'Twitter'
                
                self.log(f"Platform: {platform}")
                
                # STEP 4: Upload to Drive (Using Smart Merge)
                if self.drive_api:
                    # Find downloaded file
                    downloaded_file = None
                    for file in os.listdir(temp_dir):
                        if file.endswith('.mp4'):
                            downloaded_file = os.path.join(temp_dir, file)
                            break
                    
                    if not downloaded_file:
                        self.log("Error: No MP4 file found", "ERROR")
                        shutil.rmtree(temp_dir, ignore_errors=True)
                        return False, "No MP4 file found"
                    
                    self.log(f"📤 Uploading to Google Drive...")
                    
                    # Upload to Travis/[Platform]/[Smart Channel Folder]
                    result = self.drive_api.upload_file(
                        file_path=downloaded_file,
                        channel_info=channel_info,
                        base_folder_id='1DQDRFQtl7fkgyXoP-sqRENau2WCLJH18',  # YOUR Travis folder
                        platform=platform  # Pass platform for folder organization
                    )
                    
                    if result:
                        self.log(f"✓ Uploaded to Drive: {result['name']}", "SUCCESS")
                        self.log(f"🔗 View: {result.get('webViewLink', 'N/A')}")
                        
                        # STEP 5: Cleanup temp files
                        shutil.rmtree(temp_dir, ignore_errors=True)
                        self.log("🗑️  Temp files cleaned up")
                        
                        # STEP 6: Save to history database
                        try:
                            video_info_db = {
                                'video_id': info.get('id'),
                                'title': info.get('title'),
                                'channel_name': channel_info.get('name', 'Unknown'),
                                'url': info.get('webpage_url') or url,
                                'file_path': f"Travis/YouTube/{channel_info.get('name')}/{os.path.basename(downloaded_file)}",
                                'file_size': os.path.getsize(downloaded_file) if os.path.exists(downloaded_file) else 0,
                                'platform': 'YouTube',
                                'format': info.get('ext'),
                                'duration': info.get('duration')
                            }
                            get_history().add_to_history(video_info_db)
                        except Exception as e:
                            self.log(f"Warning: Could not add to history: {e}", "WARNING")
                        
                        return True, f"Uploaded to Drive: {title}"
                    else:
                        self.log("✗ Upload failed", "ERROR")
                        shutil.rmtree(temp_dir, ignore_errors=True)
                        return False, "Upload to Drive failed"
                else:
                    # No Drive API - just cleanup
                    self.log(f"✓ Downloaded: {title}", "SUCCESS")
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    return True, f"Downloaded: {title}"
        
        except Exception as e:
            self.log(f"✗ Download error: {e}", "ERROR")
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
            return False, f"Download failed: {e}"
