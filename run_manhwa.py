#!/usr/bin/env python3
"""
Manhwa Flamingo Downloader
Cycles through 5 manhwa channels until each has 75-125 videos
stored in their respective subfolders inside the Flamingo Drive folder.

Usage:
    python run_manhwa.py

Target: 75-125 new downloads per channel (stops each channel once it hits 75).
Batch size: 25 videos per pass per channel.
"""

import sys
import time
import random

from smart_batch import extract_standard, extract_browser
from simple_downloader import SimplifiedDownloader
from drive_api import GoogleDriveAPI
from config_loader import get_folder_id

FLAMINGO_FOLDER = get_folder_id('flamingo', '1Mmrem-JzM1tBArIJ-GrcaDX7qKRhTC5F')

CHANNELS = [
    {'url': 'https://www.youtube.com/@Korasama-v/shorts',          'name': 'Korasama-v'},
    {'url': 'https://www.youtube.com/@TRUEMANHUA/shorts',          'name': 'TRUEMANHUA'},
    {'url': 'https://www.youtube.com/@5th_Dimension_Manhwa/shorts', 'name': '5th_Dimension_Manhwa'},
    {'url': 'https://www.youtube.com/@manhwaclash/shorts',         'name': 'manhwaclash'},
    {'url': 'https://www.youtube.com/@manhwaaddict13/shorts',      'name': 'manhwaaddict13'},
]

TARGET_MIN  = 75   # stop channel once this many NEW videos are downloaded
TARGET_MAX  = 125  # never exceed this total per channel per session
BATCH_SIZE  = 25   # max new downloads per channel per round


def count_existing_in_db(channel_name: str) -> int:
    """Query local DB for previously downloaded videos from this channel."""
    try:
        from database import get_history
        db = get_history()
        cursor = db._conn.cursor()
        cursor.execute(
            'SELECT COUNT(*) FROM download_history WHERE channel_name = ?',
            (channel_name,)
        )
        return cursor.fetchone()[0]
    except Exception:
        return 0


def download_new_videos(channel: dict, downloader, cap: int) -> int:
    """
    Extract video list then download until `cap` NEW videos succeed.
    Returns count of NEW downloads (skips / already-in-Drive not counted).
    """
    url  = channel['url']
    name = channel['name']

    print(f"\n  ⚡ Extracting video list for {name}...")
    videos = extract_standard(url, max_videos=None)
    if not videos:
        print(f"  🧠 Standard extraction empty — trying browser extraction...")
        videos = extract_browser(url, max_videos=None)

    if not videos:
        print(f"  ❌ Could not extract any URLs for {name}. Skipping.")
        return 0

    print(f"  📋 {len(videos)} videos found. Downloading up to {cap} new ones...")

    new_count = 0
    for i, video_url in enumerate(videos, 1):
        if new_count >= cap:
            break

        print(f"\n  [{i}/{len(videos)}] {video_url}")
        success, msg = downloader.download(video_url)

        is_duplicate = success and any(
            kw in msg for kw in ('Already in history', 'Already in Drive', 'already downloaded', 'Skipping')
        )

        if is_duplicate:
            print(f"  ⏭️  Duplicate — skipping")
        elif success:
            new_count += 1
            print(f"  ✅ New video #{new_count} saved [{new_count}/{cap}]")
        else:
            print(f"  ❌ Failed: {msg[:80]}")

    return new_count


def main():
    print("=" * 70)
    print("🎌 MANHWA FLAMINGO DOWNLOADER")
    print(f"   Target: {TARGET_MIN}–{TARGET_MAX} new downloads per channel")
    print(f"   Batch:  {BATCH_SIZE} per pass | Folder: {FLAMINGO_FOLDER}")
    print("=" * 70)

    try:
        drive_api = GoogleDriveAPI()
    except Exception as e:
        print(f"❌ Drive API init failed: {e}")
        sys.exit(1)

    # Check existing DB counts — track total = existing + new this session
    existing = {ch['name']: count_existing_in_db(ch['name']) for ch in CHANNELS}
    session  = {ch['name']: 0 for ch in CHANNELS}

    print("\n📊 Existing DB counts (videos already downloaded from these channels):")
    for ch in CHANNELS:
        print(f"   {ch['name']:30s}: {existing[ch['name']]} in DB")

    # One downloader instance, pointed at Flamingo folder
    downloader = SimplifiedDownloader(drive_api=drive_api, base_folder_id=FLAMINGO_FOLDER)

    round_num = 0
    while True:
        round_num += 1

        # Channels that still need more: total so far < TARGET_MIN
        pending = [
            ch for ch in CHANNELS
            if (existing[ch['name']] + session[ch['name']]) < TARGET_MIN
        ]

        if not pending:
            print("\n✅ All channels have reached their targets!")
            break

        print(f"\n{'*' * 70}")
        print(f"🔄  ROUND {round_num}  —  {len(pending)} channel(s) still need videos")
        print(f"{'*' * 70}")

        for i, ch in enumerate(pending):
            name        = ch['name']
            total_so_far = existing[name] + session[name]
            # Cap this batch so we don't overshoot TARGET_MAX
            batch_cap   = min(BATCH_SIZE, TARGET_MAX - total_so_far)

            print(f"\n{'=' * 70}")
            print(f"📺  {name}")
            print(f"    In DB: {existing[name]}  |  This session: {session[name]}  |  "
                  f"Total: {total_so_far}/{TARGET_MIN}  |  Batch cap: {batch_cap}")
            print(f"{'=' * 70}")

            new = download_new_videos(ch, downloader, batch_cap)
            session[name] += new

            total_now = existing[name] + session[name]
            print(f"\n  📊 {name}: {total_now}/{TARGET_MIN} total "
                  f"({session[name]} new this session)")

            # Rest between channels (not after the last one)
            if i < len(pending) - 1:
                rest = random.randint(60, 120)
                print(f"\n💤 Resting {rest}s before next channel...")
                time.sleep(rest)

        # Check if more rounds needed
        still_pending = [
            ch for ch in CHANNELS
            if (existing[ch['name']] + session[ch['name']]) < TARGET_MIN
        ]
        if still_pending:
            rest = random.randint(180, 360)
            names = [c['name'] for c in still_pending]
            print(f"\n⏸️  Round {round_num} done. Still pending: {names}")
            print(f"   Resting {rest}s before round {round_num + 1}...")
            time.sleep(rest)

    # Final summary
    print("\n" + "=" * 70)
    print("🏁  MANHWA FLAMINGO — SESSION COMPLETE")
    print("=" * 70)
    for ch in CHANNELS:
        name = ch['name']
        total = existing[name] + session[name]
        print(f"  {name:32s}: {session[name]:3d} new  |  {total:3d} total in DB")
    print("=" * 70)


if __name__ == '__main__':
    main()
