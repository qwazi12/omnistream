# OmniStream Setup Guide

## Quick Setup

### 1. Install Setup Dependencies

```bash
pip install -r requirements_setup.txt
```

### 2. Run Setup Validator

```bash
python setup_validator.py
```

This will check:
- ✅ Google Drive for Desktop connection
- ✅ cookies.txt existence and validity
- ✅ JDownloader 2 installation and status

## Interactive Setup

For guided setup of missing components:

```bash
python setup_validator.py --setup
```

This will:
- Guide you through installing Google Drive for Desktop
- Help you create cookies.txt using browser extensions or yt-dlp
- Assist with JDownloader installation and configuration

## Component Setup Details

### Google Drive for Desktop

**Why needed:** Direct-to-cloud streaming without local storage waste

**Installation:**
1. Download from: https://www.google.com/drive/download/
2. Install and sign in with your Google account
3. Wait for initial sync to complete
4. Run validator again to confirm detection

**Target Folder:**
The validator will check for access to folder ID: `1DQDRFQtl7fkgyXoP-sqRENau2WCLJH18`

### cookies.txt Setup

**Why needed:** Download age-restricted, private, or premium content

**Method 1: Browser Extension (Recommended)**

**Chrome:**
1. Install: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
2. Visit youtube.com and login
3. Click extension icon → Export
4. Save as `cookies.txt` in OmniStream folder

**Firefox:**
1. Install: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)
2. Visit youtube.com and login
3. Click extension icon → Export
4. Save as `cookies.txt` in OmniStream folder

**Method 2: yt-dlp Auto-Extract**

```bash
yt-dlp --cookies-from-browser chrome --cookies cookies.txt "https://www.youtube.com/"
```

**Validation:**
The validator will:
- Check Netscape format compliance
- Test authentication with a sample YouTube video
- List covered domains

### JDownloader 2 Setup

**Why needed:** Download from file hosting services (Mega, MediaFire, etc.)

**Installation:**

**Windows/macOS/Linux:**
1. Download from: https://jdownloader.org/download/index
2. Install and launch JDownloader
3. Complete initial setup wizard

**MyJDownloader API Configuration:**
1. Create account at: https://my.jdownloader.org/
2. In JDownloader: Settings → MyJDownloader
3. Enter your MyJDownloader credentials
4. Click "Connect"
5. Wait for "Connected" status

**Verification:**
```bash
python setup_validator.py --configure-jd
```

## Command-Line Options

### Basic Validation
```bash
python setup_validator.py
```
Checks all components and displays status report.

### Interactive Setup
```bash
python setup_validator.py --setup
```
Guided setup for missing components.

### Test All Components
```bash
python setup_validator.py --test-all
```
Runs validation and saves detailed JSON report.

### Export JSON Report
```bash
python setup_validator.py --json-output setup_status.json
```
Saves validation results to specified JSON file.

### Configure JDownloader
```bash
python setup_validator.py --configure-jd
```
Shows JDownloader API configuration instructions.

## Folder Structure

When Google Drive is detected, the validator creates:

```
OmniStream_Downloads/
├── YouTube/
│   ├── Channels/
│   ├── Playlists/
│   └── Shorts/
├── TikTok/
│   ├── Users/
│   ├── Hashtags/
│   └── Sounds/
├── Instagram/
│   ├── Posts/
│   ├── Stories/
│   └── Reels/
├── Twitter/
│   ├── Videos/
│   └── Images/
├── FileHosts/
│   ├── Mega/
│   ├── MediaFire/
│   ├── RapidGator/
│   └── Other/
├── Generic_Sites/
└── Playwright_Downloads/
```

## Troubleshooting

### Google Drive Not Detected

**Symptoms:**
- Validator shows "Google Drive not detected"
- Using fallback to ~/Downloads/OmniStream_Local

**Solutions:**
1. Verify Google Drive for Desktop is installed
2. Check that Drive is fully synced (not paused)
3. Ensure Drive is mounted at expected path
4. Try restarting Google Drive application

**Manual Path Check:**
- Windows: Check `G:/My Drive/` or `H:/My Drive/`
- macOS: Check `/Volumes/GoogleDrive/My Drive/`
- Linux: Check `~/Google Drive/`

### cookies.txt Not Working

**Symptoms:**
- Validator finds cookies.txt but test fails
- Downloads fail with authentication errors

**Solutions:**
1. Re-export cookies (they may have expired)
2. Ensure you're logged into the sites you want to download from
3. Check file format is Netscape (should start with `# Netscape HTTP Cookie File`)
4. Try the yt-dlp auto-extract method

### JDownloader Not Detected

**Symptoms:**
- Validator shows "JDownloader 2 not detected"

**Solutions:**
1. Verify JDownloader is installed in standard location
2. Check installation path matches validator search paths
3. Try running JDownloader to ensure it's properly installed
4. On Linux, ensure JDownloader.jar has execute permissions

### JDownloader API Not Connecting

**Symptoms:**
- JDownloader installed but API shows "Not configured"

**Solutions:**
1. Create MyJDownloader account if you haven't
2. In JDownloader: Settings → MyJDownloader → Connect
3. Verify credentials are correct
4. Check internet connection
5. Wait a few minutes for connection to establish

## Status Report Example

```
============================================================
          OmniStream Setup Validator v1.0
============================================================

[1/3] 🔍 Checking Google Drive Connection...
    ✅ Google Drive Detected: G:/My Drive/
    ✅ Write Permission: Verified
    ✅ Folder Structure: Created
    📋 Download Path: G:/My Drive/OmniStream_Downloads/
    📋 Target Folder ID: 1DQDRFQtl7fkgyXoP-sqRENau2WCLJH18
    ⚠️  Note: Unable to verify specific folder (API credentials needed)

[2/3] 🍪 Checking cookies.txt...
    ✅ Found: ./cookies.txt
    ✅ Format: Valid (Netscape)
    ✅ Test: Authenticated downloads working
    📋 Sites covered: youtube.com, tiktok.com, instagram.com

[3/3] 📦 Checking JDownloader 2...
    ✅ Installed: C:/Program Files/JDownloader/JDownloader2.exe
    ✅ Running: Yes
    ⚠️  API Connection: Not configured
    
    📋 Setup Required:
        1. Create MyJDownloader account: https://my.jdownloader.org/
        2. Link your device in JDownloader Settings → MyJDownloader
        3. Run: python setup_validator.py --configure-jd

============================================================
                    SETUP SUMMARY
============================================================

Status: ⚠️ PARTIALLY READY (2/3 components configured)

✅ Google Drive: READY
✅ Cookies: READY
⚠️  JDownloader: NEEDS_CONFIG

Next Steps:
3. Configure JDownloader API
   Run: python setup_validator.py --configure-jd

4. Start OmniStream: python main.py

============================================================
```

## Next Steps

Once all components show ✅ READY:

1. **Launch OmniStream:**
   ```bash
   ./run.sh
   ```

2. **Start downloading:**
   - Paste URLs in the input box
   - Select quality and mode
   - Click "START DOWNLOAD"
   - Monitor progress in real-time

3. **Find your downloads:**
   - Google Drive: `OmniStream_Downloads/[Platform]/`
   - Local: `~/Downloads/OmniStream_Local/[Platform]/`

## Support

For issues or questions:
1. Check this setup guide
2. Review the main README.md
3. Run validator with `--test-all` for detailed diagnostics
4. Check the generated `setup_status.json` for technical details
