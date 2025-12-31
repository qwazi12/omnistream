#!/usr/bin/env python3
"""
Google Sheets Manager
Manages content calendar in Google Sheets for video posting workflow
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional
import gspread
from oauth2client.service_account import ServiceAccountCredentials


class SheetsManager:
    """Manage content calendar in Google Sheets"""
    
    # Column indices (0-based)
    COL_ID = 0
    COL_VIDEO_NAME = 1
    COL_DRIVE_LINK = 2
    COL_TITLE = 3
    COL_DESCRIPTION = 4
    COL_TAGS = 5
    COL_PLATFORMS = 6
    COL_STATUS = 7
    COL_SCHEDULED_TIME = 8
    COL_YOUTUBE_URL = 9
    COL_FACEBOOK_URL = 10
    COL_MONETIZED = 11
    COL_NOTES = 12
    
    # Status values
    STATUS_IDLE = "Idle"
    STATUS_SCHEDULED = "Scheduled"
    STATUS_PROCESSING = "Processing"
    STATUS_POSTED = "Posted"
    STATUS_FAILED = "Failed"
    
    def __init__(
        self,
        credentials_file: str = 'service_account.json',
        sheet_url: str = None,
        config_file: str = 'sheets_config.json'
    ):
        """
        Initialize Sheets Manager
        
        Args:
            credentials_file: Google service account credentials
            sheet_url: Google Sheet URL (optional, can load from config)
            config_file: Config file to save/load sheet URL
        """
        self.credentials_file = credentials_file
        self.config_file = config_file
        self.sheet = None
        self.worksheet = None
        
        # Load config
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
                sheet_url = sheet_url or config.get('sheet_url')
        
        if sheet_url:
            self.connect(sheet_url)
    
    def connect(self, sheet_url: str) -> bool:
        """
        Connect to Google Sheet
        
        Args:
            sheet_url: Full URL or sheet ID
            
        Returns:
            True if successful
        """
        try:
            # Setup credentials
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            if not os.path.exists(self.credentials_file):
                print(f"❌ Credentials file not found: {self.credentials_file}")
                print("\nTo setup:")
                print("1. Go to Google Cloud Console")
                print("2. Enable Google Sheets API")
                print("3. Create Service Account")
                print("4. Download credentials as service_account.json")
                return False
            
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                self.credentials_file, scope
            )
            client = gspread.authorize(creds)
            
            # Open sheet
            self.sheet = client.open_by_url(sheet_url)
            self.worksheet = self.sheet.sheet1
            
            # Save config
            with open(self.config_file, 'w') as f:
                json.dump({'sheet_url': sheet_url}, f)
            
            print(f"✅ Connected to Sheet: {self.sheet.title}")
            return True
            
        except Exception as e:
            print(f"❌ Error connecting to Sheet: {e}")
            return False
    
    def get_pending_videos(self) -> List[Dict]:
        """
        Get videos with Status = 'Idle' or 'Scheduled'
        
        Returns:
            List of video dictionaries
        """
        if not self.worksheet:
            return []
        
        videos = []
        rows = self.worksheet.get_all_values()[1:]  # Skip header
        
        for i, row in enumerate(rows, start=2):  # Start at row 2 (after header)
            if len(row) <= self.COL_STATUS:
                continue
                
            status = row[self.COL_STATUS]
            
            if status in [self.STATUS_IDLE, self.STATUS_SCHEDULED]:
                video = self._row_to_dict(row, i)
                videos.append(video)
        
        return videos
    
    def get_scheduled_videos(self, now: datetime = None) -> List[Dict]:
        """
        Get videos scheduled for posting (Status = 'Scheduled' and time has arrived)
        
        Args:
            now: Current time (default: now)
            
        Returns:
            List of video dictionaries ready to post
        """
        if not now:
            now = datetime.now()
        
        videos = []
        rows = self.worksheet.get_all_values()[1:]
        
        for i, row in enumerate(rows, start=2):
            if len(row) <= self.COL_SCHEDULED_TIME:
                continue
            
            status = row[self.COL_STATUS]
            scheduled_time_str = row[self.COL_SCHEDULED_TIME]
            
            if status == self.STATUS_SCHEDULED and scheduled_time_str:
                try:
                    scheduled_time = datetime.strptime(
                        scheduled_time_str, 
                        '%Y-%m-%d %H:%M'
                    )
                    
                    if scheduled_time <= now:
                        video = self._row_to_dict(row, i)
                        videos.append(video)
                except ValueError:
                    print(f"⚠️  Invalid date format in row {i}: {scheduled_time_str}")
        
        return videos
    
    def update_status(
        self,
        row_num: int,
        status: str,
        youtube_url: str = None,
        facebook_url: str = None,
        notes: str = None
    ):
        """
        Update video row status and URLs
        
        Args:
            row_num: Row number in sheet
            status: New status
            youtube_url: YouTube video URL (optional)
            facebook_url: Facebook video URL (optional)
            notes: Additional notes (optional)
        """
        if not self.worksheet:
            return
        
        # Update status
        self.worksheet.update_cell(row_num, self.COL_STATUS + 1, status)
        
        # Update URLs if provided
        if youtube_url:
            self.worksheet.update_cell(row_num, self.COL_YOUTUBE_URL + 1, youtube_url)
        
        if facebook_url:
            self.worksheet.update_cell(row_num, self.COL_FACEBOOK_URL + 1, facebook_url)
        
        # Update notes
        if notes:
            self.worksheet.update_cell(row_num, self.COL_NOTES + 1, notes)
        
        print(f"✅ Updated row {row_num}: Status = {status}")
    
    def add_video(self, video_info: Dict) -> int:
        """
        Add new video row to sheet
        
        Args:
            video_info: Dict with video metadata
            
        Returns:
            Row number of added video
        """
        if not self.worksheet:
            return 0
        
        # Get next ID
        rows = self.worksheet.get_all_values()[1:]
        next_id = len(rows) + 1
        
        row_data = [
            next_id,
            video_info.get('video_name', ''),
            video_info.get('drive_link', ''),
            video_info.get('title', ''),
            video_info.get('description', ''),
            video_info.get('tags', ''),
            video_info.get('platforms', 'YouTube'),
            video_info.get('status', self.STATUS_IDLE),
            video_info.get('scheduled_time', ''),
            '',  # YouTube URL
            '',  # Facebook URL
            video_info.get('monetized', 'Yes'),
            ''   # Notes
        ]
        
        self.worksheet.append_row(row_data)
        print(f"✅ Added video to row {next_id + 1}")
        return next_id + 1
    
    def _row_to_dict(self, row: List, row_num: int) -> Dict:
        """Convert sheet row to dictionary"""
        return {
            'row_num': row_num,
            'id': row[self.COL_ID] if len(row) > self.COL_ID else '',
            'video_name': row[self.COL_VIDEO_NAME] if len(row) > self.COL_VIDEO_NAME else '',
            'drive_link': row[self.COL_DRIVE_LINK] if len(row) > self.COL_DRIVE_LINK else '',
            'title': row[self.COL_TITLE] if len(row) > self.COL_TITLE else '',
            'description': row[self.COL_DESCRIPTION] if len(row) > self.COL_DESCRIPTION else '',
            'tags': row[self.COL_TAGS] if len(row) > self.COL_TAGS else '',
            'platforms': row[self.COL_PLATFORMS] if len(row) > self.COL_PLATFORMS else '',
            'status': row[self.COL_STATUS] if len(row) > self.COL_STATUS else '',
            'scheduled_time': row[self.COL_SCHEDULED_TIME] if len(row) > self.COL_SCHEDULED_TIME else '',
            'youtube_url': row[self.COL_YOUTUBE_URL] if len(row) > self.COL_YOUTUBE_URL else '',
            'facebook_url': row[self.COL_FACEBOOK_URL] if len(row) > self.COL_FACEBOOK_URL else '',
            'monetized': row[self.COL_MONETIZED] if len(row) > self.COL_MONETIZED else 'Yes',
            'notes': row[self.COL_NOTES] if len(row) > self.COL_NOTES else ''
        }
    
    def create_template_sheet(self, sheet_name: str = "OmniStream Content Calendar"):
        """
        Create a new sheet with template headers
        
        Args:
            sheet_name: Name for the new sheet
            
        Returns:
            URL of created sheet
        """
        if not self.worksheet:
            # Need to connect first
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                self.credentials_file, scope
            )
            client = gspread.authorize(creds)
            
            # Create new sheet
            self.sheet = client.create(sheet_name)
            self.worksheet = self.sheet.sheet1
        
        # Add headers
        headers = [
            'ID', 'Video Name', 'Drive Link', 'Title', 'Description',
            'Tags', 'Platforms', 'Status', 'Scheduled Time',
            'YouTube URL', 'Facebook URL', 'Monetized', 'Notes'
        ]
        
        self.worksheet.update('A1:M1', [headers])
        
        # Format header row
        self.worksheet.format('A1:M1', {
            'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.8},
            'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
        })
        
        # Add example row
        example_row = [
            1,
            'example_video.mp4',
            'https://drive.google.com/file/d/xxxxx',
            'Amazing Video Title',
            'This is an example description...',
            '#viral,#trending,#entertainment',
            'YouTube,Facebook',
            'Idle',
            '2024-12-31 10:00',
            '',
            '',
            'Yes',
            'Example video'
        ]
        self.worksheet.append_row(example_row)
        
        print(f"✅ Template sheet created: {sheet_name}")
        print(f"🔗 URL: {self.sheet.url}")
        
        return self.sheet.url


def setup_sheets():
    """Interactive setup for Sheets integration"""
    print("\n" + "="*70)
    print("🔧 Google Sheets Setup")
    print("="*70)
    
    print("\nOptions:")
    print("1. Create new Content Calendar sheet")
    print("2. Connect to existing sheet")
    
    choice = input("\nSelect option (1 or 2): ").strip()
    
    manager = SheetsManager()
    
    if choice == "1":
        print("\n📝 Creating new sheet...")
        sheet_name = input("Sheet name (default: OmniStream Content Calendar): ").strip()
        if not sheet_name:
            sheet_name = "OmniStream Content Calendar"
        
        url = manager.create_template_sheet(sheet_name)
        print(f"\n✅ Sheet created!")
        print(f"🔗 URL: {url}")
        print("\nNext steps:")
        print("1. Share this sheet with your Google account")
        print("2. Fill in video information")
        print("3. Run: python3 post_manager.py --run")
        
    elif choice == "2":
        sheet_url = input("\nPaste Google Sheet URL: ").strip()
        if manager.connect(sheet_url):
            print("\n✅ Connected successfully!")
            
            # Show pending videos
            pending = manager.get_pending_videos()
            print(f"\n📊 Found {len(pending)} pending videos")


if __name__ == "__main__":
    import sys
    
    if '--setup' in sys.argv:
        setup_sheets()
    elif '--test' in sys.argv:
        # Test connection
        manager = SheetsManager()
        if manager.worksheet:
            pending = manager.get_pending_videos()
            print(f"\n📊 Pending videos: {len(pending)}")
            for video in pending[:5]:
                print(f"  • {video['title']} ({video['status']})")
