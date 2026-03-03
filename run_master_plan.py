#!/usr/bin/env python3
"""Master plan runner — loads channels and folders from config files.

Prefer using run.py for new sessions:
    python run.py master
"""
import time
import random
import subprocess
import sys
from config_loader import get_folder_id, get_channels

BATCH_SIZE = 50

FOLDER_MOVIE_CLIPS = get_folder_id('movie_clips')
FOLDER_FLAMINGO    = get_folder_id('flamingo')

PLAN_MOVIE_CLIPS = [(e['url'], e['name']) for e in get_channels('movie_clips')]
PLAN_FLAMINGO    = [(e['url'], e['name']) for e in get_channels('flamingo')]


def run_download(url, limit, folder_id):
    print(f"\n🚀 Starting download: {url}")
    subprocess.run([sys.executable, "smart_batch.py", url, str(limit), folder_id])


def random_rest(min_seconds=300, max_seconds=600):
    sleep_time = random.randint(min_seconds, max_seconds)
    print(f"\n💤 Resting {sleep_time}s ({sleep_time//60}m {sleep_time%60}s)...")
    time.sleep(sleep_time)
    print("🔔 Rest complete! Resuming...")


def main():
    print("=== OMNISTREAM MASTER DOWNLOAD PLAN ===")
    print(f"Total Channels: {len(PLAN_MOVIE_CLIPS) + len(PLAN_FLAMINGO)}")
    print(f"Video Limit: {BATCH_SIZE} per channel")

    print("\n🎬 STARTING PHASE 1: MOVIE CLIPS BATCH")
    for i, (url, name) in enumerate(PLAN_MOVIE_CLIPS):
        run_download(url, BATCH_SIZE, FOLDER_MOVIE_CLIPS)
        if (i + 1) % 3 == 0 and (i + 1) < len(PLAN_MOVIE_CLIPS):
            random_rest(120, 300)
        else:
            time.sleep(5)

    print("\n⏸️ PHASE 1 COMPLETE. Long Rest before Phase 2...")
    random_rest(600, 900)

    print("\n🦩 STARTING PHASE 2: FLAMINGO BATCH")
    for i, (url, name) in enumerate(PLAN_FLAMINGO):
        run_download(url, BATCH_SIZE, FOLDER_FLAMINGO)
        if (i + 1) % 3 == 0 and (i + 1) < len(PLAN_FLAMINGO):
            random_rest(120, 300)
        else:
            time.sleep(5)

    print("\n✅ ALL DOWNLOADS COMPLETE!")


if __name__ == "__main__":
    main()
