#!/usr/bin/env python3
"""
OmniStream Unified Batch Runner

Replaces: run_master_plan.py, run_session.py

Usage:
    python run.py <batch_or_session> [--limit N]

Single batch (folder key must match channels.json key or be passed via --folder):
    python run.py movie_clips
    python run.py flamingo
    python run.py second_track_clips

Multi-batch session (runs batches in sequence with rests between them):
    python run.py master    → movie_clips then flamingo
    python run.py session   → second_track_clips then flamingo

All channel lists and folder IDs are read from channels.json / config.json.
"""

import sys
import time
import random
import subprocess
import argparse
from config_loader import get_folder_id, get_channels

# Predefined multi-batch sessions
SESSIONS = {
    'master':  ['movie_clips', 'flamingo'],
    'session': ['second_track_clips', 'flamingo'],
}

DEFAULT_LIMIT = 50


def run_download(url: str, limit: int, folder_id: str):
    cmd = [sys.executable, 'smart_batch.py', url, str(limit), folder_id]
    subprocess.run(cmd)


def random_rest(min_s: int = 120, max_s: int = 300):
    secs = random.randint(min_s, max_s)
    print(f"\n💤 Resting {secs}s ({secs // 60}m {secs % 60}s)...")
    time.sleep(secs)
    print("🔔 Resuming...")


def run_batch(batch_name: str, limit: int):
    channels = get_channels(batch_name)
    folder_id = get_folder_id(batch_name)
    print(f"\n{'='*70}")
    print(f"🎬 BATCH: {batch_name.upper()}  ({len(channels)} channels, limit={limit})")
    print(f"   Folder: {folder_id}")
    print(f"{'='*70}")

    for i, entry in enumerate(channels):
        url = entry['url'] if isinstance(entry, dict) else entry
        name = entry.get('name', url) if isinstance(entry, dict) else url
        print(f"\n  [{i+1}/{len(channels)}] {name}")
        run_download(url, limit, folder_id)

        if i < len(channels) - 1:
            random_rest(60, 180)

    print(f"\n✅ Batch '{batch_name}' complete.")


def main():
    parser = argparse.ArgumentParser(description='OmniStream batch runner')
    parser.add_argument('target', help='Batch name (e.g. movie_clips) or session (master, session)')
    parser.add_argument('--limit', type=int, default=DEFAULT_LIMIT, help='Max videos per channel')
    args = parser.parse_args()

    targets = SESSIONS.get(args.target, [args.target])

    print(f"=== OmniStream Run: {args.target.upper()} ===")
    print(f"Batches: {targets}  |  Limit: {args.limit}/channel")

    for i, batch in enumerate(targets):
        run_batch(batch, args.limit)
        if i < len(targets) - 1:
            print(f"\n⏸️  Inter-batch rest before '{targets[i+1]}'...")
            random_rest(600, 900)

    print("\n✅ ALL DONE.")


if __name__ == '__main__':
    main()
