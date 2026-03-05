#!/bin/bash

# OmniStream - Batch TikTok Download Script
# Downloads 50 videos from each specified TikTok account
# Target: Google Drive folder 1-uLwByo0LzAteTyFaTSSOvACcT_liIWJ

FOLDER_ID="1-uLwByo0LzAteTyFaTSSOvACcT_liIWJ"
MAX_VIDEOS=50

echo "=========================================="
echo "OmniStream - Batch TikTok Downloader"
echo "=========================================="
echo "Target Folder: $FOLDER_ID"
echo "Videos per account: $MAX_VIDEOS"
echo ""

# Array of TikTok accounts
ACCOUNTS=(
    "https://www.tiktok.com/@bicboiclips"
    "https://www.tiktok.com/@fruit.jamz"
    "https://www.tiktok.com/@cmbboys"
    "https://www.tiktok.com/@deetheclipplug2.0"
    "https://www.tiktok.com/@crane_editz"
)

ACCOUNT_NAMES=(
    "bicboiclips"
    "fruit.jamz (LeakHub)"
    "cmbboys (CMB)"
    "deetheclipplug2.0"
    "crane_editz"
)

# Download from each account
for i in "${!ACCOUNTS[@]}"; do
    ACCOUNT_URL="${ACCOUNTS[$i]}"
    ACCOUNT_NAME="${ACCOUNT_NAMES[$i]}"
    
    echo ""
    echo "=========================================="
    echo "[$((i+1))/5] Downloading from: $ACCOUNT_NAME"
    echo "URL: $ACCOUNT_URL"
    echo "=========================================="
    echo ""
    
    # Run smart_batch.py with the account URL, max videos, and folder ID
    python3 smart_batch.py "$ACCOUNT_URL" "$MAX_VIDEOS" "$FOLDER_ID"
    
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo "✓ Successfully completed: $ACCOUNT_NAME"
    else
        echo "✗ Failed or partially completed: $ACCOUNT_NAME"
    fi
    
    # Anti-detection: Random delay between accounts (8-15 seconds)
    if [ $i -lt $((${#ACCOUNTS[@]} - 1)) ]; then
        DELAY=$((8 + RANDOM % 8))
        echo ""
        echo "⏳ Waiting ${DELAY}s before next account (anti-detection)..."
        sleep $DELAY
    fi
done

echo ""
echo "=========================================="
echo "Batch Download Complete!"
echo "=========================================="
echo "All videos have been downloaded to Google Drive folder:"
echo "https://drive.google.com/drive/u/0/folders/$FOLDER_ID"
