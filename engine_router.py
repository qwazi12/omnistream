```
"""
Intelligent routing system for download engines
"""


class EngineRouter:
    """Intelligent routing system for download engines"""
    
    VIDEO_PLATFORMS = [
        'youtube.com', 'youtu.be', 'tiktok.com',
        'twitter.com', 'x.com', 'vimeo.com', 'twitch.tv',
        'facebook.com', 'fb.watch', 'reddit.com', 'dailymotion.com'
    ]
    
    FILE_HOSTS = [
        'mega.nz', 'mega.co.nz', 'mediafire.com', 'rapidgator.net',
        '1fichier.com', 'uploaded.net', 'turbobit.net', 'nitroflare.com',
        'zippyshare.com', 'sendspace.com', 'depositfiles.com'
    ]
    
    @staticmethod
    def choose_engine(url: str) -> str:
        """
        Intelligent engine selection based on URL patterns
        
        Args:
            url: The URL to analyze
            
        Returns:
            'yt-dlp' | 'jdownloader' | 'playwright'
        """
        url_lower = url.lower()
        
        # Check for video platforms
        for platform in EngineRouter.VIDEO_PLATFORMS:
            if platform in url_lower:
                return 'yt-dlp'
        
        # Check for file hosting services
        for host in EngineRouter.FILE_HOSTS:
            if host in url_lower:
                return 'jdownloader'
        
        # Default to Playwright for unknown sites
        return 'playwright'
