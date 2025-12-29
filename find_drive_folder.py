#!/usr/bin/env python3
"""
Find valid Google Drive folder for OmniStream uploads
"""

from drive_api import GoogleDriveAPI

def find_upload_folder():
    """Search for valid upload destination"""
    
    print("=" * 60)
    print("Finding Valid Upload Folder")
    print("=" * 60)
    
    drive_api = GoogleDriveAPI()
    
    # Get authenticated user info
    print("\n1. Checking authenticated account...")
    try:
        about = drive_api.service.about().get(fields='user').execute()
        user = about.get('user', {})
        print(f"   Email: {user.get('emailAddress')}")
        print(f"   Name: {user.get('displayName')}")
    except:
        pass
    
    # Search for "KY Media Content" or "Screen Central" or "Travis" folders
    print("\n2. Searching for existing folders...")
    
    search_terms = [
        "KY Media Content",
        "Screen Central",
        "Travis",
        "OmniDownloads"
    ]
    
    for term in search_terms:
        try:
            query = f"name contains '{term}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = drive_api.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, parents)',
                pageSize=20,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()
            
            files = results.get('files', [])
            if files:
                print(f"\n   Found folders matching '{term}':")
                for f in files:
                    print(f"     - {f['name']}")
                    print(f"       ID: {f['id']}")
        except Exception as e:
            print(f"   Error searching for '{term}': {e}")
    
    # List root-level folders
    print("\n3. Listing your root-level folders:")
    try:
        results = drive_api.service.files().list(
            q="mimeType='application/vnd.google-apps.folder' and 'root' in parents and trashed=false",
            spaces='drive',
            fields='files(id, name)',
            pageSize=50
        ).execute()
        
        folders = results.get('files', [])
        if folders:
            print(f"\n   You have {len(folders)} folders in 'My Drive':")
            for idx, folder in enumerate(folders[:20], 1):  # Show first 20
                print(f"   {idx}. {folder['name']}")
                print(f"      ID: {folder['id']}")
        else:
            print("   No folders found in root")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 60)
    print("What to do next:")
    print("=" * 60)
    print("\n1. Create a new folder in Google Drive web interface")
    print("   Name it: 'OmniDownloads' or similar")
    print("\n2. Right-click the folder → Get link → Copy folder ID")
    print("   (The ID is the part after 'folders/' in the URL)")
    print("\n3. Update OmniStream with the correct folder ID")

if __name__ == "__main__":
    find_upload_folder()
