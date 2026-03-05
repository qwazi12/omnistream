#!/usr/bin/env python3
"""
Manhwa Flamingo — PARALLEL downloader
Runs all 5 channels simultaneously, each in its own process.
Target: 75-125 videos per channel.
"""

import sys
import os
import time
import random
import multiprocessing
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

TARGET_MIN = 75
TARGET_MAX = 125


def count_in_drive(api, channel_folder_id):
    """Count files in a Drive folder."""
    try:
        r = api.service.files().list(
            q=f"'{channel_folder_id}' in parents and trashed=false",
            fields='files(id)', pageSize=200
        ).execute()
        return len(r.get('files', []))
    except Exception:
        return 0


def get_or_create_channel_folder(api, channel_name):
    """Find or create channel subfolder under Flamingo."""
    try:
        # Search for existing folder
        q = f"'{FLAMINGO_FOLDER}' in parents and name='{channel_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        r = api.service.files().list(q=q, fields='files(id)').execute()
        files = r.get('files', [])
        if files:
            return files[0]['id']
        # Create it
        meta = {
            'name': channel_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [FLAMINGO_FOLDER]
        }
        f = api.service.files().create(body=meta, fields='id').execute()
        return f['id']
    except Exception as e:
        print(f"[{channel_name}] Folder error: {e}")
        return None


def worker(channel):
    """Worker process: download until channel hits TARGET_MIN."""
    name = channel['name']
    url  = channel['url']
    prefix = f"[{name}]"

    print(f"{prefix} Starting worker")

    # Each worker gets its own Drive API instance (OAuth)
    try:
        api = GoogleDriveAPI(service_account_file='__disabled__')
    except Exception as e:
        print(f"{prefix} Drive init failed: {e}")
        return

    folder_id = get_or_create_channel_folder(api, f"@{name}")
    if not folder_id:
        print(f"{prefix} Could not get/create folder — aborting")
        return

    downloader = SimplifiedDownloader(drive_api=api, base_folder_id=FLAMINGO_FOLDER)

    session_new = 0
    round_num   = 0

    while True:
        in_drive = count_in_drive(api, folder_id)
        total    = in_drive + session_new  # rough total (drive count is source of truth)
        in_drive_actual = in_drive

        print(f"{prefix} Round {round_num+1} — {in_drive_actual} in Drive, need {max(0, TARGET_MIN - in_drive_actual)} more")

        if in_drive_actual >= TARGET_MIN:
            print(f"{prefix} ✅ Done! {in_drive_actual} videos in Drive.")
            return

        round_num += 1
        target_this_round = min(50, TARGET_MAX - in_drive_actual)

        # Extract videos
        videos = extract_standard(url, max_videos=None)
        if not videos:
            videos = extract_browser(url, max_videos=None)
        if not videos:
            print(f"{prefix} ❌ No videos found — retrying in 60s")
            time.sleep(60)
            continue

        print(f"{prefix} {len(videos)} videos available — downloading up to {target_this_round} new")

        new_this_round = 0
        for i, video_url in enumerate(videos, 1):
            if new_this_round >= target_this_round:
                break

            success, msg = downloader.download(video_url)
            is_dup = success and any(k in msg for k in ('Already in history', 'Already in Drive', 'Skipping'))

            if is_dup:
                pass  # silent skip
            elif success:
                new_this_round += 1
                session_new    += 1
                print(f"{prefix} ✅ #{new_this_round} uploaded [{i}/{len(videos)}]")
            else:
                if 'rate-limit' in msg.lower() or 'not available' in msg.lower():
                    print(f"{prefix} ⏳ Rate limited on video {i} — sleeping 30s")
                    time.sleep(30)
                # else silent fail

        print(f"{prefix} Round {round_num} done — {new_this_round} new. Checking Drive...")
        time.sleep(random.randint(10, 20))


def print_drive_summary():
    """Print current Drive counts for all channels."""
    try:
        api = GoogleDriveAPI(service_account_file='__disabled__')
        print("\n📊 Drive summary:")
        total = 0
        for ch in CHANNELS:
            folder_name = f"@{ch['name']}"
            q = f"'{FLAMINGO_FOLDER}' in parents and name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            r = api.service.files().list(q=q, fields='files(id)').execute()
            folders = r.get('files', [])
            if folders:
                cnt = len(api.service.files().list(
                    q=f"'{folders[0]['id']}' in parents and trashed=false",
                    fields='files(id)', pageSize=200
                ).execute().get('files', []))
            else:
                cnt = 0
            total += cnt
            status = '✅' if cnt >= TARGET_MIN else '⏳'
            bar = '█' * (cnt // 5)
            print(f"  {status} {ch['name']:32s}: {cnt:3d}/75  {bar}")
        print(f"  ── Total: {total}\n")
    except Exception as e:
        print(f"  (summary error: {e})")


def main():
    print("=" * 70)
    print("🎌 MANHWA FLAMINGO — PARALLEL DOWNLOADER")
    print(f"   Channels: {len(CHANNELS)} running simultaneously")
    print(f"   Target:   {TARGET_MIN}–{TARGET_MAX} per channel")
    print(f"   Folder:   {FLAMINGO_FOLDER}")
    print("=" * 70)

    print_drive_summary()

    # Launch one process per channel
    processes = []
    for ch in CHANNELS:
        p = multiprocessing.Process(target=worker, args=(ch,), name=ch['name'])
        p.start()
        processes.append((ch['name'], p))
        print(f"▶️  Launched worker for {ch['name']} (PID {p.pid})")
        time.sleep(2)  # stagger starts slightly

    print(f"\n⚡ All {len(processes)} workers running in parallel\n")

    # Monitor until all done
    while True:
        time.sleep(120)
        alive = [(name, p) for name, p in processes if p.is_alive()]
        done  = [(name, p) for name, p in processes if not p.is_alive()]

        print(f"\n⏱  {time.strftime('%H:%M:%S')} — {len(alive)} running, {len(done)} finished")
        print_drive_summary()

        if not alive:
            break

    print("\n🏁 ALL WORKERS DONE")
    print_drive_summary()


if __name__ == '__main__':
    multiprocessing.set_start_method('spawn', force=True)
    main()
