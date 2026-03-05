#!/usr/bin/env python3
"""
Manhwa Flamingo — DRIVE-AWARE resumable downloader
Uses actual Drive file counts as source of truth (not DB).
Only downloads exactly what each channel still needs to reach 75.
Batch size: 25 per round.
"""

import sys
import time
import random

from smart_batch import extract_standard, extract_browser
from simple_downloader import SimplifiedDownloader
from drive_api import GoogleDriveAPI

FLAMINGO_FOLDER = '1Mmrem-JzM1tBArIJ-GrcaDX7qKRhTC5F'
TARGET = 150
BATCH_SIZE = 25

CHANNELS = [
    {'url': 'https://www.youtube.com/@Korasama-v/shorts',          'name': 'Korasama-v',          'handle': '@Korasama-v'},
    {'url': 'https://www.youtube.com/@TRUEMANHUA/shorts',          'name': 'TRUEMANHUA',           'handle': '@TRUEMANHUA'},
    {'url': 'https://www.youtube.com/@5th_Dimension_Manhwa/shorts','name': '5th_Dimension_Manhwa', 'handle': '@5th_Dimension_Manhwa'},
    {'url': 'https://www.youtube.com/@manhwaclash/shorts',         'name': 'manhwaclash',          'handle': '@manhwaclash'},
    {'url': 'https://www.youtube.com/@manhwaaddict13/shorts',      'name': 'manhwaaddict13',       'handle': '@manhwaaddict13'},
]


def count_in_drive(api, channel_handle):
    """Count files in the channel subfolder under Flamingo. Source of truth."""
    for folder_name in [channel_handle, channel_handle.lstrip('@')]:
        q = (f"'{FLAMINGO_FOLDER}' in parents and name='{folder_name}' "
             f"and mimeType='application/vnd.google-apps.folder' and trashed=false")
        r = api.service.files().list(q=q, fields='files(id)').execute()
        folders = r.get('files', [])
        if folders:
            fid = folders[0]['id']
            r2 = api.service.files().list(
                q=f"'{fid}' in parents and trashed=false",
                fields='files(id)', pageSize=200
            ).execute()
            return len(r2.get('files', []))
    return 0


def download_batch(channel, downloader, cap):
    """Download up to `cap` NEW videos for this channel. Returns count of new uploads."""
    url = channel['url']
    name = channel['name']

    print(f"\n  ⚡ Extracting video list for {name}...")
    videos = extract_standard(url, max_videos=None)
    if not videos:
        print(f"  🧠 Standard extraction empty — trying browser...")
        videos = extract_browser(url, max_videos=None)
    if not videos:
        print(f"  ❌ Could not extract any URLs for {name}. Skipping.")
        return 0

    print(f"  📋 {len(videos)} videos found. Need {cap} more new ones...")

    new_count = 0
    for i, video_url in enumerate(videos, 1):
        if new_count >= cap:
            break
        print(f"\n  [{i}/{len(videos)}] {video_url}")
        success, msg = downloader.download(video_url)

        is_dup = success and any(kw in msg for kw in ('Already in history', 'Already in Drive', 'Skipping'))
        if is_dup:
            print(f"  ⏭️  Duplicate — skipping")
        elif success:
            new_count += 1
            print(f"  ✅ #{new_count} uploaded [{new_count}/{cap}]")
        else:
            print(f"  ❌ Failed: {msg[:80]}")

    return new_count


def main():
    print("=" * 70)
    print("🎌 MANHWA FLAMINGO — DRIVE-AWARE RESUMABLE DOWNLOADER")
    print(f"   Target: {TARGET} per channel  |  Batch: {BATCH_SIZE}")
    print(f"   Folder: {FLAMINGO_FOLDER}")
    print("=" * 70)

    try:
        api = GoogleDriveAPI(service_account_file='__disabled__')
    except Exception as e:
        print(f"❌ Drive API init failed: {e}")
        sys.exit(1)

    downloader = SimplifiedDownloader(drive_api=api, base_folder_id=FLAMINGO_FOLDER)

    # Print current Drive state
    print("\n📊 Current Drive counts (source of truth):")
    for ch in CHANNELS:
        count = count_in_drive(api, ch['handle'])
        need = max(0, TARGET - count)
        status = '✅' if count >= TARGET else f'⏳ needs {need} more'
        print(f"  {status} | {ch['name']}: {count}/{TARGET}")

    round_num = 0
    while True:
        round_num += 1

        # Determine who still needs videos (check Drive live)
        pending = []
        for ch in CHANNELS:
            count = count_in_drive(api, ch['handle'])
            need = max(0, TARGET - count)
            if need > 0:
                pending.append((ch, count, need))

        if not pending:
            print("\n✅ All channels have reached 75 videos in Drive!")
            break

        print(f"\n{'*' * 70}")
        print(f"🔄  ROUND {round_num}  —  {len(pending)} channel(s) still need videos")
        print(f"{'*' * 70}")

        for i, (ch, drive_count, need) in enumerate(pending):
            cap = min(BATCH_SIZE, need)
            print(f"\n{'=' * 70}")
            print(f"📺  {ch['name']}")
            print(f"    In Drive: {drive_count}  |  Need: {need}  |  Batch cap: {cap}")
            print(f"{'=' * 70}")

            new = download_batch(ch, downloader, cap)

            # Re-check Drive after batch
            new_count = count_in_drive(api, ch['handle'])
            print(f"\n  📊 {ch['name']}: {new_count}/{TARGET} in Drive ({new} uploaded this batch)")

            if i < len(pending) - 1:
                rest = random.randint(60, 120)
                print(f"\n💤 Resting {rest}s before next channel...")
                time.sleep(rest)

        # Check if another round is needed
        still_pending = [ch for ch in CHANNELS if count_in_drive(api, ch['handle']) < TARGET]
        if still_pending:
            rest = random.randint(180, 360)
            names = [c['name'] for c in still_pending]
            print(f"\n⏸️  Round {round_num} done. Still pending: {names}")
            print(f"   Resting {rest}s before round {round_num + 1}...")
            time.sleep(rest)

    # Final summary
    print("\n" + "=" * 70)
    print("🏁  SESSION COMPLETE — Final Drive counts:")
    print("=" * 70)
    for ch in CHANNELS:
        count = count_in_drive(api, ch['handle'])
        status = '✅' if count >= TARGET else '⏳'
        print(f"  {status} {ch['name']:32s}: {count}/{TARGET}")
    print("=" * 70)


if __name__ == '__main__':
    main()
