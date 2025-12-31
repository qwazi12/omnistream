#!/usr/bin/env python3
"""
YouTube Video Uploader
Handles authentication and video uploads to YouTube via API
"""

import os
import pickle
from pathlib import Path
from typing import Optional, Dict, List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload


class YouTubePoster:
    """Upload videos to YouTube with metadata"""
    
    # YouTube API scopes
    SCOPES = ['https://www.googleapis.com/auth/youtube.upload',
              'https://www.googleapis.com/auth/youtube.force-ssl']
    
    # YouTube video categories
    CATEGORIES = {
        'Film & Animation': '1',
        'Autos & Vehicles': '2',
        'Music': '10',
        'Pets & Animals': '15',
        'Sports': '17',
        'Short Movies': '18',
        'Travel & Events': '19',
        'Gaming': '20',
        'Videoblogging': '21',
        'People & Blogs': '22',
        'Comedy': '23',
        'Entertainment': '24',
        'News & Politics': '25',
        'Howto & Style': '26',
        'Education': '27',
        'Science & Technology': '28',
        'Nonprofits & Activism': '29'
    }
    
    def __init__(
        self,
        credentials_file: str = 'youtube_credentials.json',
        token_file: str = 'youtube_token.pickle'
    ):
        """
        Initialize YouTube poster
        
        Args:
            credentials_file: Path to OAuth credentials JSON
            token_file: Path to save/load access token
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.youtube = None
        
    def authenticate(self) -> bool:
        """
        Authenticate with YouTube API using OAuth 2.0
        
        Returns:
            True if authentication successful
        """
        creds = None
        
        # Check for existing token
        if os.path.exists(self.token_file):
            print("📱 Loading saved YouTube credentials...")
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # Refresh expired token or get new one
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("🔄 Refreshing YouTube access token...")
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    print(f"❌ Error: {self.credentials_file} not found!")
                    print("\nTo get credentials:")
                    print("1. Go to https://console.cloud.google.com")
                    print("2. Enable YouTube Data API v3")
                    print("3. Create OAuth 2.0 credentials")
                    print("4. Download and save as youtube_credentials.json")
                    return False
                
                print("🔐 Starting OAuth flow...")
                print("A browser window will open for authorization")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next time
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
            print("✅ Credentials saved")
        
        # Build YouTube service
        try:
            self.youtube = build('youtube', 'v3', credentials=creds)
            print("✅ YouTube API connected")
            return True
        except Exception as e:
            print(f"❌ Error connecting to YouTube API: {e}")
            return False
    
    def upload_video(
        self,
        filepath: str,
        title: str,
        description: str = "",
        tags: List[str] = None,
        category: str = "22",
        privacy: str = "public",
        notify_subscribers: bool = True
    ) -> Optional[str]:
        """
        Upload video to YouTube
        
        Args:
            filepath: Path to video file
            title: Video title (max 100 characters)
            description: Video description (max 5000 characters)
            tags: List of tags (max 500 characters total)
            category: Category ID (default: People & Blogs)
            privacy: 'public', 'private', or 'unlisted'
            notify_subscribers: Send notification to subscribers
            
        Returns:
            Video ID if successful, None if failed
        """
        if not self.youtube:
            if not self.authenticate():
                return None
        
        if not os.path.exists(filepath):
            print(f"❌ Error: File not found: {filepath}")
            return None
        
        # Prepare metadata
        body = {
            'snippet': {
                'title': title[:100],  # Max 100 chars
                'description': description[:5000],  # Max 5000 chars
                'tags': tags or [],
                'categoryId': category
            },
            'status': {
                'privacyStatus': privacy,
                'selfDeclaredMadeForKids': False,
                'notifySubscribers': notify_subscribers
            }
        }
        
        # Create media upload
        media = MediaFileUpload(
            filepath,
            chunksize=-1,  # Upload in single request
            resumable=True
        )
        
        print(f"\n📤 Uploading to YouTube: {title}")
        print(f"   File: {Path(filepath).name}")
        print(f"   Size: {Path(filepath).stat().st_size / (1024*1024):.1f} MB")
        print(f"   Privacy: {privacy}")
        
        try:
            # Execute upload
            request = self.youtube.videos().insert(
                part='snippet,status',
                body=body,
                media_body=media
            )
            
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    print(f"   Progress: {progress}%", end='\r')
            
            video_id = response['id']
            video_url = f"https://youtube.com/watch?v={video_id}"
            
            print(f"\n✅ Upload complete!")
            print(f"   Video ID: {video_id}")
            print(f"   URL: {video_url}")
            
            return video_id
            
        except HttpError as e:
            print(f"\n❌ YouTube API error: {e}")
            if e.resp.status == 403:
                print("   This might be a quota issue. Check your quota at:")
                print("   https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas")
            return None
        except Exception as e:
            print(f"\n❌ Upload error: {e}")
            return None
    
    def set_thumbnail(self, video_id: str, thumbnail_path: str) -> bool:
        """
        Set custom thumbnail for video
        
        Args:
            video_id: YouTube video ID
            thumbnail_path: Path to thumbnail image (JPEG/PNG, max 2MB)
            
        Returns:
            True if successful
        """
        if not self.youtube:
            return False
        
        if not os.path.exists(thumbnail_path):
            print(f"❌ Thumbnail not found: {thumbnail_path}")
            return False
        
        try:
            self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path)
            ).execute()
            print(f"✅ Thumbnail set for video {video_id}")
            return True
        except Exception as e:
            print(f"❌ Error setting thumbnail: {e}")
            return False
    
    def add_to_playlist(self, video_id: str, playlist_id: str) -> bool:
        """
        Add video to playlist
        
        Args:
            video_id: YouTube video ID
            playlist_id: Playlist ID
            
        Returns:
            True if successful
        """
        if not self.youtube:
            return False
        
        try:
            self.youtube.playlistItems().insert(
                part='snippet',
                body={
                    'snippet': {
                        'playlistId': playlist_id,
                        'resourceId': {
                            'kind': 'youtube#video',
                            'videoId': video_id
                        }
                    }
                }
            ).execute()
            print(f"✅ Video added to playlist {playlist_id}")
            return True
        except Exception as e:
            print(f"❌ Error adding to playlist: {e}")
            return False
    
    def get_channel_info(self) -> Optional[Dict]:
        """Get authenticated user's channel info"""
        if not self.youtube:
            if not self.authenticate():
                return None
        
        try:
            response = self.youtube.channels().list(
                part='snippet,statistics',
                mine=True
            ).execute()
            
            if response['items']:
                channel = response['items'][0]
                return {
                    'id': channel['id'],
                    'title': channel['snippet']['title'],
                    'subscribers': channel['statistics'].get('subscriberCount', 'Hidden'),
                    'videos': channel['statistics']['videoCount']
                }
            return None
        except Exception as e:
            print(f"❌ Error getting channel info: {e}")
            return None


if __name__ == "__main__":
    # Test/demo
    import sys
    
    poster = YouTubePoster()
    
    if poster.authenticate():
        # Show channel info
        info = poster.get_channel_info()
        if info:
            print(f"\n📺 Connected to: {info['title']}")
            print(f"   Subscribers: {info['subscribers']}")
            print(f"   Total videos: {info['videos']}")
        
        # Example upload (comment out in production)
        # if len(sys.argv) > 1:
        #     video_path = sys.argv[1]
        #     video_id = poster.upload_video(
        #         filepath=video_path,
        #         title="Test Upload",
        #         description="Uploaded via OmniStream",
        #         privacy="private"  # Use private for testing
        #     )
