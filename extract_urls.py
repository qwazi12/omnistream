#!/usr/bin/env python3
"""
Extract video URLs from channel, then download individually
Workaround for YouTube API issues
"""

import yt_dlp
import sys

def extract_video_ids(channel_url, max_videos=None):
    """Extract video IDs from channel"""
    print(f"Extracting videos from: {channel_url}")
    
    opts = {
        'quiet': True,
        'extract_flat': True,  # Don't download, just get URLs
        'playlistend': max_videos
    }
    
    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            info = ydl.extract_info(channel_url, download=False)
            
            if 'entries' in info:
                videos = []
                for entry in info['entries']:
                    if entry:
                        video_id = entry.get('id')
                        if video_id:
                            videos.append(f"https://youtube.com/watch?v={video_id}")
                
                print(f"Found {len(videos)} videos")
                return videos
            else:
                print("No entries found")
                return []
        except Exception as e:
            print(f"Error: {e}")
            return []

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/@WOLFRoblox1"
    max_vids = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    videos = extract_video_ids(url, max_vids)
    
    for video_url in videos:
        print(video_url)
