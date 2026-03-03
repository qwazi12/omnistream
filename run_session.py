#!/usr/bin/env python3
"""Session runner — loads channels and folders from config files.

Prefer using run.py for new sessions:
    python run.py session
"""
import time
import random
import subprocess
import sys
from config_loader import get_folder_id, get_channels


def run_download(channel, limit, folder_id):
    print(f"\n🚀 Starting download for {channel}...")
    subprocess.run([sys.executable, "smart_batch.py", channel, str(limit), folder_id])


def random_rest():
    sleep_time = random.randint(300, 900)
    print(f"\n💤 Resting {sleep_time}s ({sleep_time//60}m {sleep_time%60}s)...")
    time.sleep(sleep_time)
    print("🔔 Rest complete! Resuming...")


def main():
    batch1_folder   = get_folder_id('second_track_clips')
    batch1_channels = [e['url'] for e in get_channels('second_track_clips')]

    print("=== STARTING SESSION: BATCH 1 (Second Track Clips) ===")
    random_rest()

    for channel in batch1_channels:
        run_download(channel, 50, batch1_folder)
        time.sleep(10)

    batch2_folder   = get_folder_id('flamingo')
    batch2_channels = [e['url'] for e in get_channels('flamingo')]

    print("\n=== STARTING SESSION: BATCH 2 (Flamingo) ===")
    random_rest()

    for channel in batch2_channels:
        run_download(channel, 50, batch2_folder)
        time.sleep(10)

    print("\n✅ All batches complete!")


if __name__ == "__main__":
    main()
