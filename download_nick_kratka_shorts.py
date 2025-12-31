#!/usr/bin/env python3
"""
Download YouTube Shorts from @Nick_Kratka to Google Drive
Simple direct approach: yt-dlp download → Drive upload
"""

import sys
import os
import subprocess
import shutil
from pathlib import Path
from drive_api import GoogleDriveAPI


def main():
    shorts_url = "https://www.youtube.com/@Nick_Kratka/shorts"
    drive_folder_id = "1AikLbQiUiYHfcDss9Po4wGU5lB590EWs"  # "Second Track" folder
    channel_name = "Nick_Kratka"
    max_videos = 100
    
    temp_dir = Path.home() / "Downloads/yt_shorts_temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print(f"🎬 Downloading {max_videos} YouTube Shorts")
    print(f"📺 Channel: @{channel_name}")
    print(f"📁 Drive: Second Track/{channel_name}")
    print("=" * 70 + "\n")
    
    # Download with yt-dlp
    cmd = [
        "yt-dlp",
        "--cookies", "cookies.txt",
        "--playlist-end", str(max_videos),
        "-o", f"{temp_dir}/%(title)s.%(ext)s",
        "--merge-output-format", "mp4",
        shorts_url
    ]
    
    print(f"📥 Running yt-dlp...\n")
    result = subprocess.run(cmd, cwd=os.getcwd())
    
    if result.returncode != 0:
        print(f"\n❌ Download failed")
        return 1
    
    # Upload to Drive
    print(f"\n📤 Uploading to Google Drive...")
    drive = GoogleDriveAPI()
    
    # Create channel subfolder inside "Second Track"
    channel_folder = drive.find_or_create_folder(drive_folder_id, channel_name)
    
    uploaded = 0
    for filename in os.listdir(temp_dir):
        if filename.endswith(".mp4"):
            filepath = os.path.join(temp_dir, filename)
            print(f"  ⬆️  {filename}")
            drive.upload_file(filepath, channel_folder, filename)
            uploaded += 1
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)
    
    print(f"\n✅ Complete! Uploaded {uploaded} videos")
    print(f"🔗 View: https://drive.google.com/drive/folders/{channel_folder}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
