#!/usr/bin/env python3
"""
Check what folders the service account can actually see
"""

from drive_api import GoogleDriveAPI

def list_accessible_folders():
    """List all folders the service account has access to"""
    
    print("=" * 60)
    print("Service Account - Accessible Folders")
    print("=" * 60)
    
    drive_api = GoogleDriveAPI()
    
    print(f"\nAuth Mode: {drive_api.auth_mode}")
    
    if drive_api.auth_mode == 'service_account':
        print("✅ Using Service Account (Pro Mode)")
    else:
        print("⚠️  Using OAuth (not service account)")
        return
    
    print("\nSearching for folders shared with this service account...")
    
    try:
        # List all folders accessible to service account
        results = drive_api.service.files().list(
            q="mimeType='application/vnd.google-apps.folder' and trashed=false",
            spaces='drive',
            fields='files(id, name, capabilities, owners)',
            pageSize=100,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        
        files = results.get('files', [])
        
        if not files:
            print("\n❌ NO FOLDERS FOUND")
            print("\nThis means the service account has not been granted")
            print("access to ANY folders yet.")
            print("\nTo fix:")
            print("1. Go to Google Drive web interface")
            print("2. Find folder: 1DQDRFQtl7fkgyXoP-sqRENau2WCLJH18")
            print("3. Right-click → Share")
            print("4. Add: drive-uploader@manhwa-engine.iam.gserviceaccount.com")
            print("5. Permission: Editor")
            print("6. UNCHECK 'Notify people'")
            print("7. Click Share")
        else:
            print(f"\n✅ Found {len(files)} accessible folder(s):\n")
            for f in files:
                print(f"📁 {f['name']}")
                print(f"   ID: {f['id']}")
                caps = f.get('capabilities', {})
                print(f"   Can Add Files: {caps.get('canAddChildren', False)}")
                print()
            
            # Check if target folder is in the list
            target_id = "1DQDRFQtl7fkgyXoP-sqRENau2WCLJH18"
            if any(f['id'] == target_id for f in files):
                print(f"✅ TARGET FOLDER FOUND!")
                print(f"   Service account has access to: {target_id}")
            else:
                print(f"❌ TARGET FOLDER NOT IN LIST")
                print(f"   Looking for: {target_id}")
                print(f"   This folder has not been shared with the service account.")
                
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    list_accessible_folders()
