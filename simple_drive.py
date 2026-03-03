"""
SimpleDriveAPI — backwards-compatible alias for GoogleDriveAPI.

GoogleDriveAPI now supports:
  - Service account auth (preferred) with OAuth fallback
  - find_or_create_folder(names_list, parent_id)   ← new/smart style
  - find_or_create_folder(parent_id, name)          ← old style (still works)
  - upload_file(file_path, folder_id, filename)     ← flat upload
  - upload_with_channel(file_path, channel_info, base_folder_id, platform)
"""

from drive_api import GoogleDriveAPI

SimpleDriveAPI = GoogleDriveAPI
