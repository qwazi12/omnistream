#!/usr/bin/env python3
"""
Post Manager
Main orchestrator for processing videos from Google Sheets and posting to social media
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

from sheets_manager import SheetsManager
from metadata_generator import MetadataGenerator
from youtube_poster import YouTubePoster
from facebook_poster import FacebookPoster
from drive_api import GoogleDriveAPI


class PostManager:
    """Orchestrate video posting workflow"""
    
    def __init__(self):
        """Initialize all components"""
        self.sheets = SheetsManager()
        self.metadata_gen = MetadataGenerator()
        self.youtube = YouTubePoster()
        self.facebook = FacebookPoster()
        self.drive = GoogleDriveAPI()
        
        self.temp_dir = Path.home() / "Downloads/posting_temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def process_video(self, video_info: dict) -> bool:
        """
        Process a single video from Sheet
        
        Args:
            video_info: Video metadata from Sheet
            
        Returns:
            True if successful
        """
        row_num = video_info['row_num']
        video_name = video_info['video_name']
        
        print(f"\n{'='*70}")
        print(f"📹 Processing: {video_name}")
        print(f"{'='*70}")
        
        # Update status to Processing
        self.sheets.update_status(row_num, SheetsManager.STATUS_PROCESSING)
        
        try:
            # Step 1: Download from Drive
            print("\n1️⃣  Downloading from Google Drive...")
            drive_link = video_info['drive_link']
            
            # Extract file ID from Drive link
            if 'drive.google.com' in drive_link:
                file_id = self._extract_drive_id(drive_link)
            else:
                file_id = drive_link  # Assume it's just the file ID
            
            local_path = self.temp_dir / video_name
            
            # Download file
            self.drive.download_file(file_id, str(local_path))
            print(f"   ✅ Downloaded to: {local_path}")
            
            # Step 2: Get metadata (from Sheet or generate)
            print("\n2️⃣  Preparing metadata...")
            title = video_info['title']
            description = video_info['description']
            tags = video_info['tags']
            
            # If metadata missing, generate with AI
            if not title or not description:
                print("   🤖 Generating metadata with AI...")
                generated = self.metadata_gen.generate_from_filename(video_name)
                title = title or generated['title']
                description = description or generated['description']
                tags = tags or generated['tags']
                
                # Update Sheet with generated metadata
                # (Would need to add update_metadata method to sheets_manager)
            
            print(f"   Title: {title}")
            print(f"   Tags: {tags}")
            
            # Step 3: Post to platforms
            platforms = video_info['platforms'].lower()
            youtube_url = None
            facebook_url = None
            
            # YouTube posting
            if 'youtube' in platforms:
                print("\n3️⃣  Posting to YouTube...")
                
                monetized = video_info.get('monetized', 'Yes').lower() == 'yes'
                tag_list = [t.strip() for t in tags.split(',')]
                
                video_id = self.youtube.upload_video(
                    filepath=str(local_path),
                    title=title,
                    description=description,
                    tags=tag_list,
                    privacy="public",
                    monetization=monetized
                )
                
                if video_id:
                    youtube_url = f"https://youtube.com/watch?v={video_id}"
                    print(f"   ✅ YouTube: {youtube_url}")
                else:
                    raise Exception("YouTube upload failed")
            
            # Facebook posting
            if 'facebook' in platforms:
                print("\n4️⃣  Posting to Facebook...")
                
                # Create caption with hashtags
                caption = f"{title}\n\n{description}\n\n{tags}"
                
                fb_video_id = self.facebook.upload_video(
                    filepath=str(local_path),
                    caption=caption,
                    title=title
                )
                
                if fb_video_id:
                    facebook_url = f"https://facebook.com/{fb_video_id}"
                    print(f"   ✅ Facebook: {facebook_url}")
                else:
                    raise Exception("Facebook upload failed")
            
            # Step 4: Update Sheet with results
            print("\n5️⃣  Updating status...")
            self.sheets.update_status(
                row_num=row_num,
                status=SheetsManager.STATUS_POSTED,
                youtube_url=youtube_url,
                facebook_url=facebook_url,
                notes=f"Posted successfully at {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            
            # Cleanup
            if local_path.exists():
                local_path.unlink()
            
            print(f"\n✅ Successfully processed: {video_name}")
            return True
            
        except Exception as e:
            print(f"\n❌ Error processing video: {e}")
            
            # Update Sheet with error
            self.sheets.update_status(
                row_num=row_num,
                status=SheetsManager.STATUS_FAILED,
                notes=f"Error: {str(e)}"
            )
            
            # Cleanup
            if local_path.exists():
                local_path.unlink()
            
            return False
    
    def process_all_scheduled(self):
        """Process all videos that are scheduled for now"""
        print("\n🔍 Checking for scheduled videos...")
        
        videos = self.sheets.get_scheduled_videos()
        
        if not videos:
            print("   No videos ready to post")
            return
        
        print(f"   Found {len(videos)} videos to post\n")
        
        successful = 0
        failed = 0
        
        for video in videos:
            if self.process_video(video):
                successful += 1
            else:
                failed += 1
            
            # Delay between videos to avoid rate limits
            if video != videos[-1]:  # Not last video
                print("\n⏳ Waiting 30 seconds before next video...")
                time.sleep(30)
        
        print(f"\n{'='*70}")
        print(f"📊 PROCESSING COMPLETE")
        print(f"{'='*70}")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"{'='*70}")
    
    def _extract_drive_id(self, drive_link: str) -> str:
        """Extract file ID from Google Drive link"""
        # Handle different Drive URL formats
        if '/file/d/' in drive_link:
            return drive_link.split('/file/d/')[1].split('/')[0]
        elif 'id=' in drive_link:
            return drive_link.split('id=')[1].split('&')[0]
        else:
            # Assume it's the ID itself
            return drive_link


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='OmniStream Post Manager')
    parser.add_argument('--run', action='store_true', help='Process all scheduled videos')
    parser.add_argument('--test', action='store_true', help='Test connection to services')
    
    args = parser.parse_args()
    
    manager = PostManager()
    
    if args.test:
        print("\n🔧 Testing connections...")
        
        # Test Sheets
        if manager.sheets.worksheet:
            pending = manager.sheets.get_pending_videos()
            print(f"✅ Google Sheets: {len(pending)} pending videos")
        else:
            print("❌ Google Sheets: Not connected")
        
        # Test YouTube
        if manager.youtube.authenticate():
            info = manager.youtube.get_channel_info()
            if info:
                print(f"✅ YouTube: Connected to {info['title']}")
        else:
            print("❌ YouTube: Authentication failed")
        
        # Test Facebook
        if manager.facebook.test_connection():
            print("✅ Facebook: Connected")
        else:
            print("❌ Facebook: Not configured")
    
    elif args.run:
        manager.process_all_scheduled()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
