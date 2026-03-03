#!/usr/bin/env bash
# secure.sh — Tighten permissions on all sensitive local files.
# Run this after any git clone / fresh checkout.

set -euo pipefail

FILES=(
    service_account.json
    credentials.json
    token.pickle
    youtube_token.pickle
    omnistream_history.db
    cookies.txt
    tiktok_cookies.txt
    x_cookies.txt
    Instagramcookies.txt
)

for f in "${FILES[@]}"; do
    if [ -f "$f" ]; then
        chmod 600 "$f"
        echo "chmod 600 $f"
    fi
done

echo "Done. All credential files locked to owner-only."
