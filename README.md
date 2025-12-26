# OmniStream Archiver

Universal desktop downloader with triple-engine architecture that streams content directly to Google Drive.

## Features

- **Triple Engine System:**
  - yt-dlp for video platforms (YouTube, TikTok, Instagram, etc.)
  - JDownloader for file hosting services (Mega, MediaFire, etc.)
  - Playwright for ANY unknown website

- **Smart Download Modes:**
  - Auto-Detect (intelligent routing)
  - Force Video (standard quality selection)
  - Force Audio (MP3 extraction)
  - **Shorts Only** (filters for YouTube Shorts and vertical videos)
  - Bulk Channel (download entire channels/playlists)

- **Direct Google Drive Streaming:** No local storage waste
- **Smart Organization:** Auto-organized folder structures
- **Real-time Monitoring:** Live progress bars and console logs
- **Anti-Detection:** Stealth mode with delays and user-agent rotation

## Quick Start

**Easiest way to run:**
```bash
./run.sh
```

The startup script will automatically:
- Create a virtual environment if needed
- Install all dependencies
- Launch the application

## Installation

### 1. Prerequisites
- Python 3.10 or higher
- **tkinter** (required for GUI)
  - macOS: `brew install python-tk@3.13` (or your Python version)
  - Ubuntu/Debian: `sudo apt-get install python3-tk`
  - Windows: Usually included with Python
- Google Drive for Desktop installed and running (optional but recommended)
- JDownloader 2 installed (optional but recommended)

### 2. Manual Setup (if not using run.sh)
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium
```

### 3. JDownloader Setup (Optional)
1. Download from: https://jdownloader.org/download/index
2. Install and run JDownloader
3. Go to Settings > Advanced Settings
4. Search for "myjdownloader"
5. Enable MyJDownloader remote API

### 4. Cookie Setup (Optional)
For authenticated downloads (age-restricted videos, private content):
- Export cookies from your browser using extension
- Save as `cookies.txt` in project root

## Usage

1. Launch the application:
   ```bash
   ./run.sh
   ```
   
   Or manually:
   ```bash
   source venv/bin/activate
   python main.py
   ```

2. The app will auto-detect your Google Drive

3. Paste URLs (one per line for bulk downloads)

4. Select mode and quality preferences

5. Click "START DOWNLOAD"

6. Files automatically appear in Google Drive or local Downloads folder

## Supported Sites

### Via yt-dlp (1000+ sites):
- YouTube, TikTok, Instagram, Twitter/X, Facebook
- Vimeo, Twitch, Reddit, Dailymotion
- And many more...

### Via JDownloader:
- Mega, MediaFire, RapidGator, 1fichier
- File hosting services with CAPTCHA

### Via Playwright:
- Literally ANY website with downloadable content

## Folder Structure

```
Google Drive/OmniStream_Downloads/
├── YouTube/
│   └── [Channel]/[Year-Month]/
├── TikTok/
│   └── [@Creator]/[Year-Month]/
├── FileHosts/
│   └── [Service]/[Year-Month]/
└── Generic_Sites/
    └── [Domain]/[Year-Month]/
```

## Troubleshooting

**JDownloader not detected:**
- Make sure JDownloader is running
- Check that MyJDownloader API is enabled in settings

**Google Drive not detected:**
- Verify Google Drive for Desktop is installed
- Check that drive is mounted at expected path
- App will fallback to local Downloads folder

**Download fails:**
- Check console log for detailed error messages
- Try different engine (use Engine dropdown)
- Ensure cookies.txt is present for authenticated content

## License

Personal use only. Respect copyright and terms of service.
