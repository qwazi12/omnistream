# OmniStream Content Calendar - Google Sheets Template

## Create Your Sheet Manually

Since Drive storage is limited, create the Sheet yourself:

### 1. Create New Google Sheet
Go to: https://sheets.google.com/create

### 2. Name it
`OmniStream Content Calendar`

### 3. Add these column headers in Row 1:

| A | B | C | D | E | F | G | H | I | J | K | L | M |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ID | Video Name | Drive Link | Title | Description | Tags | Platforms | Status | Scheduled Time | YouTube URL | Facebook URL | Monetized | Notes |

### 4. Format header row (optional but recommended):
- Bold text
- Background color (any color you like)
- Freeze row 1 (View → Freeze → 1 row)

### 5. Share with service account
Click "Share" button and add:
```
omnistream-bot@manhwa-engine.iam.gserviceaccount.com
```
Give it **Editor** access.

### 6. Add example row (Row 2):

| ID | Video Name | Drive Link | Title | Description | Tags | Platforms | Status | Scheduled Time | YouTube URL | Facebook URL | Monetized | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | example.mp4 | https://drive.google.com/file/d/YOUR_FILE_ID | Example Video Title | This is an example description | #viral,#trending | YouTube,Facebook | Idle | 2025-01-01 10:00 | | | Yes | Test video |

### 7. Get the Sheet URL
Copy the full URL from your browser (looks like):
```
https://docs.google.com/spreadsheets/d/SHEET_ID/edit
```

### 8. Configure OmniStream
Run this command and paste your Sheet URL:
```bash
python3 -c "
from sheets_manager import SheetsManager
import json

url = input('Paste your Google Sheet URL: ')
with open('sheets_config.json', 'w') as f:
    json.dump({'sheet_url': url}, f)
print('✅ Sheet configured!')
"
```

---

## Status Values

Use these exact values in the "Status" column:

- **Idle** - Video ready, waiting to be scheduled
- **Scheduled** - Will auto-post at the scheduled time
- **Processing** - Currently uploading
- **Posted** - Successfully uploaded
- **Failed** - Upload failed (check Notes column)

---

## Platform Values

In "Platforms" column, use:
- `YouTube` - Post to YouTube only
- `Facebook` - Post to Facebook only  
- `YouTube,Facebook` - Post to both

---

## Monetized Values

In "Monetized" column (YouTube only):
- `Yes` - Enable monetization
- `No` - Disable monetization

---

## Quick Start

Once sheet is setup:
```bash
# Test connection
python3 post_manager.py --test

# Process all scheduled videos
python3 post_manager.py --run
```
