import os
import time
import tempfile
import requests
from playwright.sync_api import sync_playwright
from drive_api import GoogleDriveAPI


def download_cobalt_direct(video_url, drive_api=None, folder_id=None):
    # Cobalt is currently timing out due to heavy JS/anti-bot.
    # Delegating to 10Downloader which is lighter and more reliable for Shorts.
    return download_10downloader(video_url, drive_api, folder_id)


def download_10downloader(video_url, drive_api, folder_id):
    print(f"🔄 Switching to 10Downloader Bypass...")

    # Write to a temp file so we never pollute CWD.
    fd, tmp_path = tempfile.mkstemp(suffix=".mp4", prefix="omnistream_cobalt_")
    os.close(fd)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page()

                page.goto("https://10downloader.com/en/1")

                # Accept cookie banner if present.
                try:
                    page.click('.fc-cta-consent', timeout=2000)
                except Exception:
                    pass

                page.fill('#input-url', video_url)
                page.click('#btn-convert')

                # Wait for download links.
                page.wait_for_selector('.download-btn', timeout=15000)

                download_btn = page.query_selector('.download-btn')
                if not download_btn:
                    print("❌ No download button found")
                    return False

                actual_url = download_btn.get_attribute('href')

            finally:
                browser.close()

        # Download the file into the temp path (never into CWD).
        print("📥 Downloading video file...")
        with requests.get(actual_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(tmp_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        print(f"✓ Saved to temp: {tmp_path}")

        # Upload to Drive.
        if not folder_id:
            folder_id = '1kuOKRQQRL0ws5aOVqwkdUzdnfj5KQGjo'  # Default: Movie Clips

        print(f"📤 Uploading to Drive ({folder_id})...")
        display_name = f"short_{int(time.time())}.mp4"

        if drive_api:
            drive_api.upload_file(file_path=tmp_path, folder_id=folder_id, filename=display_name)
        else:
            drive = GoogleDriveAPI()
            drive.upload_file(file_path=tmp_path, folder_id=folder_id, filename=display_name)

        print("✅ Upload Complete!")
        return True

    except Exception as e:
        print(f"❌ 10Downloader failed: {e}")
        return False

    finally:
        # Always clean up the temp file, regardless of success or failure.
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
