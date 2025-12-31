# Social Media Auto-Posting Setup Guide

## Quick Start

### 1. Install Dependencies
```bash
cd /Users/kwasiyeboah/m3/omnistream
pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
```

### 2. Setup YouTube (5 minutes)

**Get OAuth Credentials:**
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Enable **YouTube Data API v3**:
   - APIs & Services → Library
   - Search "YouTube Data API v3"
   - Click Enable
4. Create OAuth credentials:
   - APIs & Services → Credentials
   - Create Credentials → OAuth 2.0 Client ID
   - Application type: Desktop app
   - Download credentials as **`youtube_credentials.json`**
5. Save to OmniStream directory

**Test Authentication:**
```bash
python3 youtube_poster.py
```
- Browser will open for authorization
- Allow access to your YouTube channel
- Credentials saved for future use

### 3. Setup Facebook (10 minutes)

**Get Page Access Token:**
1. Go to [Facebook Developers](https://developers.facebook.com)
2. Create app (Business type) if you don't have one
3. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer)
4. Select your Page
5. Click "Get Page Access Token"
6. Select permissions:
   - `pages_manage_posts`
   - `pages_read_engagement`
   - `pages_show_list`
7. Generate token

**Run Setup:**
```bash
python3 facebook_poster.py --setup
```
- Paste your Page Access Token
- Select which Page to use
- Config saved automatically

---

## Usage Examples

### Upload Single Video

**YouTube:**
```python
from youtube_poster import YouTubePoster

poster = YouTubePoster()
video_id = poster.upload_video(
    filepath="video.mp4",
    title="My Awesome Video",
    description="Check this out!",
    tags=["viral", "trending"],
    privacy="public"  # or "private", "unlisted"
)
```

**Facebook:**
```python
from facebook_poster import FacebookPoster

poster = FacebookPoster()
video_id = poster.upload_video(
    filepath="video.mp4",
    caption="Check out this awesome video! 🔥\n\n#Viral #Trending",
    published=True
)
```

### Batch Upload
```python
from youtube_poster import YouTubePoster
from facebook_poster import FacebookPoster
from pathlib import Path

yt = YouTubePoster()
fb = FacebookPoster()

video_dir = Path("/path/to/videos")

for video_file in video_dir.glob("*.mp4"):
    title = video_file.stem  # Filename without extension
    
    # Upload to YouTube
    yt_id = yt.upload_video(
        filepath=str(video_file),
        title=title,
        privacy="public"
    )
    
    # Upload to Facebook
    fb_id = fb.upload_video(
        filepath=str(video_file),
        caption=f"{title} 🎬"
    )
    
    print(f"✅ Uploaded {title} to YouTube and Facebook")
```

---

## Integration with OmniStream

Once setup is complete, auto-posting will work like this:

```python
from omnistream_downloader import download_video
from youtube_poster import YouTubePoster
from facebook_poster import FacebookPoster

# Download video
video_path = download_video("https://tiktok.com/@user/video/123")

# Auto-post to YouTube
yt = YouTubePoster()
yt.upload_video(
    filepath=video_path,
    title="Reposted from TikTok",
    description="Great content!",
    tags=["tiktok", "viral"]
)

# Auto-post to Facebook
fb = FacebookPoster()
fb.upload_video(
    filepath=video_path,
    caption="Check this out! 🔥 #Viral"
)
```

---

## Troubleshooting

### YouTube Issues

**"Quota exceeded" error:**
- YouTube has daily upload limits (10,000 quota units)
- Each upload uses ~1600 units (~6 videos/day)
- Check quota: https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas
- Request quota increase if needed

**OAuth errors:**
- Delete `youtube_token.pickle` and re-authenticate
- Make sure `youtube_credentials.json` is in the project directory

### Facebook Issues

**"Invalid access token":**
- Page Access Tokens expire after 60 days
- Re-run setup: `python3 facebook_poster.py --setup`

**"Cannot upload to personal profile":**
- Facebook API only works with Pages, not personal profiles
- Create a Facebook Page or use an existing one

**Upload fails:**
- File must be under 10 GB
- Supported formats: MP4, MOV, AVI

---

## API Limits

### YouTube
- **Quota**: 10,000 units/day
- **Upload cost**: ~1600 units
- **Daily uploads**: ~6 videos
- **File size**: 256 GB max (128 GB recommended)

### Facebook
- **Rate limit**: ~200 requests/hour
- **File size**: 10 GB max
- **Video length**: No strict limit
- **Daily uploads**: No official limit

---

## Next Steps

1. Test uploading a single video to each platform
2. Try batch uploading a few videos
3. Integrate with OmniStream download workflow
4. Set up scheduling for automated posting

Need help? Check the implementation plan or ask!
