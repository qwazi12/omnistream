#!/usr/bin/env python3
"""
Facebook Video Uploader
Handles video uploads to Facebook Pages via Graph API
"""

import os
import json
import requests
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime, timedelta


class FacebookPoster:
    """Upload videos to Facebook Pages"""
    
    API_VERSION = 'v18.0'
    BASE_URL = f'https://graph.facebook.com/{API_VERSION}'
    
    def __init__(self, config_file: str = 'facebook_config.json'):
        """
        Initialize Facebook poster
        
        Args:
            config_file: Path to config with page access token
        """
        self.config_file = config_file
        self.access_token = None
        self.page_id = None
        self.session = requests.Session()
        
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.access_token = config.get('page_access_token')
                self.page_id = config.get('page_id')
                print("✅ Facebook config loaded")
        else:
            print(f"⚠️  {self.config_file} not found - will need to setup")
    
    def save_config(self, page_access_token: str, page_id: str):
        """
        Save Facebook configuration
        
        Args:
            page_access_token: Long-lived Page Access Token
            page_id: Facebook Page ID
        """
        config = {
            'page_access_token': page_access_token,
            'page_id': page_id,
            'api_version': self.API_VERSION
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        self.access_token = page_access_token
        self.page_id = page_id
        print(f"✅ Config saved to {self.config_file}")
    
    def get_pages(self, user_access_token: str) -> List[Dict]:
        """
        Get list of Pages user manages
        
        Args:
            user_access_token: User Access Token from Graph API Explorer
            
        Returns:
            List of pages with id, name, and access_token
        """
        url = f"{self.BASE_URL}/me/accounts"
        params = {'access_token': user_access_token}
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            pages = response.json().get('data', [])
            print(f"\n📄 Found {len(pages)} Pages:")
            for page in pages:
                print(f"   • {page['name']} (ID: {page['id']})")
            
            return pages
        except Exception as e:
            print(f"❌ Error getting pages: {e}")
            return []
    
    def upload_video(
        self,
        filepath: str,
        caption: str = "",
        title: str = "",
        description: str = "",
        tags: List[str] = None,
        published: bool = True,
        schedule_time: Optional[datetime] = None
    ) -> Optional[str]:
        """
        Upload video to Facebook Page
        
        Args:
            filepath: Path to video file
            caption: Post caption/description
            title: Video title (optional)
            description: Video description (optional)
            tags: List of hashtags (optional)
            published: Publish immediately (True) or schedule (False)
            schedule_time: When to publish (if published=False)
            
        Returns:
            Video ID if successful, None if failed
        """
        if not self.access_token or not self.page_id:
            print("❌ Facebook not configured. Run setup first.")
            return None
        
        if not os.path.exists(filepath):
            print(f"❌ File not found: {filepath}")
            return None
        
        file_size = Path(filepath).stat().st_size
        
        # Facebook has 10GB limit
        if file_size > 10 * 1024 * 1024 * 1024:
            print(f"❌ File too large: {file_size / (1024**3):.1f} GB (max 10 GB)")
            return None
        
        print(f"\n📤 Uploading to Facebook Page")
        print(f"   File: {Path(filepath).name}")
        print(f"   Size: {file_size / (1024*1024):.1f} MB")
        
        # Step 1: Initialize upload session
        init_url = f"{self.BASE_URL}/{self.page_id}/videos"
        
        init_params = {
            'access_token': self.access_token,
            'upload_phase': 'start',
            'file_size': file_size
        }
        
        try:
            # Start upload session
            print("   Initializing upload...")
            response = self.session.post(init_url, params=init_params)
            response.raise_for_status()
            
            upload_session_id = response.json().get('upload_session_id')
            video_id = response.json().get('video_id')
            
            # Step 2: Upload video file
            print("   Uploading video...")
            transfer_url = f"{self.BASE_URL}/{self.page_id}/videos"
            
            with open(filepath, 'rb') as video_file:
                transfer_params = {
                    'access_token': self.access_token,
                    'upload_phase': 'transfer',
                    'upload_session_id': upload_session_id
                }
                
                files = {'video_file_chunk': video_file}
                
                response = self.session.post(
                    transfer_url,
                    params=transfer_params,
                    files=files
                )
                response.raise_for_status()
            
            # Step 3: Finish upload and publish
            print("   Finalizing...")
            finish_params = {
                'access_token': self.access_token,
                'upload_phase': 'finish',
                'upload_session_id': upload_session_id,
                'title': title,
                'description': caption or description,
                'published': 'true' if published else 'false'
            }
            
            # Add schedule time if provided
            if schedule_time and not published:
                timestamp = int(schedule_time.timestamp())
                finish_params['scheduled_publish_time'] = timestamp
                finish_params['unpublished_content_type'] = 'SCHEDULED'
            
            response = self.session.post(transfer_url, params=finish_params)
            response.raise_for_status()
            
            result = response.json()
            video_id = result.get('id') or video_id
            
            video_url = f"https://www.facebook.com/{video_id}"
            
            print(f"\n✅ Upload complete!")
            print(f"   Video ID: {video_id}")
            print(f"   URL: {video_url}")
            
            if schedule_time and not published:
                print(f"   Scheduled for: {schedule_time.strftime('%Y-%m-%d %H:%M')}")
            
            return video_id
            
        except requests.exceptions.HTTPError as e:
            print(f"\n❌ Facebook API error: {e}")
            print(f"   Response: {e.response.text}")
            return None
        except Exception as e:
            print(f"\n❌ Upload error: {e}")
            return None
    
    def get_video_insights(self, video_id: str) -> Optional[Dict]:
        """
        Get analytics/insights for a video
        
        Args:
            video_id: Facebook video ID
            
        Returns:
            Dict with video insights (views, likes, etc.)
        """
        if not self.access_token:
            return None
        
        url = f"{self.BASE_URL}/{video_id}"
        params = {
            'access_token': self.access_token,
            'fields': 'views,likes.summary(true),comments.summary(true),created_time,length'
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            insights = {
                'views': data.get('views', 0),
                'likes': data.get('likes', {}).get('summary', {}).get('total_count', 0),
                'comments': data.get('comments', {}).get('summary', {}).get('total_count', 0),
                'created_time': data.get('created_time'),
                'duration': data.get('length', 0)
            }
            
            return insights
        except Exception as e:
            print(f"❌ Error getting insights: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Test if configuration is valid"""
        if not self.access_token or not self.page_id:
            print("❌ Not configured")
            return False
        
        url = f"{self.BASE_URL}/{self.page_id}"
        params = {
            'access_token': self.access_token,
            'fields': 'name,fan_count'
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            page = response.json()
            print(f"✅ Connected to: {page['name']}")
            print(f"   Followers: {page.get('fan_count', 'Unknown')}")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False


def setup_facebook():
    """Interactive setup for Facebook posting"""
    print("\n" + "="*70)
    print("🔧 Facebook Posting Setup")
    print("="*70)
    
    print("\nTo upload videos to Facebook, you need:")
    print("1. A Facebook Page (not personal profile)")
    print("2. A Page Access Token")
    print("\nSteps to get Page Access Token:")
    print("1. Go to: https://developers.facebook.com/tools/explorer")
    print("2. Select your App (or create one)")
    print("3. Click 'Get User Access Token'")
    print("4. Select permissions: pages_manage_posts, pages_read_engagement")
    print("5. Click 'Generate Access Token'")
    print("6. Copy the token\n")
    
    user_token = input("Paste User Access Token: ").strip()
    
    if not user_token:
        print("❌ Setup cancelled")
        return
    
    poster = FacebookPoster()
    pages = poster.get_pages(user_token)
    
    if not pages:
        print("❌ No pages found. Make sure you manage at least one Page.")
        return
    
    if len(pages) == 1:
        page = pages[0]
        print(f"\n✅ Using page: {page['name']}")
    else:
        print("\nSelect a page:")
        for i, page in enumerate(pages, 1):
            print(f"{i}. {page['name']}")
        
        choice = int(input("\nEnter page number: ")) - 1
        page = pages[choice]
    
    # Save configuration with Page Access Token
    poster.save_config(
        page_access_token=page['access_token'],
        page_id=page['id']
    )
    
    print("\n✅ Setup complete!")
    poster.test_connection()


if __name__ == "__main__":
    import sys
    
    if '--setup' in sys.argv:
        setup_facebook()
    else:
        # Test connection
        poster = FacebookPoster()
        poster.test_connection()
