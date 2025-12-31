"""
Primary engine for video platforms using yt-dlp
Enhanced with Shorts-only filter mode
"""

import yt_dlp
import os
import random
import time
import shutil
import tempfile
from datetime import datetime
from fake_useragent import UserAgent
from typing import Callable, Tuple, Optional
from database import get_history


class YtDlpEngine:
    """Primary engine for video platforms with Shorts filtering"""
    
    def __init__(self, output_path: str, progress_callback: Optional[Callable] = None, log_callback: Optional[Callable] = None, stealth_mode: bool = True, use_drive_api: bool = False, drive_folder_id: str = None):
        self.output_path = output_path
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.stealth_mode = stealth_mode
        self.ua = UserAgent()
        self.use_drive_api = use_drive_api
        # Use specific folder ID: https://drive.google.com/drive/folders/1DQDRFQtl7fkgyXoP-sqRENau2WCLJH18
        # STRICT ENFORCEMENT: Always fallback to this specific ID
        self.drive_folder_id = drive_folder_id or '1DQDRFQtl7fkgyXoP-sqRENau2WCLJH18'
        
        # Initialize Drive API if enabled
        self.drive_api = None
        if self.use_drive_api:
            try:
                from drive_api import GoogleDriveAPI
                self.drive_api = GoogleDriveAPI()
                self.log("✓ Google Drive API initialized", "SUCCESS")
                self.log(f"📁 Target folder ID: {self.drive_folder_id}", "INFO")
            except Exception as e:
                self.log(f"⚠️  Drive API initialization failed: {e}", "WARNING")
                self.use_drive_api = False
        
    def log(self, message: str, level: str = "INFO"):
        """Send log message to callback"""
        if self.log_callback:
            self.log_callback(message, level)
            
    def _normalize_shorts_url(self, url: str) -> str:
        """
        Normalize YouTube Shorts channel URLs for yt-dlp compatibility
        
        DISABLED: yt-dlp can now natively handle @channel/shorts URLs
        Just pass through the URL unchanged
        """
        # Let yt-dlp handle the URL natively
        return url
    
    def _is_short(self, info, incomplete):
        """
        Custom Filter: Returns None to DOWNLOAD, or a string to SKIP.
        Logic: Keeps video if URL has '/shorts/' OR if it is Vertical (Height > Width).
        """
        url = info.get('webpage_url', '')
        original_url = info.get('original_url', '')
        width = info.get('width')
        height = info.get('height')

        # 1. Strong Signal: The URL explicitly says "shorts"
        if '/shorts/' in url or '/shorts/' in original_url:
            return None  # Keep it (It's definitely a Short)

        # 2. Shape Signal: It is a Vertical Video (9:16 aspect ratio)
        # This catches Shorts that YouTube might serve with a standard /watch?v= URL
        if width and height:
            if height > width:
                return None  # Keep it (It's vertical, likely a Short/TikTok)

        # 3. Fallback: If neither, it's a standard horizontal video -> Skip it.
        return "Skipping: Content is not a Short (Horizontal/Standard Format)"
    
    def download(self, url: str, quality: str = 'best', mode: str = 'video', max_downloads: int = None, date_after: str = None, date_before: str = None) -> Tuple[bool, str]:
        """
        Download using yt-dlp with optimal settings
        
        Args:
            url: URL to download
            quality: Quality preference (best, 1080p, 720p, audio)
            mode: Download mode (video, audio, shorts_only, bulk)
            max_downloads: Maximum number of videos to download (for playlists/channels)
            
        Returns:
            (success: bool, message: str)
        """
        # Normalize URL BEFORE processing
        url = self._normalize_shorts_url(url)
        
        self.log(f"Starting yt-dlp download: {url}")
        
        # Get video info first to check if already downloaded
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                video_id = info.get('id')
                
                # Check duplicate detection database
                if video_id and get_history().is_downloaded(video_id):
                    self.log(f"⏭️  Skipping: Already downloaded (ID: {video_id})", "WARNING")
                    return True, f"Video already in history: {info.get('title', 'Unknown')}"
        except Exception as e:
            self.log(f"Could not pre-check video info: {e}", "WARNING")
        
        # Check for cookies.txt
        cookie_file = 'cookies.txt' if os.path.exists('cookies.txt') else None
        if cookie_file and self.stealth_mode:
            self.log("Using cookies.txt for authentication")
        
        # Base Options with FFmpeg Integration
        ydl_opts = {
            # Output template: Creator/Title_VideoID.ext
            # This ensures: 1) Creator folders, 2) Original title, 3) Unique ID
            'outtmpl': os.path.join(self.output_path, '%(uploader)s/%(title)s_%(id)s.%(ext)s'),
            'ignoreerrors': True,
            'no_warnings': True,
            'quiet': False,
            'progress_hooks': [self._progress_hook],
            'postprocessor_hooks': [self._postprocessor_hook],
            'geo_bypass': True,
            'nocheckcertificate': True,
            'extract_flat': False,
            
            # DISABLED: Don't save extra files
            'writeinfojson': False,  # Don't save .info.json
            'writethumbnail': False,  # Don't save thumbnails
            
            # FFmpeg Integration: Merge video+audio into single MP4
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',  # Force MP4 container
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',  # Convert to MP4 if needed
            }],
            
            'http_headers': {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate',
            }
        }
        
        # Add max downloads limit if specified
        if max_downloads and max_downloads > 0:
            ydl_opts['playlistend'] = max_downloads
            self.log(f"📊 Limiting to {max_downloads} most recent videos")
            
        # Add Date Range Filters
        if date_after:
            ydl_opts['dateafter'] = date_after.replace('-', '') # YYYYMMDD
            self.log(f"📅 Filter: After {date_after}")
        if date_before:
            ydl_opts['datebefore'] = date_before.replace('-', '') # YYYYMMDD
            self.log(f"📅 Filter: Before {date_before}")
        
        # Cookie injection (Stealth)
        if cookie_file and self.stealth_mode:
            ydl_opts['cookiefile'] = cookie_file
        
        # --- SHORTS MODE LOGIC ---
        if mode == "shorts_only":
            self.log("Mode: Shorts Only (filtering vertical content)")
            # DISABLED: If using /shorts tab URL, yt-dlp already filters to Shorts
            # The match_filter was too strict and rejected valid Shorts
            # Rely on the /shorts tab URL to provide only Shorts
            # ydl_opts['match_filter'] = self._is_short
            
            # Ensure we get the best quality vertical stream merged
            # Ensure we get the best quality vertical stream merged
            # Removed [height>width] from format string as it causes syntax errors in some versions
            # The _is_short match_filter logic handles the filtering
            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            
        elif mode == 'audio':
            self.log("🎵 Audio-only mode")
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        
        # Anti-detection delay for bulk operations
        if self._is_bulk_operation(url):
            delay = random.uniform(5, 15)
            self.log(f"Anti-detection delay: {delay:.2f}s")
            time.sleep(delay)
        
        # Execute download
        try:
            # For Drive API mode: download to temp first
            if self.use_drive_api and self.drive_api:
                temp_dir = tempfile.mkdtemp(prefix='omnistream_')
                ydl_opts['outtmpl'] = os.path.join(temp_dir, '%(title)s_%(id)s.%(ext)s')
                self.log(f"📥 Downloading to temp: {temp_dir}")
            else:
                # Direct download to final destination
                self.log(f"📥 Downloading directly to: {self.output_path}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                if info:
                    title = info.get('title', 'Unknown')
                    
                    # Record in download history database
                    try:
                        video_info_db = {
                            'video_id': info.get('id'),
                            'title': info.get('title'),
                            'channel_name': info.get('uploader') or info.get('channel'),
                            'url': info.get('webpage_url') or url,
                            'file_path': info.get('_filename'),
                            'file_size': os.path.getsize(info.get('_filename')) if info.get('_filename') and os.path.exists(info.get('_filename')) else 0,
                            'platform': 'YouTube' if 'youtube' in url else 'Unknown',
                            'format': info.get('ext'),
                            'duration': info.get('duration')
                        }
                        get_history().add_to_history(video_info_db)
                    except Exception as e:
                        self.log(f"Warning: Could not add to history: {e}", "WARNING")
                    
                    # If using Drive API, upload and cleanup
                    if self.use_drive_api and self.drive_api:
                        return self._upload_to_drive(info, temp_dir)
                    else:
                        self.log(f"✓ Successfully downloaded: {title}", "SUCCESS")
                        return True, f"Downloaded: {title}"
                else:
                    return False, "Failed to extract video information"
                    
        except Exception as e:
            error_msg = str(e)
            self.log(f"✗ yt-dlp error: {error_msg}", "ERROR")
            return False, f"Download failed: {error_msg}"
    
    def _get_format_string(self, quality: str, mode: str) -> str:
        """Convert quality preference to yt-dlp format string"""
        if mode == 'audio':
            return 'bestaudio/best'
        
        format_map = {
            'best': 'bestvideo+bestaudio/best',
            '1080p': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
            '720p': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
            '480p': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
            'audio': 'bestaudio/best'
        }
        return format_map.get(quality, format_map['best'])
    
    def _is_bulk_operation(self, url: str) -> bool:
        """Detect if URL is a channel/playlist (bulk operation)"""
        bulk_indicators = ['playlist', 'channel', '/c/', '/@', '/user/']
        return any(indicator in url.lower() for indicator in bulk_indicators)
    
    def _progress_hook(self, d):
        """Progress callback for UI updates"""
        if d['status'] == 'downloading':
            try:
                percentage = d.get('_percent_str', '0%').strip()
                speed = d.get('_speed_str', 'N/A').strip()
                eta = d.get('_eta_str', 'N/A').strip()
                filename = d.get('filename', 'Unknown')
                
                if self.progress_callback:
                    self.progress_callback({
                        'percentage': percentage,
                        'speed': speed,
                        'eta': eta,
                        'filename': os.path.basename(filename)
                    })
            except:
                pass
        
        elif d['status'] == 'finished':
            self.log(f"Download finished, processing file...")
    
    def _postprocessor_hook(self, d):
        """Post-processor callback"""
        if d['status'] == 'finished':
            self.log("Post-processing completed")
    
    def _upload_to_drive(self, info: dict, temp_dir: str) -> Tuple[bool, str]:
        """Upload downloaded file to Google Drive and cleanup"""
        try:
            # Get file info
            title = info.get('title', 'Unknown')
            uploader = info.get('uploader', 'Unknown')
            video_id = info.get('id', '')
            ext = info.get('ext', 'mp4')
            
            # Find downloaded file
            filename = f"{title}_{video_id}.{ext}"
            file_path = os.path.join(temp_dir, filename)
            
            # Find actual file if name doesn't match
            if not os.path.exists(file_path):
                files = [f for f in os.listdir(temp_dir) if f.endswith(f'.{ext}')]
                if files:
                    file_path = os.path.join(temp_dir, files[0])
                    filename = files[0]
            
            if not os.path.exists(file_path):
                self.log(f"✗ Downloaded file not found: {filename}", "ERROR")
                shutil.rmtree(temp_dir, ignore_errors=True)
                return False, "File not found after download"
            
            self.log(f"📤 Uploading to Google Drive...")
            
            # Use the configured folder ID directly (no navigation needed)
            base_folder_id = self.drive_folder_id
            
            # Detect platform from URL
            platform = self._detect_platform(info.get('webpage_url', ''))
            
            # Create platform folder inside base folder
            platform_folder_id = self.drive_api.find_or_create_folder(base_folder_id, platform)
            if not platform_folder_id:
                self.log(f"✗ Failed to create platform folder: {platform}", "ERROR")
                shutil.rmtree(temp_dir, ignore_errors=True)
                return False, "Failed to create platform folder"
            
            # Get creator name with better fallbacks
            creator = info.get('uploader') or info.get('channel') or info.get('uploader_id') or 'Unknown_Creator'
            # Sanitize creator name (remove invalid chars)
            creator = self._sanitize_folder_name(creator)
            
            # Create creator folder
            creator_folder_id = self.drive_api.find_or_create_folder(platform_folder_id, creator)
            if not creator_folder_id:
                self.log(f"✗ Failed to create creator folder: {creator}", "ERROR")
                shutil.rmtree(temp_dir, ignore_errors=True)
                return False, "Failed to create creator folder"
            
            # Upload file
            result = self.drive_api.upload_file(file_path, creator_folder_id, filename)
            
            if result:
                self.log(f"✓ Uploaded to Drive: {result['name']}", "SUCCESS")
                self.log(f"🔗 View: {result.get('webViewLink', 'N/A')}")
                
                # Cleanup temp directory
                shutil.rmtree(temp_dir, ignore_errors=True)
                self.log("🗑️  Temp files cleaned up")
                
                return True, f"Uploaded to Drive: {title}"
            else:
                self.log("✗ Upload failed", "ERROR")
                shutil.rmtree(temp_dir, ignore_errors=True)
                return False, "Upload to Drive failed"
        
        except Exception as e:
            self.log(f"✗ Drive upload error: {str(e)}", "ERROR")
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
            return False, f"Upload error: {str(e)}"
    
    def _detect_platform(self, url: str) -> str:
        """Detect platform from URL"""
        url_lower = url.lower()
        if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'YouTube'
        elif 'tiktok.com' in url_lower:
            return 'TikTok'
        elif 'instagram.com' in url_lower:
            return 'Instagram'
        elif 'twitter.com' in url_lower or 'x.com' in url_lower:
            return 'Twitter'
        else:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc.replace('www.', '')
            return f"Generic_Sites/{domain}"
    
    def _sanitize_folder_name(self, name: str) -> str:
        """Remove invalid characters from folder name"""
        # Remove characters that are invalid in folder names
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        # Remove leading/trailing spaces and dots
        name = name.strip('. ')
        # Limit length
        return name[:100] if name else 'Unknown'
