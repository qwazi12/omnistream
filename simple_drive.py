#!/usr/bin/env python3
"""
SIMPLIFIED Drive API - OAuth only, Travis/YouTube/Channel structure
"""

import os
import pickle
from typing import Optional, Dict
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/drive.file']

class SimpleDriveAPI:
    def __init__(self):
        self.service = None
        self.authenticate()
    
    def authenticate(self):
        """OAuth authentication only"""
        creds = None
        
        # Load existing token
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        # Refresh or create new token
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save token
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('drive', 'v3', credentials=creds)
        print("👤 Google Drive: OAuth Mode")
        print("✓ Google Drive API initialized")
    
    def find_or_create_folder(self, folder_names: list, parent_id: str) -> str:
        """
        Find existing folder matching ANY name in the list, or create new one using the first name.
        Args:
            folder_names: List of names to check (e.g., ['@IndieLens-m5m', 'Indie Lens'])
            parent_id: ID of parent folder
        """
        # Ensure input is a list
        if isinstance(folder_names, str):
            folder_names = [folder_names]
            
        # 1. Search for ANY existing folder matching one of the names
        # Construct query: (name = 'Name1' or name = 'Name2') and ...
        name_queries = [f"name = '{name.replace("'", "\\'")}'" for name in folder_names if name]
        if not name_queries:
            return None
            
        query = f"({' or '.join(name_queries)}) and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        
        try:
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                pageSize=1
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                found_name = files[0]['name']
                print(f"✓ Found existing folder: {found_name}")
                return files[0]['id']
            
            # 2. If none found, create new folder using the PRIMARY name (first in list)
            primary_name = folder_names[0]
            if not primary_name:
                primary_name = "Unknown_Channel"
                
            file_metadata = {
                'name': primary_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            print(f"✓ Created folder: {primary_name}")
            return folder['id']
        
        except Exception as e:
            print(f"Error finding/creating folder: {e}")
            return None
    
    def upload_file(self, file_path: str, channel_info: dict, base_folder_id: str, platform: str = 'YouTube') -> Optional[Dict]:
        """
        Upload file to Drive with Smart Folder Merging
        
        Args:
            file_path: Local MP4 file
            channel_info: Dict with keys 'handle', 'name', 'id'
            base_folder_id: ID of Travis folder
            platform: Platform name (YouTube, Instagram, TikTok, Twitter)
        """
        try:
            # 1. Get Travis Folder (Base)
            current_folder_id = base_folder_id
            
            # 2. Get/Create Platform folder (YouTube, Instagram, TikTok, etc.)
            current_folder_id = self.find_or_create_folder([platform], current_folder_id)
            if not current_folder_id: return None
            
            # 3. Get/Create Channel Folder (Smart Merge)
            # Prioritize: @Handle -> Display Name -> Channel ID
            potential_names = []
            if channel_info.get('handle'):
                potential_names.append(channel_info['handle']) # Primary: @IndieLens-m5m
            if channel_info.get('name'):
                potential_names.append(channel_info['name'])   # Secondary: Indie Lens
            if channel_info.get('id'):
                potential_names.append(channel_info['id'])     # Fallback: UC...
                
            current_folder_id = self.find_or_create_folder(potential_names, current_folder_id)
            if not current_folder_id: return None
            
            # 4. Upload File
            file_metadata = {
                'name': os.path.basename(file_path),
                'parents': [current_folder_id]
            }
            
            media = MediaFileUpload(file_path, resumable=True)
            
            folder_str = f"Travis/{platform}/{potential_names[0] if potential_names else 'Unknown'}"
            print(f"Uploading file: {os.path.basename(file_path)} ({os.path.getsize(file_path)} bytes)")
            print(f"Target folder: {folder_str}")
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()
            
            print(f"Upload complete: {file.get('name')}")
            return file
        
        except Exception as e:
            print(f"Upload error: {e}")
            return None
