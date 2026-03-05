# OmniStream Automation System - Full Specification

## 1. What We'd Need

### Backend Components:

#### A. Job Queue System
- **Purpose**: Manage multiple download batches in sequence
- **Tech**: Python `queue` module or Redis for distributed setup
- **Features**:
  - Priority queuing (urgent vs. regular batches)
  - Pause/resume capability
  - Retry failed jobs automatically

#### B. Smart Scheduler
- **Purpose**: Handle pacing and rest periods
- **Features**:
  - Random rest intervals (300-900s) between batches
  - Detect bot flags and auto-pause for cooldown
  - Schedule downloads for off-peak hours

#### C. Configuration Manager
- **Purpose**: Store channel groups and settings
- **File**: `automation_config.json`
- **Structure**:
```json
{
  "folder_groups": {
    "Flamingo": {
      "drive_id": "1Mmrem-JzM1tBArIJ-GrcaDX7qKRhTC5F",
      "channels": [
        {"url": "https://youtube.com/@Havertz02/shorts", "limit": 50},
        {"url": "https://youtube.com/@VynixAE/shorts", "limit": 50}
      ]
    },
    "Second Track Clips": {
      "drive_id": "1_HWppeJLcrGAo--UFc3u-eUTpvE0T0S6",
      "channels": [
        {"url": "https://youtube.com/@BriarrWolf/shorts", "limit": 50}
      ]
    }
  },
  "settings": {
    "rest_min": 300,
    "rest_max": 900,
    "max_parallel": 3,
    "auto_refresh_cookies": true
  }
}
```

#### D. Progress Tracker
- **Purpose**: Real-time status updates
- **Tech**: SQLite database + WebSocket for live updates
- **Tracks**:
  - Current batch progress (23/50 videos)
  - Overall session stats (150/300 total)
  - Speed (MB/s), ETA, success rate

#### E. Cookie Auto-Refresh
- **Purpose**: Prevent "Sign in" errors
- **Method**: 
  - Monitor for auth failures
  - Alert user when cookies need refresh
  - Optional: Browser automation to auto-extract cookies

#### F. Error Recovery System
- **Purpose**: Handle failures gracefully
- **Features**:
  - Detect "bot" errors → trigger extended rest
  - Network failures → auto-retry with exponential backoff
  - Drive quota exceeded → pause and notify

---

## 2. Workflow Design

### Phase 1: Setup (One-Time)
1. User adds channel groups via UI
2. Assigns each group to a Drive folder
3. Sets limits (50 per channel, max 3 parallel, etc.)
4. System validates cookies and Drive access

### Phase 2: Planning (Automatic)
1. System scans all configured channels
2. Checks Drive for existing videos (deduplication)
3. Creates optimized batch queue:
   - Batch 1: Flamingo (3 channels × 50)
   - Rest: 5-15 mins
   - Batch 2: Second Track (3 channels × 50)
   - Rest: 5-15 mins
   - Batch 3: Movie Clips (4 channels × 50)

### Phase 3: Execution (Automatic)
1. **Rest Period**: Random delay before starting
2. **Download**: Process batch (parallel or sequential)
3. **Monitor**: Track progress, detect errors
4. **Adapt**: If bot detected → extend rest period
5. **Loop**: Move to next batch after rest

### Phase 4: Completion
1. Generate summary report
2. Send notification (email/Slack/Discord)
3. Update analytics dashboard
4. Schedule next run (optional recurring mode)

---

## 3. User Interface Layout

### Main Dashboard (Home Page)

```
┌─────────────────────────────────────────────────────────────────┐
│  🎬 OmniStream Automation                    🟢 Active  👤 User │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📊 Session Overview                         [⚙️ Settings] [⏸️ Pause]│
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Current Batch: Second Track Clips (Batch 2/5)           │  │
│  │  Progress: ████████████░░░░░░░░░░░░░░░░░░░░░ 48/150     │  │
│  │  Status: Downloading @BriarrWolf (23/50)                 │  │
│  │  Speed: 12.3 MB/s  |  ETA: 8m 34s  |  Success: 98.2%     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  🗂️ Folder Groups                                               │
│  ┌───────────────────┬────────────┬─────────┬──────────────┐   │
│  │ Flamingo          │ 150/150 ✅ │ 12.3 GB │ [View Files] │   │
│  │ Second Track Clips│  48/150 🔄 │  4.8 GB │ [View Files] │   │
│  │ Movie Clips       │   0/200 ⏳ │  0.0 GB │ [View Files] │   │
│  └───────────────────┴────────────┴─────────┴──────────────┘   │
│                                                                  │
│  📋 Active Downloads (3)                      [Expand All ▼]    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 🎥 @BriarrWolf                                 23/50 (46%)│  │
│  │    └─ "Epic Fight Scene"  ████████░░░░░░░░  8.2/15.4 MB  │  │
│  │ 🎥 @CJ-112-w9r                                 19/50 (38%)│  │
│  │    └─ "Comedy Skit #23"   ██████░░░░░░░░░░  5.1/12.8 MB  │  │
│  │ 🎥 @LebohangSwiggs                             21/50 (42%)│  │
│  │    └─ "Dance Moves"       ███████░░░░░░░░░  6.4/11.2 MB  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ⏰ Next: Rest Period (7m 12s) → Batch 3: Movie Clips           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Channel Manager Page

```
┌─────────────────────────────────────────────────────────────────┐
│  📺 Channel Manager                          [+ Add Channel]     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  🗂️ Flamingo (Drive ID: 1Mmrem-JzM1tBArIJ...)                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ @Havertz02/shorts           │ 50 limit │ 50✅│ [Edit] [❌] │    │
│  │ @VynixAE/shorts             │ 50 limit │ 50✅│ [Edit] [❌] │    │
│  │ @TonyPino666/shorts         │ 50 limit │ 50✅│ [Edit] [❌] │    │
│  │ @FrysFuturisticShorts       │ 50 limit │ 23🔄│ [Edit] [❌] │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  🗂️ Second Track Clips (Drive ID: 1_HWppeJLcrGAo...)           │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ @BriarrWolf/shorts          │ 50 limit │ 23🔄│ [Edit] [❌] │    │
│  │ @CJ-112-w9r/shorts          │ 50 limit │ 19🔄│ [Edit] [❌] │    │
│  │ @LebohangSwiggs/shorts      │ 50 limit │ 21🔄│ [Edit] [❌] │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  [+ Add New Folder Group]                                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Settings Page

