#!/usr/bin/env python3
"""
OmniStream CLI - Command-line interface for bulk downloads
Uses all OmniStream infrastructure: engines, database, Drive API
"""

import argparse
import sys
from datetime import datetime
from ytdlp_engine import YtDlpEngine
from database import get_history

def log(message, level="INFO"):
    """Simple console logger"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def main():
    parser = argparse.ArgumentParser(
        description="OmniStream CLI - Bulk video downloader",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download channel with date range
  python omnistream_cli.py \\
    --url "https://youtube.com/@ChannelName" \\
    --date-from "2025-09-17" \\
    --date-to "2025-12-22"
  
  # Download with max limit
  python omnistream_cli.py \\
    --url "https://youtube.com/@ChannelName" \\
    --max 40
  
  # Download Shorts only
  python omnistream_cli.py \\
    --url "https://youtube.com/@ChannelName" \\
    --mode shorts
        """
    )
    
    parser.add_argument('--url', required=True, help='YouTube channel/playlist/video URL')
    parser.add_argument('--date-from', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--date-to', help='End date (YYYY-MM-DD)')
    parser.add_argument('--max', type=int, help='Maximum videos to download')
    parser.add_argument('--mode', choices=['video', 'audio', 'shorts_only'], default='video',
                        help='Download mode (default: video)')
    parser.add_argument('--quality', choices=['best', '1080p', '720p', '480p'], default='best',
                        help='Video quality (default: best)')
    parser.add_argument('--folder-id', default='1DQDRFQtl7fkgyXoP-sqRENau2WCLJH18',
                        help='Google Drive folder ID')
    
    args = parser.parse_args()
    
    # Print header
    print("=" * 70)
    print("OmniStream CLI - Bulk Video Downloader")
    print("=" * 70)
    print(f"URL: {args.url}")
    if args.date_from:
        print(f"Date From: {args.date_from}")
    if args.date_to:
        print(f"Date To: {args.date_to}")
    if args.max:
        print(f"Max Downloads: {args.max}")
    print(f"Mode: {args.mode}")
    print(f"Quality: {args.quality}")
    print(f"Drive Folder: {args.folder_id}")
    print("=" * 70)
    
    # Show current download stats
    stats = get_history().get_stats()
    print(f"\n📊 Your Download History: {stats['total_downloads']} videos ({stats['total_size_gb']:.1f}GB)")
    print()
    
    # Initialize download engine
    log("Initializing download engine...")
    
    def progress_callback(data):
        """Progress updates"""
        pass  # Silent for CLI, just let yt-dlp handle it
    
    try:
        engine = YtDlpEngine(
            output_path="/tmp/omnistream_cli",  # Not used with Drive API
            progress_callback=progress_callback,
            log_callback=log,
            use_drive_api=True,
            drive_folder_id=args.folder_id
        )
        
        log("✓ Engine initialized")
        log("Starting download...")
        print()
        
        # Execute download
        success, message = engine.download(
            url=args.url,
            quality=args.quality,
            mode=args.mode,
            max_downloads=args.max,
            date_after=args.date_from,
            date_before=args.date_to
        )
        
        print()
        print("=" * 70)
        if success:
            log(f"✓ {message}", "SUCCESS")
            
            # Show updated stats
            new_stats = get_history().get_stats()
            print()
            log(f"📊 Total Downloaded: {new_stats['total_downloads']} videos ({new_stats['total_size_gb']:.1f}GB)", "INFO")
            
            return 0
        else:
            log(f"✗ {message}", "ERROR")
            return 1
            
    except KeyboardInterrupt:
        print("\n")
        log("Download cancelled by user", "WARNING")
        return 1
    except Exception as e:
        log(f"Unexpected error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        print("=" * 70)

if __name__ == "__main__":
    sys.exit(main())
