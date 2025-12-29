#!/usr/bin/env python3
"""
Google Drive API Authentication & Folder Verification Tool
Re-authenticates and verifies folder access
"""

import os
import sys
from drive_api import GoogleDriveAPI

def check_folder_access():
    """Check if we can access the target folder"""
    
    print("=" * 60)
    print("Google Drive Authentication & Folder Verification")
    print("=" * 60)
    
    target_folder_id = "1DQDRFQtl7fkgyXoP-sqRENau2WCLJH18"
    
    print(f"\n1. Authenticating with Google Drive...")
    print("   (Browser window will open for OAuth login)")
    
    try:
        # This will force fresh OAuth authentication
        drive_api = GoogleDriveAPI()
        
        print(f"\n2. Authentication Mode: {drive_api.auth_mode}")
        
        print(f"\n3. Testing folder access...")
        print(f"   Target Folder ID: {target_folder_id}")
        
        # Try to get folder metadata
        try:
            folder = drive_api.service.files().get(
                fileId=target_folder_id,
                fields='id, name, owners, capabilities, permissions',
                supportsAllDrives=True
            ).execute()
            
            print(f"\n✅ SUCCESS: Folder accessible!")
            print(f"   Folder Name: {folder.get('name')}")
            print(f"   Folder ID: {folder.get('id')}")
            
            # Check capabilities
            caps = folder.get('capabilities', {})
            can_edit = caps.get('canEdit', False)
            can_add_children = caps.get('canAddChildren', False)
            
            print(f"\n4. Permissions:")
            print(f"   Can Edit: {can_edit}")
            print(f"   Can Add Files: {can_add_children}")
            
            if can_add_children:
                print(f"\n✅ You have write access to this folder!")
            else:
                print(f"\n❌ WARNING: You do NOT have write access!")
                print(f"   This folder may be read-only or you need permission.")
            
            # Check storage quota
            print(f"\n5. Checking Google Drive storage...")
            about = drive_api.service.about().get(fields='storageQuota').execute()
            quota = about.get('storageQuota', {})
            
            limit = int(quota.get('limit', 0))
            usage = int(quota.get('usage', 0))
            
            if limit > 0:
                free = limit - usage
                free_gb = free / (1024**3)
                total_gb = limit / (1024**3)
                used_gb = usage / (1024**3)
                
                print(f"   Total Storage: {total_gb:.2f}GB")
                print(f"   Used: {used_gb:.2f}GB")
                print(f"   Free: {free_gb:.2f}GB")
                
                if free_gb > 5:
                    print(f"   ✅ Sufficient space available")
                else:
                    print(f"   ⚠️  WARNING: Low storage space!")
            else:
                print(f"   Storage: Unlimited (Google Workspace)")
            
            print(f"\n" + "=" * 60)
            print("Verification Complete!")
            print("=" * 60)
            
            if can_add_children and (limit == 0 or free_gb > 5):
                print("\n✅ ALL CHECKS PASSED")
                print("   OmniStream should now be able to upload files.")
                return True
            else:
                print("\n❌ ISSUES DETECTED")
                if not can_add_children:
                    print("   - No write permission to folder")
                if limit > 0 and free_gb < 5:
                    print("   - Low storage space")
                return False
                
        except Exception as e:
            print(f"\n❌ ERROR: Cannot access folder!")
            print(f"   Error: {str(e)}")
            print(f"\n   This could mean:")
            print(f"   - Folder doesn't exist")
            print(f"   - Folder ID is incorrect")
            print(f"   - You don't have permission to access it")
            return False
            
    except Exception as e:
        print(f"\n❌ Authentication failed!")
        print(f"   Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = check_folder_access()
    sys.exit(0 if success else 1)
