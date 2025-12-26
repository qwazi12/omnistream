# OmniStream AI-Powered User Guide

## 🚀 Quick Start

### Launch the Application
```bash
cd /Users/kwasiyeboah/m3/omnistream
./run.sh
```

---

## 🤖 Using AI Natural Language Commands

### Simple Examples

**Download a single video:**
```
"Download this video"
"Get this in 1080p"
"Grab the video"
```

**Download with filters:**
```
"All shorts from last week"
"Latest 10 videos"
"Download all MrBeast shorts from December 2024"
```

**Advanced commands:**
```
"Get the playlist but skip videos I already have"
"Latest 50 videos from this channel, audio only"
"All reels from this Instagram account in the last month"
```

### How It Works

1. **Paste URL** in the URL input box
2. **Type command** in AI Command box
3. **Click "🚀 Parse with AI"**
4. **Review interpretation** (confidence score, detected settings)
5. **Click "✓ Accept"** or "✎ Edit Manually"

---

## 🎯 Site-Aware Dynamic Filtering

### Automatic Detection

When you paste a URL, OmniStream automatically detects:
- Platform (YouTube, TikTok, Instagram, etc.)
- Available content types (Shorts, Reels, Stories)
- Supported quality options
- Bulk download capabilities

### Platform-Specific Features

#### YouTube
- **Content Types:** All Videos, Shorts Only, Audio Only
- **Quality:** Best, 4K, 1440p, 1080p, 720p, 480p
- **Bulk:** Channels, Playlists
- **Date Filter:** ✅ Yes

#### TikTok
- **Content Types:** All Videos, Audio Only
- **Quality:** Best Available
- **Bulk:** User profiles
- **Date Filter:** ✅ Yes

#### Instagram
- **Content Types:** All Videos, Reels Only, Stories Only, Audio Only
- **Quality:** Best Available
- **Bulk:** User profiles
- **Date Filter:** ✅ Yes

#### Spotify/SoundCloud
- **Content Types:** Audio Only, Playlists, Albums
- **Quality:** Best Available
- **Bulk:** Playlists, Albums
- **Date Filter:** ❌ No

---

## 📅 Date Range Filtering

### Absolute Dates
```
From: 2024-12-01
To: 2024-12-31
```

### Relative Dates
```
"last week"     → Last 7 days
"last month"    → Last 30 days
"yesterday"     → Yesterday only
"today"         → Today only
"last 5 days"   → Last 5 days
```

---

## ⚙️ Manual Mode

If you prefer manual configuration:

1. Click **"⚙️ Manual Filters"**
2. Filters appear based on detected site
3. Configure:
   - Content Type
   - Date Range
   - Max Downloads
   - Quality

---

## 🔍 AI Interpretation Panel

After parsing, you'll see:

```
🎯 Downloading all Shorts from MrBeast's channel uploaded in December 2024 at 1080p quality

📊 Confidence: 95%
🔗 URL: https://youtube.com/@MrBeast/shorts
📹 Content: Shorts Only
🎨 Quality: 1080p
📅 Date Range: 2024-12-01 to 2024-12-31
```

**Confidence Levels:**
- **90-100%:** Very confident, safe to accept
- **70-89%:** Good, review interpretation
- **Below 70%:** Ambiguous, check carefully

---

## 🛡️ Safety Features

### Automatic Caps
- **Max 500 videos** per download (safety limit)
- **Date range validation** (auto-corrects reversed dates)
- **Duplicate detection** (skips already downloaded)

### Warnings
The AI will warn you about:
- Excessive download counts
- Ambiguous commands
- Missing information
- Potential issues

---

## 💡 Tips & Best Practices

### For Best AI Results

1. **Be specific:** "All shorts from December" is better than "get videos"
2. **Include context:** Mention the platform if URL is generic
3. **Use natural language:** Write like you're talking to a person
4. **Review interpretation:** Always check the confidence score

### For Bulk Downloads

1. **Start small:** Test with "latest 5" before downloading entire channels
2. **Use date ranges:** Narrow down to specific periods
3. **Enable skip existing:** Avoid re-downloading

