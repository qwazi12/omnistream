import os
import time
import tempfile
import requests
from playwright.sync_api import sync_playwright
from drive_api import GoogleDriveAPI


def download_snaptik_direct(video_url, drive_api=None):
    print(f"🚀 Using Snaptik bypass for: {video_url}")

    # Write to a temp file so we never pollute CWD.
    fd, tmp_path = tempfile.mkstemp(suffix=".mp4", prefix="omnistream_snaptik_")
    os.close(fd)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.goto("https://snaptik.app/en2")

                page.fill('input[name="url"]', video_url)
                page.click('button[type="submit"]')

                # Wait for processing.
                try:
                    page.wait_for_selector('.download-file', timeout=15000)
                except Exception:
                    print("❌ Snaptik analysis timed out")
                    return False

                download_btn = page.query_selector('.download-file')
                if not download_btn:
                    print("❌ Could not find download button")
                    return False

                actual_url = download_btn.get_attribute('href')

            finally:
                browser.close()

        # Download into the temp path (never into CWD).
        print("📥 Downloading video file...")
        with requests.get(actual_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(tmp_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        print(f"✓ Saved to temp: {tmp_path}")

        # Upload to Drive.
        from config_loader import get_folder_id
        folder_id = get_folder_id('movie_clips', '1kuOKRQQRL0ws5aOVqwkdUzdnfj5KQGjo')
        display_name = f"tiktok_{int(time.time())}.mp4"

        if drive_api:
            print("📤 Uploading via provided Drive API...")
            drive_api.upload_file(file_path=tmp_path, folder_id=folder_id, filename=display_name)
        else:
            print("📤 Uploading via new Drive instance...")
            drive = GoogleDriveAPI()
            drive.upload_file(file_path=tmp_path, folder_id=folder_id, filename=display_name)

        print("✅ Upload Complete!")
        return True

    except Exception as e:
        print(f"❌ Snaptik Failed: {e}")
        return False

    finally:
        # Always clean up the temp file, regardless of success or failure.
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
