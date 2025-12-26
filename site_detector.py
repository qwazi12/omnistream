"""
Site Detection Module
Intelligent pattern matching for 15+ platforms with capability detection
"""

from typing import Dict, List, Optional
from urllib.parse import urlparse
import re


class SiteDetector:
    """Detect platform and capabilities from URL"""
    
    # Platform patterns and capabilities
    SITE_PATTERNS = {
        'youtube.com': {
            'name': 'YouTube',
            'aliases': ['youtu.be', 'youtube.com'],
            'content_types': ['All Videos', 'Shorts Only', 'Audio Only'],
            'bulk_support': True,
            'date_filter': True,
            'quality_options': ['Best Available', '4K', '1440p', '1080p', '720p', '480p', 'Audio Only'],
            'supports_playlists': True,
            'supports_channels': True,
            'icon': '🎥'
        },
        'tiktok.com': {
            'name': 'TikTok',
            'aliases': ['tiktok.com', 'vm.tiktok.com'],
            'content_types': ['All Videos', 'Audio Only'],
            'bulk_support': True,
            'date_filter': True,
            'quality_options': ['Best Available', 'Audio Only'],
            'supports_playlists': False,
            'supports_channels': True,
            'icon': '🎵'
        },
        'instagram.com': {
            'name': 'Instagram',
            'aliases': ['instagram.com', 'instagr.am'],
            'content_types': ['All Videos', 'Reels Only', 'Stories Only', 'Audio Only'],
            'bulk_support': True,
            'date_filter': True,
            'quality_options': ['Best Available', 'Audio Only'],
            'supports_playlists': False,
            'supports_channels': True,
            'icon': '📸'
        },
        'twitter.com': {
            'name': 'Twitter/X',
            'aliases': ['twitter.com', 'x.com', 't.co'],
            'content_types': ['All Videos', 'Audio Only'],
            'bulk_support': True,
            'date_filter': True,
            'quality_options': ['Best Available', '1080p', '720p', 'Audio Only'],
            'supports_playlists': False,
            'supports_channels': True,
            'icon': '🐦'
        },
        'facebook.com': {
            'name': 'Facebook',
            'aliases': ['facebook.com', 'fb.com', 'fb.watch'],
            'content_types': ['All Videos', 'Reels Only', 'Stories Only', 'Audio Only'],
            'bulk_support': True,
            'date_filter': True,
            'quality_options': ['Best Available', '1080p', '720p', 'Audio Only'],
            'supports_playlists': False,
            'supports_channels': True,
            'icon': '👥'
        },
        'vimeo.com': {
            'name': 'Vimeo',
            'aliases': ['vimeo.com'],
            'content_types': ['All Videos', 'Audio Only'],
            'bulk_support': True,
            'date_filter': True,
            'quality_options': ['Best Available', '4K', '1080p', '720p', 'Audio Only'],
            'supports_playlists': True,
            'supports_channels': True,
            'icon': '🎬'
        },
        'dailymotion.com': {
            'name': 'Dailymotion',
            'aliases': ['dailymotion.com', 'dai.ly'],
            'content_types': ['All Videos', 'Audio Only'],
            'bulk_support': True,
            'date_filter': True,
            'quality_options': ['Best Available', '1080p', '720p', '480p', 'Audio Only'],
            'supports_playlists': True,
            'supports_channels': True,
            'icon': '📹'
        },
        'twitch.tv': {
            'name': 'Twitch',
            'aliases': ['twitch.tv'],
            'content_types': ['All Videos', 'Clips Only', 'Audio Only'],
            'bulk_support': True,
            'date_filter': True,
            'quality_options': ['Best Available', '1080p', '720p', '480p', 'Audio Only'],
            'supports_playlists': False,
            'supports_channels': True,
            'icon': '🎮'
        },
        'soundcloud.com': {
            'name': 'SoundCloud',
            'aliases': ['soundcloud.com'],
            'content_types': ['Audio Only', 'Playlists'],
            'bulk_support': True,
            'date_filter': True,
            'quality_options': ['Best Available'],
            'supports_playlists': True,
            'supports_channels': True,
            'icon': '🎧'
        },
        'spotify.com': {
            'name': 'Spotify',
            'aliases': ['spotify.com', 'open.spotify.com'],
            'content_types': ['Audio Only', 'Playlists', 'Albums'],
            'bulk_support': True,
            'date_filter': False,
            'quality_options': ['Best Available'],
            'supports_playlists': True,
            'supports_channels': True,
            'icon': '🎵'
        },
        'reddit.com': {
            'name': 'Reddit',
            'aliases': ['reddit.com', 'redd.it', 'v.redd.it'],
            'content_types': ['All Videos', 'Audio Only'],
            'bulk_support': True,
            'date_filter': True,
            'quality_options': ['Best Available', '720p', '480p', 'Audio Only'],
            'supports_playlists': False,
            'supports_channels': True,
            'icon': '🤖'
        },
        'vk.com': {
            'name': 'VK',
            'aliases': ['vk.com', 'vkontakte.ru'],
            'content_types': ['All Videos', 'Audio Only'],
            'bulk_support': True,
            'date_filter': True,
            'quality_options': ['Best Available', '1080p', '720p', 'Audio Only'],
            'supports_playlists': True,
            'supports_channels': True,
            'icon': '🇷🇺'
        },
        'bilibili.com': {
            'name': 'Bilibili',
            'aliases': ['bilibili.com', 'b23.tv'],
            'content_types': ['All Videos', 'Audio Only'],
            'bulk_support': True,
            'date_filter': True,
            'quality_options': ['Best Available', '1080p', '720p', 'Audio Only'],
            'supports_playlists': True,
            'supports_channels': True,
            'icon': '📺'
        },
        'pornhub.com': {
            'name': 'Adult Site',
            'aliases': ['pornhub.com', 'xvideos.com', 'xnxx.com'],
            'content_types': ['All Videos', 'Audio Only'],
            'bulk_support': True,
            'date_filter': True,
            'quality_options': ['Best Available', '1080p', '720p', 'Audio Only'],
            'supports_playlists': True,
            'supports_channels': True,
            'icon': '🔞'
        },
        'generic': {
            'name': 'Generic Site',
            'aliases': [],
            'content_types': ['All Videos', 'Audio Only'],
            'bulk_support': False,
            'date_filter': False,
            'quality_options': ['Best Available', 'Audio Only'],
            'supports_playlists': False,
            'supports_channels': False,
            'icon': '🌐'
        }
    }
    
    @classmethod
    def detect_site(cls, url: str) -> Dict:
        """
        Detect platform from URL
        
        Args:
            url: URL to analyze
            
        Returns:
            dict with site info and capabilities
        """
        if not url:
            return cls._get_site_info('generic')
        
        url_lower = url.lower()
        parsed = urlparse(url_lower)
        domain = parsed.netloc.replace('www.', '')
        
        # Check each platform's aliases
        for site_key, site_data in cls.SITE_PATTERNS.items():
            if site_key == 'generic':
                continue
                
            for alias in site_data['aliases']:
                if alias in domain or alias in url_lower:
                    return cls._get_site_info(site_key)
        
        # Default to generic
        return cls._get_site_info('generic')
    
    @classmethod
    def _get_site_info(cls, site_key: str) -> Dict:
        """Get complete site information"""
        site_data = cls.SITE_PATTERNS.get(site_key, cls.SITE_PATTERNS['generic'])
        return {
            'key': site_key,
            'name': site_data['name'],
            'icon': site_data['icon'],
            'content_types': site_data['content_types'],
            'quality_options': site_data['quality_options'],
            'bulk_support': site_data['bulk_support'],
            'date_filter': site_data['date_filter'],
            'supports_playlists': site_data['supports_playlists'],
            'supports_channels': site_data['supports_channels']
        }
    
    @classmethod
    def is_bulk_url(cls, url: str) -> bool:
        """Check if URL is a bulk operation (playlist/channel)"""
        bulk_indicators = [
            'playlist', 'channel', '/c/', '/@', '/user/',
            'albums', 'sets', 'collections'
        ]
        return any(indicator in url.lower() for indicator in bulk_indicators)
    
    @classmethod
    def get_url_type(cls, url: str) -> str:
        """Determine URL type (single, playlist, channel)"""
        url_lower = url.lower()
        
        if 'playlist' in url_lower or 'list=' in url_lower:
            return 'playlist'
        elif any(x in url_lower for x in ['channel', '/c/', '/@', '/user/']):
            return 'channel'
        elif 'album' in url_lower:
            return 'album'
        else:
            return 'single'