### For Quality

- **"Best Available"** = Highest quality (default)
- **Specific resolution** = Caps at that resolution
- **"Audio Only"** = Extracts MP3

---

## 🔧 Troubleshooting

### AI Not Available

**Symptom:** No AI command section appears

**Solution:**
1. Check `.env` file exists with `GEMINI_API_KEY`
2. Verify `AI_ENABLED=true`
3. Restart application

### Low Confidence Scores

**Symptom:** AI shows <70% confidence

**Solution:**
1. Be more specific in your command
2. Include the URL
3. Use manual mode instead

### Site Not Detected

**Symptom:** Shows "Generic Site"

**Solution:**
1. Verify URL is correct
2. Site might not be in supported list (15+ platforms)
3. Use Playwright engine as fallback

### Date Parsing Issues

**Symptom:** Dates not recognized

**Solution:**
- Use YYYY-MM-DD format
- Or use relative: "last week", "yesterday"
- Check for typos

---

## 📊 Supported Platforms

✅ YouTube (Videos, Shorts, Channels, Playlists)  
✅ TikTok (Videos, User profiles)  
✅ Instagram (Posts, Reels, Stories)  
✅ Twitter/X (Videos, Images)  
✅ Facebook (Videos, Reels, Stories)  
✅ Vimeo (Videos, Channels)  
✅ Dailymotion (Videos, Channels)  
✅ Twitch (VODs, Clips)  
✅ SoundCloud (Tracks, Playlists)  
✅ Spotify (Tracks, Playlists, Albums)  
✅ Reddit (Videos, GIFs)  
✅ VK (Videos, Audio)  
✅ Bilibili (Videos)  
✅ Adult sites (Videos)  
✅ Generic sites (Fallback to Playwright)  

---

## 🎓 Example Workflows

### Workflow 1: Download YouTube Channel Shorts

1. Copy channel URL: `https://youtube.com/@MrBeast/shorts`
2. Paste in URL box
3. AI Command: `"All shorts from December 2024"`
4. Click "🚀 Parse with AI"
5. Review: Confidence 95%, Shorts Only, Date range correct
6. Click "✓ Accept"
7. Click "▶ START DOWNLOAD"

### Workflow 2: Download Instagram Reels

1. Copy profile URL: `https://instagram.com/username`
2. Paste in URL box
3. AI Command: `"Latest 20 reels"`
4. Click "🚀 Parse with AI"
5. Review: Reels Only, Max 20 videos
6. Click "✓ Accept"
7. Click "▶ START DOWNLOAD"

### Workflow 3: Download Spotify Playlist

1. Copy playlist URL
2. Paste in URL box
3. AI Command: `"Download the entire playlist as MP3"`
4. Click "🚀 Parse with AI"
5. Review: Audio Only, Playlist mode
6. Click "✓ Accept"
7. Click "▶ START DOWNLOAD"

---

## 📁 File Organization

Downloads are automatically organized:

```
Google Drive/OmniStream_Downloads/
├── YouTube/
│   ├── 2024-12/
│   │   ├── MrBeast/
│   │   │   ├── video1_id123.mp4
│   │   │   ├── video1_id123.info.json
│   │   │   └── video1_id123.jpg
├── TikTok/
│   ├── 2024-12/
│   │   └── username/
├── Instagram/
│   ├── 2024-12/
│   │   └── username/
```

---

## 💰 AI Cost

**Gemini 1.5 Flash Pricing:**
- ~$0.01 per month for 100 commands
- Extremely affordable
- No usage limits

---

## 🔐 Privacy & Security

✅ API key stored in `.env` (gitignored)  
✅ No data sent to external services (except Gemini for parsing)  
✅ All downloads local/Google Drive  
✅ Cookies stored locally  

---

## 🆘 Getting Help

1. Check console log for detailed errors
2. Review AI interpretation for ambiguities
3. Try manual mode if AI fails
4. Check README_SETUP.md for setup issues

---

**Enjoy your AI-powered downloading! 🚀**
