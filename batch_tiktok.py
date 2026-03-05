#!/usr/bin/env python3
"""
OmniStream - Batch TikTok Downloader
Downloads videos from multiple TikTok accounts using the dedicated TikTok engine
"""

import asyncio
import time
import random
from tiktok_engine import TikTokEngine


# Configuration
FOLDER_ID = "1-uLwByo0LzAteTyFaTSSOvACcT_liIWJ"
MAX_VIDEOS_PER_ACCOUNT = 50

# TikTok accounts to download from
ACCOUNTS = [
    {"username": "@bicboiclips", "name": "bicboiclips (Streamer Clips)"},
    {"username": "@fruit.jamz", "name": "LeakHub (Viral Editor)"},
    {"username": "@cmbboys", "name": "CMB (Official Page)"},
    {"username": "@deetheclipplug2.0", "name": "DeeTheClipPlug (Stream Clips)"},
    {"username": "@crane_editz", "name": "crane_editz (Streamer/Sport Edits)"},
]


async def download_account(engine, account, account_num, total_accounts):
    """Download videos from a single account"""
    username = account["username"]
    name = account["name"]
    
    print("\n" + "="*70)
    print(f"[{account_num}/{total_accounts}] {name}")
    print(f"URL: https://www.tiktok.com/{username}")
    print("="*70)
    
    # Download videos
    successful, failed = await engine.download_user(username, MAX_VIDEOS_PER_ACCOUNT)
    
    # Summary for this account
    total = successful + failed
    success_rate = (successful / total * 100) if total > 0 else 0
    
    print(f"\n✓ Account Complete: {name}")
    print(f"   Downloaded: {successful}/{total} ({success_rate:.1f}% success)")
    
    return successful, failed


async def main():
    """Main batch download function"""
    print("="*70)
    print("OmniStream - Batch TikTok Downloader")
    print("="*70)
    print(f"Target Folder: {FOLDER_ID}")
    print(f"Videos per account: {MAX_VIDEOS_PER_ACCOUNT}")
    print(f"Total accounts: {len(ACCOUNTS)}")
    print("="*70)
    
    # Create engine
    engine = TikTokEngine(folder_id=FOLDER_ID)
    
    # Track overall stats
    total_successful = 0
    total_failed = 0
    account_results = []
    
    # Download from each account
    for i, account in enumerate(ACCOUNTS, 1):
        # Download videos
        successful, failed = await download_account(engine, account, i, len(ACCOUNTS))
        
        # Track results
        total_successful += successful
        total_failed += failed
        account_results.append({
            "name": account["name"],
            "successful": successful,
            "failed": failed,
            "total": successful + failed
        })
        
        # Anti-detection delay between accounts (except after last one)
        if i < len(ACCOUNTS):
            delay = random.randint(8, 15)
            print(f"\n⏳ Waiting {delay}s before next account (anti-detection)...")
            time.sleep(delay)
    
    # Final summary
    print("\n" + "="*70)
    print("📊 BATCH DOWNLOAD COMPLETE")
    print("="*70)
    
    # Per-account breakdown
    print("\n📋 Per-Account Results:")
    for result in account_results:
        success_rate = (result["successful"] / result["total"] * 100) if result["total"] > 0 else 0
        print(f"   {result['name']}")
        print(f"      ✓ {result['successful']}/{result['total']} ({success_rate:.1f}%)")
    
    # Overall stats
    total_videos = total_successful + total_failed
    overall_success_rate = (total_successful / total_videos * 100) if total_videos > 0 else 0
    
    print(f"\n📈 Overall Statistics:")
    print(f"   Total Videos Attempted: {total_videos}")
    print(f"   ✓ Successful: {total_successful}")
    print(f"   ✗ Failed: {total_failed}")
    print(f"   Success Rate: {overall_success_rate:.1f}%")
    
    print(f"\n🔗 All videos saved to:")
    print(f"   https://drive.google.com/drive/u/0/folders/{FOLDER_ID}")
    print("="*70)
    
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
