# OmniStream - Complete Setup Guide

## Quick Setup with gcloud CLI (2 Minutes!)

### 1. Install gcloud CLI
```bash
brew install google-cloud-sdk
```

### 2. Run Automated Setup
```bash
cd /Users/kwasiyeboah/m3/omnistream
./setup_gcloud.sh
```

This script will:
- ✅ Authenticate with Google Cloud
- ✅ Set project to `manhwa-engine`
- ✅ Enable all required APIs (YouTube, Sheets, Drive, Gemini)
- ✅ Create service account `omnistream-bot`
- ✅ Generate `service_account.json`
- ✅ Save Gemini API key to environment

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 4. Create Content Calendar Sheet
```bash
python3 sheets_manager.py --setup
```

### 5. Test Everything
```bash
python3 post_manager.py --test
```

---

## Manual Setup (If Needed)

### YouTube OAuth
1. Go to https://console.cloud.google.com/apis/credentials
2. Create OAuth 2.0 Client ID → Desktop app
3. Download as `youtube_credentials.json`
4. Test: `python3 youtube_poster.py`

### Facebook Page Access
```bash
python3 facebook_poster.py --setup
```

### Gemini API Key
1. Get key: https://aistudio.google.com/app/apikey
2. Add to shell:
   ```bash
   echo 'export GEMINI_API_KEY="your-key-here"' >> ~/.zshrc
   source ~/.zshrc
   ```

---

## Usage

### One-Time Posting
```bash
python3 post_manager.py --run
```

### Continuous Monitoring (Coming Soon)
```bash
python3 post_scheduler.py --daemon
```

---

## Models Available

**Metadata Generation** (metadata_generator.py):
- **Current**: `gemini-2.5-flash` - Best balance of speed/quality
- Upgrade options:
  - `gemini-3-flash-preview` - Latest, fastest
  - `gemini-2.5-pro` - Highest quality thinking

**Image Generation** (if needed):
- `gemini-2.5-flash-image` - Generate video thumbnails

---

## Troubleshooting

**"gcloud not found"**
```bash
brew install google-cloud-sdk
```

**"Permission denied: ./setup_gcloud.sh"**
```bash
chmod +x setup_gcloud.sh
```

**"No API key"**
```bash
export GEMINI_API_KEY="your-key"
```

---

## File Checklist

After setup, you should have:
- ✅ `service_account.json` (Sheets/Drive access)
- ✅ `youtube_credentials.json` (YouTube upload)
- ✅ `facebook_config.json` (Facebook Page, optional)
- ✅ `sheets_config.json` (Google Sheet URL)
- ✅ `GEMINI_API_KEY` environment variable

Ready to auto-post! 🚀
