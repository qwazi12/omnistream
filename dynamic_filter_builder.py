"""
Dynamic Filter Builder
Converts user filters into yt-dlp options with date parsing and advanced filtering
"""

from typing import Dict, Optional, Callable
from datetime import datetime, timedelta
import re


class DynamicFilterBuilder:
    """Build yt-dlp options from user-defined filters"""
    
    @staticmethod
    def parse_date_input(date_str: str) -> str:
        """
        Parse various date formats including relative dates
        
        Args:
            date_str: Date string (YYYY-MM-DD, "today", "yesterday", "last week", etc.)
            
        Returns:
            Date in YYYYMMDD format for yt-dlp
        """
        if not date_str:
            return None
        
        date_str_lower = date_str.lower().strip()
        
        # Relative dates
        if date_str_lower == 'today':
            return datetime.now().strftime('%Y%m%d')
        elif date_str_lower == 'yesterday':
            return (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
        elif date_str_lower in ['this week', 'last 7 days']:
            return (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
        elif date_str_lower in ['this month', 'last 30 days']:
            return (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        elif date_str_lower in ['last week']:
            return (datetime.now() - timedelta(days=14)).strftime('%Y%m%d')
        elif date_str_lower in ['last month']:
            return (datetime.now() - timedelta(days=60)).strftime('%Y%m%d')
        
        # Extract number of days (e.g., "last 5 days")
        match = re.search(r'last (\d+) days?', date_str_lower)
        if match:
            days = int(match.group(1))
            return (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
        
        # Parse YYYY-MM-DD format
        try:
            parsed = datetime.strptime(date_str, '%Y-%m-%d')
            return parsed.strftime('%Y%m%d')
        except ValueError:
            pass
        
        # Try other common formats
        for fmt in ['%m/%d/%Y', '%d/%m/%Y', '%Y%m%d']:
            try:
                parsed = datetime.strptime(date_str, fmt)
                return parsed.strftime('%Y%m%d')
            except ValueError:
                continue
        
        return None
    
    @staticmethod
    def build_match_filter(filters: Dict) -> Optional[Callable]:
        """
        Build custom match filter function for yt-dlp
        
        Args:
            filters: Dictionary of filter criteria
            
        Returns:
            Callable filter function or None
        """
        def match_filter(info, incomplete):
            """Custom filter logic"""
            
            # Duration filter
            min_duration = filters.get('min_duration')
            max_duration = filters.get('max_duration')
            duration = info.get('duration', 0)
            
            if min_duration and duration < min_duration:
                return f"Duration {duration}s is less than minimum {min_duration}s"
            if max_duration and duration > max_duration:
                return f"Duration {duration}s exceeds maximum {max_duration}s"
            
            # Title exclusion patterns
            exclude_titles = filters.get('exclude_titles', [])
            title = info.get('title', '').lower()
            for pattern in exclude_titles:
                if pattern.lower() in title:
                    return f"Title contains excluded pattern: {pattern}"
            
            # Title inclusion patterns (must match at least one)
            include_titles = filters.get('include_titles', [])
            if include_titles:
                if not any(pattern.lower() in title for pattern in include_titles):
                    return f"Title does not match any required patterns"
            
            # View count filter
            min_views = filters.get('min_views')
            max_views = filters.get('max_views')
            views = info.get('view_count', 0)
            
            if min_views and views < min_views:
                return f"View count {views} is less than minimum {min_views}"
            if max_views and views > max_views:
                return f"View count {views} exceeds maximum {max_views}"
            
            # Content type filter (Shorts, Reels, etc.)
            content_type = filters.get('content_type', 'All Videos')
            
            if 'Shorts Only' in content_type or 'Reels Only' in content_type:
                url = info.get('webpage_url', '')
                original_url = info.get('original_url', '')
                width = info.get('width')
                height = info.get('height')
                
                # Check for vertical format
                is_vertical = False
                if '/shorts/' in url or '/shorts/' in original_url or '/reel/' in url:
                    is_vertical = True
                elif width and height and height > width:
                    is_vertical = True
                
                if not is_vertical:
                    return "Not a Short/Reel (horizontal format)"
            
            # All checks passed
            return None
        
        # Only return filter if we have active filters
        if any(filters.get(k) for k in ['min_duration', 'max_duration', 'exclude_titles', 
                                         'include_titles', 'min_views', 'max_views', 'content_type']):
            return match_filter
        
        return None
    
    @staticmethod
    def build_ytdlp_options(filters: Dict, base_output_path: str) -> Dict:
        """
        Build complete yt-dlp options dictionary
        
        Args:
            filters: User-defined filters
            base_output_path: Base directory for downloads
            
        Returns:
            Complete yt-dlp options dict
        """
        options = {
            'outtmpl': f'{base_output_path}/%(uploader)s/%(title)s_%(id)s.%(ext)s',
            'ignoreerrors': True,
            'no_warnings': False,
            'extract_flat': False,
            'writeinfojson': True,
            'writethumbnail': True,
            'geo_bypass': True,
            'nocheckcertificate': True,
        }
        
        # Quality/Format selection
        quality = filters.get('quality', 'Best Available')
        content_type = filters.get('content_type', 'All Videos')
        
        if 'Audio Only' in content_type or 'Audio Only' in quality:
            options['format'] = 'bestaudio/best'
            options['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        elif 'Shorts Only' in content_type or 'Reels Only' in content_type:
            # Prioritize vertical formats
            options['format'] = 'bestvideo[height>width]+bestaudio/best[height>width]/best'
        else:
            # Standard video format
            format_map = {
                'Best Available': 'bestvideo+bestaudio/best',
                '4K': 'bestvideo[height<=2160]+bestaudio/best[height<=2160]',
                '1440p': 'bestvideo[height<=1440]+bestaudio/best[height<=1440]',
                '1080p': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
                '720p': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
                '480p': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
            }
            options['format'] = format_map.get(quality, format_map['Best Available'])
        
        # Date range filtering
        date_from = DynamicFilterBuilder.parse_date_input(filters.get('date_from'))
        date_to = DynamicFilterBuilder.parse_date_input(filters.get('date_to'))
        
        if date_from:
            options['dateafter'] = date_from
        if date_to:
            options['datebefore'] = date_to
        
        # File size limits
        max_filesize = filters.get('max_filesize')
        if max_filesize:
            # Convert to bytes if needed (e.g., "500M" -> 524288000)
            if isinstance(max_filesize, str):
                max_filesize = max_filesize.upper()
                if 'G' in max_filesize:
                    max_filesize = float(max_filesize.replace('G', '')) * 1024 * 1024 * 1024
                elif 'M' in max_filesize:
                    max_filesize = float(max_filesize.replace('M', '')) * 1024 * 1024
            options['max_filesize'] = int(max_filesize)
        
        # Playlist/count limits
        max_downloads = filters.get('max_downloads')
        if max_downloads:
            options['playlistend'] = min(max_downloads, 500)  # Safety cap
        
        # Subtitles
        if filters.get('download_subtitles', False):
            options['writesubtitles'] = True
            options['writeautomaticsub'] = True
            options['subtitleslangs'] = ['en', 'en-US']
        
        # Skip existing files
        if filters.get('skip_existing', True):
            options['download_archive'] = f'{base_output_path}/.download_archive.txt'
        
        # Custom match filter
        match_filter = DynamicFilterBuilder.build_match_filter(filters)
        if match_filter:
            options['match_filter'] = match_filter
        
        return options
    
    @staticmethod
    def validate_filters(filters: Dict) -> Dict:
        """
        Validate and sanitize filter values
        
        Args:
            filters: Raw filter dictionary
            
        Returns:
            Validated and sanitized filters with warnings
        """
        validated = filters.copy()
        warnings = []
        
        # Cap excessive download counts
        if validated.get('max_downloads', 0) > 500:
            validated['max_downloads'] = 500
            warnings.append('Download count capped at 500 for safety')
        
        # Validate date range
        date_from = DynamicFilterBuilder.parse_date_input(validated.get('date_from'))
        date_to = DynamicFilterBuilder.parse_date_input(validated.get('date_to'))
        
        if date_from and date_to and date_from > date_to:
            # Swap if reversed
            validated['date_from'], validated['date_to'] = validated['date_to'], validated['date_from']
            warnings.append('Date range was reversed (from > to), automatically corrected')
        
        # Validate duration range
        min_dur = validated.get('min_duration', 0)
        max_dur = validated.get('max_duration', 0)
        
        if min_dur and max_dur and min_dur > max_dur:
            validated['min_duration'], validated['max_duration'] = max_dur, min_dur
            warnings.append('Duration range was reversed, automatically corrected')
        
        validated['_warnings'] = warnings
        return validated
