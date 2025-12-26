"""
Primary engine for video platforms using yt-dlp
Enhanced with Shorts-only filter mode
"""

import yt_dlp
import os
import random
import time
from datetime import datetime
from fake_useragent import UserAgent
from typing import Callable, Tuple, Optional


class YtDlpEngine:
    """Primary engine for video platforms with Shorts filtering"""
    
    def __init__(self, output_path: str, progress_callback: Optional[Callable] = None, log_callback: Optional[Callable] = None, stealth_mode: bool = True):
        self.output_path = output_path
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.stealth_mode = stealth_mode
        self.ua = UserAgent()
        
    def log(self, message: str, level: str = "INFO"):
        """Send log message to callback"""
        if self.log_callback:
            self.log_callback(message, level)
    
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
    
    def download(self, url: str, quality: str = 'best', mode: str = 'video') -> Tuple[bool, str]:
        """
        Download using yt-dlp with optimal settings
        
        Args:
            url: URL to download
            quality: Quality preference (best, 1080p, 720p, audio)
            mode: Download mode (video, audio, shorts_only, bulk)
            
        Returns:
            (success: bool, message: str)
        """
        self.log(f"Starting yt-dlp download: {url}")
        
        # Check for cookies.txt
        cookie_file = 'cookies.txt' if os.path.exists('cookies.txt') else None
        if cookie_file and self.stealth_mode:
            self.log("Using cookies.txt for authentication")
        
        # Base Options
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
            'writeinfojson': True,  # Save metadata
            'writethumbnail': True,  # Save thumbnail
            'http_headers': {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate',
            }
        }
        
        # Cookie injection (Stealth)
        if cookie_file and self.stealth_mode:
            ydl_opts['cookiefile'] = cookie_file
        
        # --- SHORTS MODE LOGIC ---
        if mode == "shorts_only":
            self.log("Mode: Shorts Only (filtering vertical content)")
            # Attach the custom Python filter defined above
            ydl_opts['match_filter'] = self._is_short
            
            # Ensure we get the best quality vertical stream
            ydl_opts['format'] = 'bestvideo[height>width]+bestaudio/best[height>width]/best'

        # --- STANDARD VIDEO MODE ---
        elif mode == "video" or mode == "auto":
            ydl_opts['format'] = self._get_format_string(quality, mode)

        # --- AUDIO ONLY MODE ---
        elif mode == "audio":
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
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                if info:
                    title = info.get('title', 'Unknown')
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
