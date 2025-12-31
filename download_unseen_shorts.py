#!/usr/bin/env python3
"""
Simple YouTube Shorts Downloader to Google Drive
Downloads Shorts and uploads directly to Google Drive
"""

import sys
import os
import subprocess
import shutil
from drive_api import GoogleDriveAPI


def main():
    # Config
    shorts_url = "https://www.youtube.com/@UnseenWorldsAI/shorts"
    drive_folder_id = "1AikLbQiUiYHfcDss9Po4wGU5lB590EWs"
    max_videos = 2 if "--test" in sys.argv else 45
    
    # Temp download location
    temp_dir = os.path.expanduser("~/Downloads/omnistream_temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    print(f"🎬 Downloading {max_videos} YouTube Shorts")
    print(f"📁 Google Drive Folder: {drive_folder_id}\n")
    
    # Download with yt-dlp
    cmd = [
        "yt-dlp",
        "--cookies", "cookies.txt",
        "--playlist-end", str(max_videos),
        "-o", f"{temp_dir}/%(title)s.%(ext)s",
        "--merge-output-format", "mp4",
        shorts_url
    ]
    
    print(f"📥 Running: {' '.join(cmd)}\n")
    result = subprocess.run(cmd, cwd=os.getcwd())
    
    if result.returncode != 0:
        print(f"\n❌ Download failed with code {result.returncode}")
        return 1
    
    # Upload to Drive
    print(f"\n📤 Uploading to Google Drive...")
    drive = GoogleDriveAPI()
    
    # Create YouTube/UnseenWorldsAI folders
    youtube_folder = drive.find_or_create_folder(drive_folder_id, "YouTube")
    channel_folder = drive.find_or_create_folder(youtube_folder, "UnseenWorldsAI")
    
    uploaded = 0
    for filename in os.listdir(temp_dir):
        if filename.endswith(".mp4"):
            filepath = os.path.join(temp_dir, filename)
            print(f"  ⬆️  {filename}")
            drive.upload_file(filepath, channel_folder, filename)
            uploaded += 1
    
    # Cleanup
    shutil.rmtree(temp_dir,ignore_errors=True)
    
    print(f"\n✅ Complete! Uploaded {uploaded} videos")
    print(f"🔗 View: https://drive.google.com/drive/folders/{channel_folder}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
