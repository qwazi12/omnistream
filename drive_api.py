"""
Google Drive API wrapper for OmniStream
Enables direct uploads to shared folders bypassing filesystem limitations
"""

import os
import io
import pickle
from typing import List, Optional, Dict
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/drive.file']


class GoogleDriveAPI:
    """Google Drive API client for file uploads"""
    
    def __init__(self, credentials_file: str = 'credentials.json', token_file: str = 'token.pickle', service_account_file: str = 'service_account.json'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service_account_file = service_account_file
        self.service = None
        self.auth_mode = None  # 'service_account' or 'oauth'
        self.authenticate()
    
    def authenticate(self):
        """
        Authenticate with Google Drive API
        Priority: Service Account (Pro Mode) > OAuth (User Mode)
        """
        creds = None
        
        # OPTION 1: Service Account (Pro Mode - Never expires, stable)
        if os.path.exists(self.service_account_file):
            try:
                creds = service_account.Credentials.from_service_account_file(
                    self.service_account_file,
                    scopes=SCOPES
                )
                self.auth_mode = 'service_account'
                print("🔑 Google Drive: Pro Mode (Service Account)")
            except Exception as e:
                print(f"⚠️  Service account auth failed: {e}")
                print("   Falling back to OAuth...")
                creds = None
        
        # OPTION 2: OAuth (User Mode - Requires browser login)
        if creds is None:
            # Load cached token if exists
            if os.path.exists(self.token_file):
                with open(self.token_file, 'rb') as token:
                    creds = pickle.load(token)
            
            # If no valid credentials, authenticate
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    # Refresh expired token
                    creds.refresh(Request())
                else:
                    # Run OAuth flow
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for next run
                with open(self.token_file, 'wb') as token:
                    pickle.dump(creds, token)
            
            self.auth_mode = 'oauth'
            print("👤 Google Drive: User Mode (OAuth)")
        
        # Build Drive service
        self.service = build('drive', 'v3', credentials=creds)
        print("✓ Google Drive API initialized")
    
    def find_folder_by_path(self, path_parts: List[str]) -> Optional[str]:
        """
        Navigate folder hierarchy and return folder ID
        
        Args:
            path_parts: List of folder names, e.g. ['KY Media Content', 'Screen Central', 'Travis']
        
        Returns:
            Folder ID or None if not found
        """
        current_folder_id = 'root'
        
        for folder_name in path_parts:
            # Search for folder in current parent
            query = (
                f"name='{folder_name}' and "
                f"'{current_folder_id}' in parents and "
                f"mimeType='application/vnd.google-apps.folder' and "
                f"trashed=false"
            )
            
            try:
                results = self.service.files().list(
                    q=query,
                    spaces='drive',
                    fields='files(id, name)',
                    includeItemsFromAllDrives=True,
                    supportsAllDrives=True
                ).execute()
                
                files = results.get('files', [])
                
                if not files:
                    # Folder doesn't exist, create it
                    folder_metadata = {
                        'name': folder_name,
                        'mimeType': 'application/vnd.google-apps.folder',
                        'parents': [current_folder_id]
                    }
                    folder = self.service.files().create(
                        body=folder_metadata,
                        fields='id',
                        supportsAllDrives=True
                    ).execute()
                    current_folder_id = folder.get('id')
                else:
                    current_folder_id = files[0].get('id')
            
            except HttpError as e:
                print(f"[ERROR] Failed to navigate to folder '{folder_name}': {e}")
                return None
        
        return current_folder_id
    
    def find_or_create_folder(self, parent_id: str, folder_name: str) -> Optional[str]:
        """
        Find or create a folder within parent
        
        Args:
            parent_id: Parent folder ID
            folder_name: Name of folder to find/create
        
        Returns:
            Folder ID or None on error
        """
        # Search for existing folder
        query = (
            f"name='{folder_name}' and "
            f"'{parent_id}' in parents and "
            f"mimeType='application/vnd.google-apps.folder' and "
            f"trashed=false"
        )
        
        try:
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                includeItemsFromAllDrives=True,
                supportsAllDrives=True
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                return files[0].get('id')
            
            # Create folder if not found
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }
            folder = self.service.files().create(
                body=folder_metadata,
                fields='id',
                supportsAllDrives=True
            ).execute()
            return folder.get('id')
        
        except HttpError as e:
            print(f"[ERROR] Failed to create folder '{folder_name}': {e}")
            return None
    
    def upload_file(self, file_path: str, folder_id: str, filename: Optional[str] = None) -> Optional[Dict]:
        """
        Upload file to Google Drive
        
        Args:
            file_path: Local file path
            folder_id: Parent folder ID
            filename: Optional custom filename (defaults to basename)
        
        Returns:
            File metadata dict with id, name, webViewLink or None on error
        """
        if filename is None:
            filename = os.path.basename(file_path)
        
        # Verify file exists
        if not os.path.exists(file_path):
            print(f"[ERROR] File not found: {file_path}")
            return None
        
        file_size = os.path.getsize(file_path)
        print(f"[INFO] Uploading file: {filename} ({file_size} bytes)")
        print(f"[INFO] Target folder ID: {folder_id}")
        
        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }
        
        try:
            media = MediaFileUpload(
                file_path,
                resumable=True
            )
            
            print(f"[INFO] Starting upload to Drive...")
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink',
                supportsAllDrives=True
            ).execute()
            
            print(f"[SUCCESS] Upload complete: {file.get('name')}")
            return file
        
        except HttpError as e:
            print(f"[ERROR] HTTP Error during upload: {e}")
            print(f"[ERROR] Error details: {e.error_details if hasattr(e, 'error_details') else 'No details'}")
            return None
        except Exception as e:
            print(f"[ERROR] Unexpected error during upload: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def upload_from_bytes(self, file_bytes: bytes, filename: str, folder_id: str, mimetype: str = 'video/mp4') -> Optional[Dict]:
        """
        Upload file directly from bytes (no local file needed)
        
        Args:
            file_bytes: File content as bytes
            filename: Filename for uploaded file
            folder_id: Parent folder ID
            mimetype: MIME type of file
        
        Returns:
            File metadata dict or None on error
        """
        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }
        
        try:
            media = MediaIoBaseUpload(
                io.BytesIO(file_bytes),
                mimetype=mimetype,
                resumable=True
            )
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink',
                supportsAllDrives=True
            ).execute()
            
            return file
        
        except HttpError as e:
            print(f"[ERROR] Failed to upload bytes as '{filename}': {e}")
            return None
