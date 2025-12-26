"""
Secondary engine for file hosting services using JDownloader
"""

import subprocess
import time
import json
import os
from typing import Tuple, Optional, Callable


class JDownloaderEngine:
    """Secondary engine for file hosting services"""
    
    def __init__(self, output_path: str, log_callback: Optional[Callable] = None):
        self.output_path = output_path
        self.log_callback = log_callback
        self.jd_connected = False
        self.check_jdownloader()
    
    def log(self, message: str, level: str = "INFO"):
        """Send log message to callback"""
        if self.log_callback:
            self.log_callback(message, level)
    
    def check_jdownloader(self) -> bool:
        """
        Check if JDownloader is installed and running
        
        Returns:
            True if JDownloader is available, False otherwise
        """
        try:
            # Check if JDownloader process is running
            if os.name == 'nt':  # Windows
                result = subprocess.run(
                    ['tasklist', '/FI', 'IMAGENAME eq JDownloader2.exe'],
                    capture_output=True,
                    text=True
                )
                self.jd_connected = 'JDownloader2.exe' in result.stdout
            else:  # macOS/Linux
                result = subprocess.run(
                    ['pgrep', '-f', 'JDownloader'],
                    capture_output=True,
                    text=True
                )
                self.jd_connected = len(result.stdout.strip()) > 0
            
            if self.jd_connected:
                self.log("✓ JDownloader detected and running")
            else:
                self.log("⚠ JDownloader not running - file host downloads may fail", "WARNING")
            
            return self.jd_connected
            
        except Exception as e:
            self.log(f"JDownloader check failed: {str(e)}", "WARNING")
            self.jd_connected = False
            return False
    
    def download(self, url: str) -> Tuple[bool, str]:
        """
        Download using JDownloader via folder monitoring
        
        Args:
            url: URL to download
            
        Returns:
            (success: bool, message: str)
        """
        if not self.jd_connected:
            self.log("JDownloader not available, trying fallback", "WARNING")
            return False, "JDownloader not running"
        
        self.log(f"Starting JDownloader download: {url}")
        
        try:
            # Create a links file for JDownloader to monitor
            links_file = os.path.join(self.output_path, 'jdownloader_links.txt')
            
            with open(links_file, 'w') as f:
                f.write(url + '\n')
            
            self.log("Link file created for JDownloader monitoring")
            
            # JDownloader will automatically detect and download the file
            # Monitor for completion (simplified approach)
            self.log("JDownloader processing link... (check JDownloader GUI for progress)")
            
            return True, "Link sent to JDownloader - check JDownloader app for progress"
            
        except Exception as e:
            error_msg = str(e)
            self.log(f"✗ JDownloader error: {error_msg}", "ERROR")
            return False, f"JDownloader failed: {error_msg}"
    
    def download_via_cli(self, url: str) -> Tuple[bool, str]:
        """
        Alternative: Download using JDownloader CLI if available
        
        This is a fallback method that uses JDownloader's command-line interface
        """
        try:
            # Find JDownloader installation
            jd_paths = [
                'C:/Program Files/JDownloader/JDownloader2.exe',
                'C:/Program Files (x86)/JDownloader/JDownloader2.exe',
                '/Applications/JDownloader.app/Contents/MacOS/JDownloader',
                os.path.expanduser('~/JDownloader/JDownloader2')
            ]
            
            jd_path = None
            for path in jd_paths:
                if os.path.exists(path):
                    jd_path = path
                    break
            
            if not jd_path:
                return False, "JDownloader executable not found"
            
            # Add link to JDownloader via command line
            subprocess.run([
                jd_path,
                '-add',
                url,
                '-dest',
                self.output_path
            ], check=True)
            
            self.log("Link added to JDownloader via CLI")
            return True, "Added to JDownloader queue"
            
        except Exception as e:
            return False, f"CLI method failed: {str(e)}"
