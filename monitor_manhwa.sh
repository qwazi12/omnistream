#!/bin/bash
# Active monitor for run_manhwa.py
# Watches progress, detects stalls, auto-restarts on failure

LOG=/private/tmp/manhwa_run.log
STALL_LIMIT=600   # seconds with no new output = stall (10 min)
CHECK_INTERVAL=60 # check every 60s

echo "🔍 MANHWA MONITOR STARTED — $(date)"
echo "   Log: $LOG"
echo "   Stall threshold: ${STALL_LIMIT}s"
echo ""

run_downloader() {
    echo "▶️  Starting run_manhwa.py — $(date)" | tee -a "$LOG"
    python /Users/kwasiyeboah/m3/omnistream/run_manhwa.py 2>&1 | tee -a "$LOG"
    EXIT=$?
    echo "⏹️  run_manhwa.py exited with code $EXIT — $(date)" | tee -a "$LOG"
    return $EXIT
}

while true; do
    # Start the downloader in background
    run_downloader &
    PID=$!
    echo "   PID: $PID"

    # Watch it
    LAST_SIZE=0
    STALL_SECS=0

    while kill -0 $PID 2>/dev/null; do
        sleep $CHECK_INTERVAL
        CURRENT_SIZE=$(wc -c < "$LOG" 2>/dev/null || echo 0)

        # Progress summary
        SUCCESSES=$(grep -c "✅ New video" "$LOG" 2>/dev/null || echo 0)
        ERRORS=$(grep -c "rate-limited\|ERROR\|❌" "$LOG" 2>/dev/null || echo 0)
        LAST_LINE=$(tail -1 "$LOG" 2>/dev/null)

        echo "--- $(date '+%H:%M:%S') | ✅ $SUCCESSES new | ❌ $ERRORS errors | Last: ${LAST_LINE:0:80}"

        if [ "$CURRENT_SIZE" -eq "$LAST_SIZE" ]; then
            STALL_SECS=$((STALL_SECS + CHECK_INTERVAL))
            echo "    ⚠️  No output for ${STALL_SECS}s..."
            if [ "$STALL_SECS" -ge "$STALL_LIMIT" ]; then
                echo "    🔴 STALL DETECTED — killing and restarting..."
                kill $PID 2>/dev/null
                break
            fi
        else
            STALL_SECS=0
        fi
        LAST_SIZE=$CURRENT_SIZE
    done

    # Check if it finished cleanly
    wait $PID
    EXIT=$?

    if [ $EXIT -eq 0 ]; then
        echo ""
        echo "✅ ALL DONE — $(date)"
        echo "   Total new videos: $(grep -c '✅ New video' "$LOG")"
        break
    else
        echo "🔁 Process ended (exit $EXIT) — checking if more work needed..."
        # Check DB counts
        python3 -c "
import sqlite3, json
conn = sqlite3.connect('/Users/kwasiyeboah/m3/omnistream/omnistream_history.db')
channels = ['Korasama-v','TRUEMANHUA','5th_Dimension_Manhwa','manhwaclash','manhwaaddict13']
all_done = True
for ch in channels:
    count = conn.execute('SELECT COUNT(*) FROM download_history WHERE channel_name LIKE ?', (f'%{ch}%',)).fetchone()[0]
    status = '✅' if count >= 75 else '⏳'
    print(f'  {status} {ch}: {count}/75')
    if count < 75:
        all_done = False
conn.close()
if all_done:
    print('ALL_DONE')
" 2>/dev/null

        DONE=$(python3 -c "
import sqlite3
conn = sqlite3.connect('/Users/kwasiyeboah/m3/omnistream/omnistream_history.db')
channels = ['Korasama-v','TRUEMANHUA','5th_Dimension_Manhwa','manhwaclash','manhwaaddict13']
all_done = all(conn.execute('SELECT COUNT(*) FROM download_history WHERE channel_name LIKE ?', (f'%{ch}%',)).fetchone()[0] >= 75 for ch in channels)
conn.close()
print('yes' if all_done else 'no')
" 2>/dev/null)

        if [ "$DONE" = "yes" ]; then
            echo "✅ All channels at 75+ — done!"
            break
        fi

        echo "🔁 Restarting in 30s..."
        sleep 30
    fi
done
