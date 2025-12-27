#!/usr/bin/env python3
"""
Storage management utilities for OmniStream
Checks disk space and prevents critical low-space situations
"""

import shutil
import os
from typing import Tuple


def check_disk_space(path: str = "/", min_gb: float = 10.0) -> Tuple[bool, float, float, float]:
    """
    Check available disk space
    
    Args:
        path: Path to check (default: root)
        min_gb: Minimum required space in GB
        
    Returns:
        Tuple of (has_enough_space, free_gb, used_gb, total_gb)
    """
    try:
        stat = shutil.disk_usage(path)
        free_gb = stat.free / (1024**3)
        used_gb = stat.used / (1024**3)
        total_gb = stat.total / (1024**3)
        
        has_space = free_gb >= min_gb
        
        return has_space, free_gb, used_gb, total_gb
        
    except Exception as e:
        print(f"Error checking disk space: {e}")
        # Return safe defaults (assume no space to be safe)
        return False, 0.0, 0.0, 0.0


def get_storage_stats() -> dict:
    """
    Get comprehensive storage statistics
    
    Returns:
        Dictionary with storage info and status
    """
    has_space, free_gb, used_gb, total_gb = check_disk_space()
    
    # Determine status level
    if free_gb < 5:
        status = "critical"
        color = "#ff0000"
        icon = "🔴"
    elif free_gb < 10:
        status = "warning"
        color = "#ffaa00"
        icon = "🟡"
    elif free_gb < 50:
        status = "moderate"
        color = "#00aaff"
        icon = "🟢"
    else:
        status = "good"
        color = "#00ff00"
        icon = "🟢"
    
    return {
        'free_gb': free_gb,
        'used_gb': used_gb,
        'total_gb': total_gb,
        'percent_used': (used_gb / total_gb * 100) if total_gb > 0 else 0,
        'status': status,
        'color': color,
        'icon': icon,
        'has_space': has_space
    }


def format_storage_display(stats: dict) -> str:
    """
    Format storage stats for UI display
    
    Args:
        stats: Dictionary from get_storage_stats()
        
    Returns:
        Formatted string for display
    """
    icon = stats['icon']
    free = stats['free_gb']
    total = stats['total_gb']
    percent = stats['percent_used']
    
    return f"{icon} Storage: {free:.1f}GB free / {total:.1f}GB ({percent:.0f}% used)"
