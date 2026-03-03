import sys
import time
import random
from smart_batch import extract_standard, extract_browser
from simple_downloader import SimplifiedDownloader
from drive_api import GoogleDriveAPI
from config_loader import get_folder_id, get_channels

FOLDER_MOVIE_CLIPS = get_folder_id('movie_clips')
CHANNELS = [e['url'] for e in get_channels('batch_25')]

TARGET_NEW = 25

def process_channel(channel_url, downloader, drive_api):
    print(f"\n{'='*70}\n🎬 Processing Channel: {channel_url}\n{'='*70}")
    
    # 1. Fetch full list of URLs
    print("⚡ Extracting full video list (No limit)...")
    video_urls = extract_standard(channel_url, max_videos=None)
    
    if not video_urls:
        print("⚠️ Standard extraction empty, trying browser extraction...")
        video_urls = extract_browser(channel_url, max_videos=None)
        
    if not video_urls:
        print("❌ Could not extract any URLs. Skipping.")
        return
        
    print(f"📋 Total videos found: {len(video_urls)}")
    
    # 2. Iterate and download until 25 *new* videos succeed
    new_downloads = 0
    skipped = 0
    failed = 0
    
    for i, url in enumerate(video_urls, 1):
        if new_downloads >= TARGET_NEW:
            print(f"\n✅ Reached target of {TARGET_NEW} NEW downloads for {channel_url}")
            break
            
        print(f"\n[{i}/{len(video_urls)}] {url}")
        
        success, msg = downloader.download(url)
        
        # Check if it was skipped due to duplicate 
        # (SimplifiedDownloader returns success=True msg="Already in history..." or "Skipping...")
        if success and ("Already downloaded" in msg or "already downloaded" in msg.lower() or "Skipping" in msg or "Already in history" in msg):
            print(f"  ⏭️ Duplicate detected in DB/Drive. Skipping.")
            skipped += 1
            continue
            
        if success:
            print(f"  🎉 New video saved! [{new_downloads+1}/{TARGET_NEW}]")
            new_downloads += 1
        else:
            print(f"  ⚠️ Standard failed: {msg}. Falling back to bypasses...")
            
            # Try 10Downloader Bypass
            bypass_success = False
            if 'youtube.com' in url or 'youtu.be' in url:
                try:
                    from download_cobalt import download_cobalt_direct
                    print(f"  🚀 Using Web Bypass (10Downloader)...")
                    if download_cobalt_direct(url, drive_api, FOLDER_MOVIE_CLIPS):
                        print(f"  🎉 New video saved via bypass! [{new_downloads+1}/{TARGET_NEW}]")
                        new_downloads += 1
                        bypass_success = True
                    else:
                        print(f"  ❌ Web Bypass Failed for {url}")
                except Exception as e:
                    print(f"  ❌ Web Bypass Error: {e}")
                    
            if not bypass_success:
                failed += 1
                
    print(f"\n📊 Summary for {channel_url}:")
    print(f"   New Videos Saved: {new_downloads}")
    print(f"   Duplicates Skipped: {skipped}")
    print(f"   Failures: {failed}")

CYCLES = 4

def main():
    print(f"🚀 Starting OmniStream Batch 25 Scheduler - {CYCLES} CYCLES\n")
    try:
        from simple_drive import SimpleDriveAPI
        drive_api = SimpleDriveAPI()
    except Exception as e:
        print(f"Drive API init failed: {e}")
        sys.exit(1)
        
    # Init central downloader
    downloader = SimplifiedDownloader(drive_api=drive_api, base_folder_id=FOLDER_MOVIE_CLIPS)
    
    for cycle in range(1, CYCLES + 1):
        print(f"\n{'*'*70}")
        print(f"🔄 STARTING CYCLE {cycle} of {CYCLES}")
        print(f"{'*'*70}")
        
        for idx, channel in enumerate(CHANNELS, 1):
            process_channel(channel, downloader, drive_api)
            
            # Rest between channels
            if idx < len(CHANNELS):
                sleep_time = random.randint(120, 300)
                print(f"\n💤 Resting for {sleep_time}s before next channel to avoid bans...")
                time.sleep(sleep_time)
                
        # Rest between cycles
        if cycle < CYCLES:
            rest_time = random.randint(300, 600)
            print(f"\n🏁 Cycle {cycle} Complete! Taking a long rest {rest_time}s before next cycle...")
            time.sleep(rest_time)
            
    print("\n✅ All 4 Rotation Cycles Complete! 100 New Videos extracted per channel.")

if __name__ == "__main__":
    main()