```
┌─────────────────────────────────────────────────────────────────┐
│  ⚙️ Settings                                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  🔐 Authentication                                               │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Cookies Status: ✅ Valid (expires in 14 days)          │    │
│  │ [Refresh Cookies] [Upload New cookies.txt]             │    │
│  │                                                         │    │
│  │ Drive OAuth: ✅ Connected (kwasi@example.com)          │    │
│  │ [Re-authenticate] [Switch Account]                     │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ⏱️ Download Behavior                                           │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Rest Period: [300] - [900] seconds (5-15 mins)         │    │
│  │ Max Parallel Downloads: [3] channels at once           │    │
│  │ Default Video Limit: [50] per channel                  │    │
│  │ ☑ Auto-skip duplicates                                 │    │
│  │ ☑ Shorts only (vertical videos)                        │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  🛡️ Bot Protection                                              │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Detection Response: [Extended Rest (15-30 mins)] ▼     │    │
│  │ Max Retries: [3]                                        │    │
│  │ ☑ Auto-pause on repeated failures                      │    │
│  │ ☑ Notify me on detection events                        │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  [Save Changes] [Reset to Defaults]                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Analytics Page

```
┌─────────────────────────────────────────────────────────────────┐
│  📊 Analytics                                [Last 30 Days ▼]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📈 Download Statistics                                          │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐     │
│  │ Total Videos│   Storage   │ Success Rate│  Avg Speed  │     │
│  │     847     │   68.2 GB   │    98.4%    │  11.2 MB/s  │     │
│  └─────────────┴─────────────┴─────────────┴─────────────┘     │
│                                                                  │
│  📊 Downloads Over Time                                          │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ 100│            ▄▄▄                                     │    │
│  │ 80 │        ▄▄▄█████▄                                  │    │
│  │ 60 │    ▄▄▄████████████                                │    │
│  │ 40 │▄▄▄██████████████████▄                             │    │
│  │ 20 │████████████████████████▄▄                         │    │
│  │  0 └────────────────────────────────────────────       │    │
│  │     Jan 5  Jan 6  Jan 7  Jan 8  Jan 9  Jan 10  Jan 11  │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  🏆 Top Channels (By Videos Downloaded)                         │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ 1. @Havertz02         150 videos  █████████████░░ 18%  │    │
│  │ 2. @VynixAE           150 videos  █████████████░░ 18%  │    │
│  │ 3. @TonyPino666       150 videos  █████████████░░ 18%  │    │
│  │ 4. @JaiceNoir          50 videos  ████░░░░░░░░░░  6%  │    │
│  │ 5. @Hypeflix.official  50 videos  ████░░░░░░░░░░  6%  │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  [Export Report] [View Detailed Analytics]                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Implementation Priority

### Phase 1 (MVP - Week 1):
1. ✅ Core downloader (already have)
2. ⬜ Web UI (Flask/FastAPI backend)
3. ⬜ Channel manager
4. ⬜ Basic queue system

### Phase 2 (Automation - Week 2):
5. ⬜ Smart scheduler with rest periods
6. ⬜ Progress tracking with WebSockets
7. ⬜ Configuration file system

### Phase 3 (Intelligence - Week 3):
8. ⬜ Bot detection & auto-recovery
9. ⬜ Analytics dashboard
10. ⬜ Cookie auto-refresh alerts

### Phase 4 (Polish - Week 4):
11. ⬜ Notifications (email/Slack/Discord)
12. ⬜ Recurring schedules (daily/weekly runs)
13. ⬜ Mobile-responsive UI

---

## 5. Deployment Options

### Option A: Local Desktop App
- **Pros**: Full control, no server costs
- **Cons**: Must keep computer running
- **Tech**: Electron wrapper around web UI

### Option B: Cloud VPS
- **Pros**: 24/7 operation, access from anywhere
- **Cons**: Monthly costs (~$10-20/month)
- **Tech**: DigitalOcean/AWS EC2 + nginx

### Option C: Raspberry Pi
- **Pros**: Low power, always-on, cheap
- **Cons**: Slower downloads, limited storage
- **Tech**: Pi 4 with external SSD

---

## 6. Key Automation Features

### Smart Pacing Algorithm:
```python
def calculate_rest_time(downloads_completed, failures_count):
    base_rest = random.randint(300, 900)  # 5-15 mins
    
    # Increase rest if many failures
    if failures_count > 5:
        base_rest *= 2  # Double rest time
    
    # Decrease rest if smooth sailing
    if failures_count == 0 and downloads_completed > 100:
        base_rest *= 0.7  # Reduce by 30%
    
    return int(base_rest)
```

### Duplicate Prevention:
- Check database before every download
- Cross-reference with Drive folder (by video ID in filename)
- Skip if already exists → mark as "Already Downloaded"

### Failure Recovery:
1. **Retry 3 times** with increasing delays (10s, 30s, 60s)
2. If still fails → **move to "Failed Queue"**
3. At end of batch → **report failed videos for manual review**

---

Would you like me to start building this? I can create a working prototype of the web UI + automation system!
