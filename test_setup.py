#!/usr/bin/env python3
"""
Quick verification script to test OmniStream Archiver setup
"""

import sys
import os

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import customtkinter
        print("✅ customtkinter imported successfully")
    except ImportError as e:
        print(f"❌ customtkinter import failed: {e}")
        return False
    
    try:
        import yt_dlp
        print("✅ yt-dlp imported successfully")
    except ImportError as e:
        print(f"❌ yt-dlp import failed: {e}")
        return False
    
    try:
        from playwright.sync_api import sync_playwright
        print("✅ playwright imported successfully")
    except ImportError as e:
        print(f"❌ playwright import failed: {e}")
        return False
    
    try:
        import requests
        print("✅ requests imported successfully")
    except ImportError as e:
        print(f"❌ requests import failed: {e}")
        return False
    
    try:
        from fake_useragent import UserAgent
        print("✅ fake-useragent imported successfully")
    except ImportError as e:
        print(f"❌ fake-useragent import failed: {e}")
        return False
    
    return True

def test_modules():
    """Test that all project modules can be imported"""
    print("\nTesting project modules...")
    
    try:
        from utils import detect_google_drive
        print("✅ utils module imported successfully")
    except ImportError as e:
        print(f"❌ utils import failed: {e}")
        return False
    
    try:
        from engine_router import EngineRouter
        print("✅ engine_router module imported successfully")
    except ImportError as e:
        print(f"❌ engine_router import failed: {e}")
        return False
    
    try:
        from ytdlp_engine import YtDlpEngine
        print("✅ ytdlp_engine module imported successfully")
    except ImportError as e:
        print(f"❌ ytdlp_engine import failed: {e}")
        return False
    
    try:
        from jdownloader_engine import JDownloaderEngine
        print("✅ jdownloader_engine module imported successfully")
    except ImportError as e:
        print(f"❌ jdownloader_engine import failed: {e}")
        return False
    
    try:
        from playwright_engine import PlaywrightEngine
        print("✅ playwright_engine module imported successfully")
    except ImportError as e:
        print(f"❌ playwright_engine import failed: {e}")
        return False
    
    return True

def test_google_drive_detection():
    """Test Google Drive detection"""
    print("\nTesting Google Drive detection...")
    
    try:
        from utils import detect_google_drive
        is_connected, base_path = detect_google_drive()
        
        if is_connected:
            print(f"✅ Google Drive detected at: {base_path}")
        else:
            print(f"⚠️  Google Drive not detected, using fallback: {base_path}")
        
        return True
    except Exception as e:
        print(f"❌ Google Drive detection failed: {e}")
        return False

def test_engine_router():
    """Test engine routing logic"""
    print("\nTesting engine router...")
    
    try:
        from engine_router import EngineRouter
        
        # Test video platform detection
        youtube_url = "https://www.youtube.com/watch?v=test"
        engine = EngineRouter.choose_engine(youtube_url)
        assert engine == "yt-dlp", f"Expected yt-dlp for YouTube, got {engine}"
        print(f"✅ YouTube URL → {engine}")
        
        # Test file host detection
        mega_url = "https://mega.nz/file/test"
        engine = EngineRouter.choose_engine(mega_url)
        assert engine == "jdownloader", f"Expected jdownloader for Mega, got {engine}"
        print(f"✅ Mega URL → {engine}")
        
        # Test unknown site detection
        unknown_url = "https://example.com/video.mp4"
        engine = EngineRouter.choose_engine(unknown_url)
        assert engine == "playwright", f"Expected playwright for unknown site, got {engine}"
        print(f"✅ Unknown URL → {engine}")
        
        return True
    except Exception as e:
        print(f"❌ Engine router test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("OmniStream Archiver - Setup Verification")
    print("=" * 60)
    
    all_passed = True
    
    # Test imports
    if not test_imports():
        all_passed = False
    
    # Test modules
    if not test_modules():
        all_passed = False
    
    # Test Google Drive detection
    if not test_google_drive_detection():
        all_passed = False
    
    # Test engine router
    if not test_engine_router():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED - OmniStream is ready to use!")
        print("Run './run.sh' to launch the application")
    else:
        print("❌ SOME TESTS FAILED - Please check the errors above")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
