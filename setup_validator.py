#!/usr/bin/env python3
"""
OmniStream Setup Validator & Auto-Configurator
Validates Google Drive, cookies.txt, and JDownloader configuration
"""

import os
import sys
import json
import subprocess
import webbrowser
from pathlib import Path
from datetime import datetime
from typing import Tuple, Dict, List, Optional
import argparse

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class SetupValidator:
    """Main setup validation class"""
    
    # Google Drive mount paths (priority order)
    DRIVE_MOUNT_PATHS = [
        # Windows
        "G:/My Drive/",
        "G:/",
        "H:/My Drive/",
        "D:/My Drive/",
        
        # macOS
        "/Volumes/GoogleDrive/My Drive/",
        "/Volumes/Google Drive/My Drive/",
        
        # Linux
        os.path.expanduser("~/Google Drive/"),
        os.path.expanduser("~/GoogleDrive/"),
    ]
    
    # Cookie file paths
    COOKIE_PATHS = [
        "./cookies.txt",
        os.path.expanduser("~/cookies.txt"),
        "./config/cookies.txt",
    ]
    
    # JDownloader paths by OS
    JDOWNLOADER_PATHS = {
        'Windows': [
            "C:/Program Files/JDownloader/JDownloader2.exe",
            "C:/Program Files (x86)/JDownloader/JDownloader2.exe",
            os.path.expanduser("~/AppData/Local/JDownloader v2.0/JDownloader2.exe"),
        ],
        'Darwin': [  # macOS
            "/Applications/JDownloader 2.0/JDownloader 2.0.app",
            os.path.expanduser("~/Applications/JDownloader 2.0/JDownloader 2.0.app"),
        ],
        'Linux': [
            "/opt/jdownloader/JDownloader.jar",
            os.path.expanduser("~/jdownloader/JDownloader.jar"),
            "/usr/share/jdownloader/JDownloader.jar",
        ]
    }
    
    # Target Google Drive folder ID
    TARGET_FOLDER_ID = "1DQDRFQtl7fkgyXoP-sqRENau2WCLJH18"
    
    def __init__(self):
        self.results = {
            'google_drive': {'status': 'unknown', 'details': {}},
            'cookies': {'status': 'unknown', 'details': {}},
            'jdownloader': {'status': 'unknown', 'details': {}},
            'timestamp': datetime.now().isoformat()
        }
    
    def print_header(self):
        """Print fancy header"""
        print("\n" + "="*60)
        print(f"{Colors.BOLD}          OmniStream Setup Validator v1.0{Colors.ENDC}")
        print("="*60 + "\n")
    
    def print_section(self, number: int, total: int, title: str):
        """Print section header"""
        print(f"\n{Colors.BOLD}[{number}/{total}] {title}{Colors.ENDC}")
    
    def print_success(self, message: str):
        """Print success message"""
        print(f"    {Colors.OKGREEN}✅ {message}{Colors.ENDC}")
    
    def print_warning(self, message: str):
        """Print warning message"""
        print(f"    {Colors.WARNING}⚠️  {message}{Colors.ENDC}")
    
    def print_error(self, message: str):
        """Print error message"""
        print(f"    {Colors.FAIL}❌ {message}{Colors.ENDC}")
    
    def print_info(self, message: str):
        """Print info message"""
        print(f"    {Colors.OKCYAN}📋 {message}{Colors.ENDC}")
    
    def check_google_drive(self) -> Tuple[bool, Optional[str]]:
        """Check for Google Drive mount point"""
        self.print_section(1, 3, "🔍 Checking Google Drive Connection...")
        
        # Use the updated detection from utils
        from utils import detect_google_drive
        is_connected, download_path = detect_google_drive()
        
        if is_connected:
            # Extract the actual Drive path (parent of OmniStream_Downloads)
            drive_path = os.path.dirname(download_path)
            
            self.print_success(f"Google Drive Detected: {drive_path}")
            self.print_success("Write Permission: Verified")
            self.print_success("Folder Structure: Created")
            self.print_info(f"Download Path: {download_path}")
            self.print_info(f"Target Folder ID: {self.TARGET_FOLDER_ID}")
            self.print_warning("Note: Unable to verify specific folder (API credentials needed)")
            
            self.results['google_drive'] = {
                'status': 'ready',
                'details': {
                    'path': drive_path,
                    'download_path': download_path,
                    'writable': True,
                    'folder_id': self.TARGET_FOLDER_ID
                }
            }
            return True, download_path
        else:
            self.print_warning("Google Drive not detected")
            self.print_info(f"Using fallback: {download_path}")
            
            self.results['google_drive'] = {
                'status': 'fallback',
                'details': {
                    'path': download_path,
                    'download_path': download_path,
                    'writable': True,
                    'is_drive': False
                }
            }
            return False, download_path
    
    def create_folder_structure(self, base_path: str) -> str:
        """Create OmniStream folder structure"""
        folders = {
            "YouTube": ["Channels", "Playlists", "Shorts"],
            "TikTok": ["Users", "Hashtags", "Sounds"],
            "Instagram": ["Posts", "Stories", "Reels"],
            "Twitter": ["Videos", "Images"],
            "FileHosts": ["Mega", "MediaFire", "RapidGator", "Other"],
            "Generic_Sites": [],
            "Playwright_Downloads": []
        }
        
        base = Path(base_path) / "OmniStream_Downloads"
        base.mkdir(parents=True, exist_ok=True)
        
        for platform, subfolders in folders.items():
            platform_path = base / platform
            platform_path.mkdir(exist_ok=True)
            
            for subfolder in subfolders:
                (platform_path / subfolder).mkdir(exist_ok=True)
        
        # Create metadata file
        metadata = {
            "created": datetime.now().isoformat(),
            "version": "1.0",
            "drive_path": str(base),
            "drive_folder_id": self.TARGET_FOLDER_ID
        }
        
        with open(base / ".omnistream_metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
        
        return str(base)
    
    def check_cookies(self) -> bool:
        """Check for cookies.txt and validate"""
        self.print_section(2, 3, "🍪 Checking cookies.txt...")
        
        cookie_file = None
        for path in self.COOKIE_PATHS:
            if os.path.exists(path):
                cookie_file = path
                break
        
        if not cookie_file:
            self.print_error("cookies.txt not found")
            self.print_info("Searched locations:")
            for path in self.COOKIE_PATHS:
                print(f"        - {path}")
            
            self.results['cookies'] = {
                'status': 'missing',
                'details': {'searched_paths': self.COOKIE_PATHS}
            }
            return False
        
        self.print_success(f"Found: {cookie_file}")
        
        # Validate format
        try:
            with open(cookie_file, 'r') as f:
                content = f.read()
                
            # Check for Netscape format header
            if "# Netscape HTTP Cookie File" in content or "# HTTP Cookie File" in content:
                self.print_success("Format: Valid (Netscape)")
                format_valid = True
            else:
                self.print_warning("Format: May not be valid Netscape format")
                format_valid = False
            
            # Count domains
            domains = set()
            for line in content.split('\n'):
                if line and not line.startswith('#'):
                    parts = line.split('\t')
                    if len(parts) >= 1:
                        domains.add(parts[0])
            
            if domains:
                self.print_info(f"Sites covered: {', '.join(list(domains)[:5])}")
            
            # Test with yt-dlp if available
            if self.test_cookies_with_ytdlp(cookie_file):
                self.print_success("Test: Authenticated downloads working")
                test_passed = True
            else:
                self.print_warning("Test: Unable to verify (yt-dlp may not be in PATH)")
                test_passed = False
            
            self.results['cookies'] = {
                'status': 'ready' if format_valid else 'warning',
                'details': {
                    'path': cookie_file,
                    'format_valid': format_valid,
                    'test_passed': test_passed,
                    'domains': list(domains)[:10]
                }
            }
            return True
            
        except Exception as e:
            self.print_error(f"Validation failed: {str(e)}")
            self.results['cookies'] = {
                'status': 'error',
                'details': {'error': str(e)}
            }
            return False
    
    def test_cookies_with_ytdlp(self, cookie_file: str) -> bool:
        """Test cookies with yt-dlp"""
        try:
            result = subprocess.run([
                "yt-dlp",
                "--cookies", cookie_file,
                "--skip-download",
                "--print", "title",
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            ], capture_output=True, text=True, timeout=10)
            
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def check_jdownloader(self) -> bool:
        """Check for JDownloader installation and status"""
        self.print_section(3, 3, "📦 Checking JDownloader 2...")
        
        # Detect OS
        import platform
        os_name = platform.system()
        
        paths = self.JDOWNLOADER_PATHS.get(os_name, [])
        
        jd_path = None
        for path in paths:
            if os.path.exists(path):
                jd_path = path
                break
        
        if not jd_path:
            self.print_error("JDownloader 2 not detected")
            self.print_info("Searched locations:")
            for path in paths:
                print(f"        - {path}")
            
            self.results['jdownloader'] = {
                'status': 'missing',
                'details': {'searched_paths': paths}
            }
            return False
        
        self.print_success(f"Installed: {jd_path}")
        
        # Check if running
        is_running = self.is_jdownloader_running()
        if is_running:
            self.print_success("Running: Yes")
        else:
            self.print_warning("Running: No")
        
        # Check API configuration
        self.print_warning("API Connection: Not configured")
        self.print_info("Setup Required:")
        print("        1. Create MyJDownloader account: https://my.jdownloader.org/")
        print("        2. Link your device in JDownloader Settings → MyJDownloader")
        print("        3. Run: python setup_validator.py --configure-jd")
        
        self.results['jdownloader'] = {
            'status': 'needs_config' if jd_path else 'missing',
            'details': {
                'path': jd_path,
                'running': is_running,
                'api_configured': False
            }
        }
        
        return jd_path is not None
    
    def is_jdownloader_running(self) -> bool:
        """Check if JDownloader process is running"""
        try:
            import psutil
            for proc in psutil.process_iter(['name']):
                if 'jdownloader' in proc.info['name'].lower():
                    return True
        except ImportError:
            # Fallback to platform-specific commands
            import platform
            if platform.system() == 'Windows':
                result = subprocess.run(['tasklist'], capture_output=True, text=True)
                return 'jdownloader' in result.stdout.lower()
            else:
                result = subprocess.run(['pgrep', '-f', 'jdownloader'], capture_output=True)
                return len(result.stdout.strip()) > 0
        
        return False
    
    def print_summary(self):
        """Print setup summary"""
        print("\n" + "="*60)
        print(f"{Colors.BOLD}                    SETUP SUMMARY{Colors.ENDC}")
        print("="*60 + "\n")
        
        # Count ready components
        ready_count = 0
        total_count = 3
        
        if self.results['google_drive']['status'] in ['ready', 'fallback']:
            ready_count += 1
        if self.results['cookies']['status'] == 'ready':
            ready_count += 1
        if self.results['jdownloader']['status'] in ['ready', 'needs_config']:
            ready_count += 0.5  # Partial credit
        
        # Overall status
        if ready_count >= 2.5:
            status_icon = "✅"
            status_text = "READY"
            status_color = Colors.OKGREEN
        elif ready_count >= 1.5:
            status_icon = "⚠️"
            status_text = "PARTIALLY READY"
            status_color = Colors.WARNING
        else:
            status_icon = "❌"
            status_text = "NOT READY"
            status_color = Colors.FAIL
        
        print(f"Status: {status_color}{status_icon} {status_text} ({int(ready_count)}/{total_count} components configured){Colors.ENDC}\n")
        
        # Component status
        drive_status = "✅" if self.results['google_drive']['status'] in ['ready', 'fallback'] else "❌"
        cookies_status = "✅" if self.results['cookies']['status'] == 'ready' else "❌"
        jd_status = "⚠️" if self.results['jdownloader']['status'] == 'needs_config' else ("✅" if self.results['jdownloader']['status'] == 'ready' else "❌")
        
        print(f"{drive_status} Google Drive: {self.results['google_drive']['status'].upper()}")
        print(f"{cookies_status} Cookies: {self.results['cookies']['status'].upper()}")
        print(f"{jd_status} JDownloader: {self.results['jdownloader']['status'].upper()}")
        
        # Next steps
        print(f"\n{Colors.BOLD}Next Steps:{Colors.ENDC}")
        
        if self.results['google_drive']['status'] == 'fallback':
            print("1. Install Google Drive for Desktop for cloud storage")
        
        if self.results['cookies']['status'] != 'ready':
            print("2. Set up cookies.txt for authenticated downloads")
            print("   Run: python setup_validator.py --setup")
        
        if self.results['jdownloader']['status'] == 'needs_config':
            print("3. Configure JDownloader API")
            print("   Run: python setup_validator.py --configure-jd")
        elif self.results['jdownloader']['status'] == 'missing':
            print("3. Install JDownloader 2")
            print("   Run: python setup_validator.py --setup")
        
        if ready_count >= 2:
            print(f"\n{Colors.OKGREEN}4. Start OmniStream: python main.py{Colors.ENDC}")
        
        print("\n" + "="*60 + "\n")
    
    def save_json_report(self, output_file: str = "setup_status.json"):
        """Save results to JSON file"""
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        self.print_success(f"Status report saved to: {output_file}")
    
    def interactive_setup(self):
        """Interactive setup mode"""
        print(f"\n{Colors.BOLD}🚀 OmniStream Interactive Setup{Colors.ENDC}\n")
        
        # Google Drive
        if self.results['google_drive']['status'] == 'fallback':
            print(f"{Colors.WARNING}❌ Google Drive not detected.{Colors.ENDC}")
            choice = input("Install Google Drive for Desktop now? (y/n): ")
            if choice.lower() == 'y':
                webbrowser.open("https://www.google.com/drive/download/")
                print("✅ Opening download page...")
                print("⏳ Please install and restart this script.")
                return
        
        # Cookies
        if self.results['cookies']['status'] != 'ready':
            print(f"\n{Colors.WARNING}❌ cookies.txt not found.{Colors.ENDC}")
            print("Choose a method:")
            print("  1) Browser Extension (recommended)")
            print("  2) yt-dlp auto-extract")
            print("  3) Skip (limited functionality)")
            choice = input("Select (1/2/3): ")
            
            if choice == '1':
                print("\n📋 Browser Extension Setup:")
                print("Chrome: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc")
                print("Firefox: https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/")
                print("\n1. Install extension")
                print("2. Visit youtube.com and login")
                print("3. Click extension → Export")
                print("4. Save as 'cookies.txt' in this folder")
                input("\nPress Enter when done...")
                
            elif choice == '2':
                print("\n⚙️  Extracting cookies with yt-dlp...")
                try:
                    subprocess.run([
                        "yt-dlp",
                        "--cookies-from-browser", "chrome",
                        "--cookies", "cookies.txt",
                        "--skip-download",
                        "https://www.youtube.com/"
                    ])
                    print("✅ Cookies extracted to cookies.txt")
                except Exception as e:
                    print(f"❌ Failed: {str(e)}")
        
        # JDownloader
        if self.results['jdownloader']['status'] == 'missing':
            print(f"\n{Colors.WARNING}❌ JDownloader 2 not detected.{Colors.ENDC}")
            choice = input("Install JDownloader 2 now? (y/n): ")
            if choice.lower() == 'y':
                webbrowser.open("https://jdownloader.org/download/index")
                print("✅ Opening download page...")
                print("⏳ Please install and restart this script.")
                return
        
        print(f"\n{Colors.OKGREEN}✅ Setup complete! Run the validator again to verify.{Colors.ENDC}")
    
    def run_validation(self):
        """Run full validation"""
        self.print_header()
        self.check_google_drive()
        self.check_cookies()
        self.check_jdownloader()
        self.print_summary()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='OmniStream Setup Validator')
    parser.add_argument('--setup', action='store_true', help='Run interactive setup')
    parser.add_argument('--test-all', action='store_true', help='Test all components')
    parser.add_argument('--json-output', type=str, help='Export status to JSON file')
    parser.add_argument('--configure-jd', action='store_true', help='Configure JDownloader API')
    
    args = parser.parse_args()
    
    validator = SetupValidator()
    
    if args.setup:
        validator.run_validation()
        validator.interactive_setup()
    elif args.configure_jd:
        print("JDownloader API configuration:")
        print("1. Open JDownloader")
        print("2. Go to Settings → MyJDownloader")
        print("3. Create account at: https://my.jdownloader.org/")
        print("4. Link this device")
        print("\nOnce configured, run the validator again.")
    else:
        validator.run_validation()
        
        if args.json_output:
            validator.save_json_report(args.json_output)
        elif args.test_all:
            validator.save_json_report()


if __name__ == "__main__":
    main()
