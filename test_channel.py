import yt_dlp

url = "https://www.youtube.com/@IndieLens-m5m"

ydl_opts = {
    'quiet': False,
    'extract_flat': True,
    'cookiefile': 'cookies.txt'
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    try:
        info = ydl.extract_info(url, download=False)
        print(f"\nChannel Type: {info.get('type')}")
        print(f"Channel ID: {info.get('channel_id')}")
        print(f"Available tabs: {info.get('tabs', [])}")
        
        if 'entries' in info:
            print(f"Total videos found: {len(list(info['entries']))}")
    except Exception as e:
        print(f"Error: {e}")
