"""
Fallback engine for generic web scraping using Playwright
"""

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from fake_useragent import UserAgent
import requests
import os
from typing import Tuple, List, Dict, Optional, Callable
from urllib.parse import urlparse, urljoin


class PlaywrightEngine:
    """Fallback engine for generic web scraping"""
    
    def __init__(self, output_path: str, log_callback: Optional[Callable] = None):
        self.output_path = output_path
        self.log_callback = log_callback
        self.ua = UserAgent()
        self.media_files = []
    
    def log(self, message: str, level: str = "INFO"):
        """Send log message to callback"""
        if self.log_callback:
            self.log_callback(message, level)
    
    def download(self, url: str) -> Tuple[bool, str]:
        """
        Universal web scraper using Playwright
        
        Args:
            url: URL to scrape
            
        Returns:
            (success: bool, message: str)
        """
        self.log(f"Starting Playwright scan: {url}")
        self.media_files = []
        
        try:
            with sync_playwright() as p:
                # Launch browser with stealth settings
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox'
                    ]
                )
                
                context = browser.new_context(
                    user_agent=self.ua.random,
                    viewport={'width': 1920, 'height': 1080}
                )
                
                page = context.new_page()
                
                # Intercept network requests to find media
                page.on('response', self._handle_response)
                
                # Navigate to page
                self.log("Loading page...")
                page.goto(url, wait_until='networkidle', timeout=30000)
                
                # Additional DOM scanning for embedded media
                self._scan_dom_for_media(page, url)
                
                browser.close()
                
                # Download found media files
                if self.media_files:
                    self.log(f"Found {len(self.media_files)} media file(s)")
                    success_count = 0
                    
                    for media in self.media_files:
                        if self._download_file(media['url'], media.get('filename')):
                            success_count += 1
                    
                    return True, f"Downloaded {success_count}/{len(self.media_files)} files"
                else:
                    self.log("No downloadable media found", "WARNING")
                    return False, "No media files detected on page"
                    
        except PlaywrightTimeout:
            self.log("Page load timeout", "ERROR")
            return False, "Page failed to load within timeout"
            
        except Exception as e:
            error_msg = str(e)
            self.log(f"✗ Playwright error: {error_msg}", "ERROR")
            return False, f"Playwright failed: {error_msg}"
    
    def _handle_response(self, response):
        """Network response interceptor to find media files"""
        url = response.url
        content_type = response.headers.get('content-type', '').lower()
        
        # Media type detection
        media_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.webm', '.m3u8', 
                          '.pdf', '.zip', '.rar', '.jpg', '.png', '.gif']
        
        media_content_types = ['video/', 'audio/', 'application/pdf', 
                              'application/zip', 'image/']
        
        is_media = (
            any(ext in url.lower() for ext in media_extensions) or
            any(ct in content_type for ct in media_content_types)
        )
        
        if is_media and response.status == 200:
            size = response.headers.get('content-length', 'Unknown')
            filename = self._extract_filename(url, response.headers)
            
            self.media_files.append({
                'url': url,
                'type': self._detect_media_type(url, content_type),
                'size': size,
                'filename': filename
            })
            
            self.log(f"Detected media: {filename} ({size} bytes)")
    
    def _scan_dom_for_media(self, page, base_url: str):
        """Scan DOM for embedded media elements"""
        try:
            # Find video elements
            videos = page.query_selector_all('video source, video')
            for video in videos:
                src = video.get_attribute('src')
                if src:
                    full_url = urljoin(base_url, src)
                    if full_url not in [m['url'] for m in self.media_files]:
                        self.media_files.append({
                            'url': full_url,
                            'type': 'video',
                            'size': 'Unknown',
                            'filename': self._extract_filename(full_url)
                        })
            
            # Find audio elements
            audios = page.query_selector_all('audio source, audio')
            for audio in audios:
                src = audio.get_attribute('src')
                if src:
                    full_url = urljoin(base_url, src)
                    if full_url not in [m['url'] for m in self.media_files]:
                        self.media_files.append({
                            'url': full_url,
                            'type': 'audio',
                            'size': 'Unknown',
                            'filename': self._extract_filename(full_url)
                        })
            
            # Find download links
            links = page.query_selector_all('a[href*=".mp4"], a[href*=".pdf"], a[download]')
            for link in links:
                href = link.get_attribute('href')
                if href:
                    full_url = urljoin(base_url, href)
                    if full_url not in [m['url'] for m in self.media_files]:
                        self.media_files.append({
                            'url': full_url,
                            'type': 'file',
                            'size': 'Unknown',
                            'filename': self._extract_filename(full_url)
                        })
        except:
            pass
    
    def _extract_filename(self, url: str, headers: dict = None) -> str:
        """Extract filename from URL or headers"""
        # Try content-disposition header first
        if headers and 'content-disposition' in headers:
            disp = headers['content-disposition']
            if 'filename=' in disp:
                return disp.split('filename=')[1].strip('"\'')
        
        # Extract from URL
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)
        
        # Remove query parameters
        if '?' in filename:
            filename = filename.split('?')[0]
        
        # Generate fallback name if needed
        if not filename or len(filename) < 3:
            from datetime import datetime
            ext = self._guess_extension(url)
            filename = f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
        
        return filename
    
    def _detect_media_type(self, url: str, content_type: str) -> str:
        """Detect media type from URL and content-type"""
        if 'video' in content_type or any(ext in url for ext in ['.mp4', '.mkv', '.webm']):
            return 'video'
        elif 'audio' in content_type or any(ext in url for ext in ['.mp3', '.wav', '.ogg']):
            return 'audio'
        elif 'pdf' in content_type or '.pdf' in url:
            return 'document'
        elif 'image' in content_type or any(ext in url for ext in ['.jpg', '.png', '.gif']):
            return 'image'
        else:
            return 'file'
    
    def _guess_extension(self, url: str) -> str:
        """Guess file extension from URL"""
        extensions = {
            'mp4': '.mp4', 'mkv': '.mkv', 'webm': '.webm',
            'mp3': '.mp3', 'wav': '.wav',
            'pdf': '.pdf', 'zip': '.zip',
            'jpg': '.jpg', 'png': '.png'
        }
        
        url_lower = url.lower()
        for ext_key, ext_value in extensions.items():
            if ext_key in url_lower:
                return ext_value
        
        return '.bin'
    
    def _download_file(self, url: str, filename: Optional[str] = None) -> bool:
        """Stream download file to destination"""
        try:
            if not filename:
                filename = self._extract_filename(url)
            
            # Sanitize filename
            filename = self._sanitize_filename(filename)
            
            filepath = os.path.join(self.output_path, filename)
            
            self.log(f"Downloading: {filename}")
            
            headers = {'User-Agent': self.ua.random}
            with requests.get(url, stream=True, headers=headers, timeout=30) as r:
                r.raise_for_status()
                
                with open(filepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            
            self.log(f"✓ Saved: {filename}", "SUCCESS")
            
            # Drive API Upload Integration
            # Strict enforcement of Folder ID 1DQDRFQtl7fkgyXoP-sqRENau2WCLJH18
            try:
                from drive_api import GoogleDriveAPI
                drive = GoogleDriveAPI()
                folder_id = '1DQDRFQtl7fkgyXoP-sqRENau2WCLJH18'
                
                self.log(f"📤 Uploading to Drive Folder ID: {folder_id}...", "INFO")
                drive.upload_file(filepath, filename, folder_id)
                self.log("✓ Uploaded to Google Drive", "SUCCESS")
                
                # Cleanup local file after upload
                os.remove(filepath)
                self.log("🧹 Cleaned up local file", "INFO")
                
            except ImportError:
                 self.log("⚠️ Drive API not available for Playwright", "WARNING")
            except Exception as e:
                self.log(f"❌ Drive Upload Failed: {str(e)}", "ERROR")
            
            return True
            
        except Exception as e:
            self.log(f"✗ Failed to download {filename}: {str(e)}", "ERROR")
            return False
    
    def _sanitize_filename(self, filename: str) -> str:
        """Remove invalid characters from filename"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename[:255]  # Max filename length
