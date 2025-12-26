"""
OmniStream Archiver - Main Application
Triple-Engine Universal Downloader with Google Drive Integration
"""

import customtkinter as ctk
import threading
import os
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from utils import detect_google_drive
from engine_router import EngineRouter
from ytdlp_engine import YtDlpEngine
from jdownloader_engine import JDownloaderEngine
from playwright_engine import PlaywrightEngine
from site_detector import SiteDetector
from dynamic_filter_builder import DynamicFilterBuilder
from ai_assistant import AICommandParser, AIErrorPredictor


class OmniStreamApp(ctk.CTk):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Window configuration
        self.title("OmniStream Archiver - Triple Engine Downloader")
        self.geometry("1000x1000")  # Increased height to fit all UI sections
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Initialize storage
        self.drive_connected, self.base_path = detect_google_drive()
        
        # Initialize AI assistant
        self.ai_parser = AICommandParser()
        self.ai_predictor = AIErrorPredictor()
        self.ai_enabled = self.ai_parser.is_available()
        
        # Initialize engines
        self.ytdlp_engine = None
        self.jdownloader_engine = None
        self.playwright_engine = None
        self.is_downloading = False
        self.download_thread = None
        self.use_drive_api_var = False  # Drive API toggle state
        
        # Current site tracking
        self.current_site_info = None
        self.current_ai_config = None
        
        # Build UI
        self.create_header()
        self.create_ai_command_section()  # NEW: AI natural language input
        self.create_input_section()
        self.create_interpretation_panel()  # NEW: AI parsing results
        self.create_dynamic_filters_section()  # NEW: Site-aware filters
        self.create_settings_section()
        self.create_status_bar()  # MOVED: Create before console so log() can access status_text
        self.create_console_section()
        self.create_progress_section()
        self.create_control_section()
        
        # Initialize JDownloader check
        self.after(1000, self.check_jdownloader_status)
    
    def create_header(self):
        """Create header with title and status"""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(pady=15, padx=20, fill="x")
        
        title = ctk.CTkLabel(
            header_frame,
            text="OmniStream Archiver",
            font=("Arial", 32, "bold")
        )
        title.pack()
        
        subtitle = ctk.CTkLabel(
            header_frame,
            text="Triple-Engine Universal Downloader",
            font=("Arial", 14),
            text_color="gray"
        )
        subtitle.pack(pady=(0, 5))
        
        # Storage status
        status_color = "#00ff00" if self.drive_connected else "#ffaa00"
        status_icon = "🟢" if self.drive_connected else "🟡"
        status_text = f"{status_icon} Google Drive: {self.base_path}" if self.drive_connected \
                     else f"{status_icon} Local Storage: {self.base_path}"
        
        self.storage_status = ctk.CTkLabel(
            header_frame,
            text=status_text,
            font=("Arial", 11),
            text_color=status_color
        )
        self.storage_status.pack()
        
        # Engine status frame
        engine_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        engine_frame.pack(pady=(5, 0))
        
        self.ytdlp_status = ctk.CTkLabel(
            engine_frame,
            text="🎥 yt-dlp: Ready",
            font=("Arial", 10),
            text_color="#00ff00"
        )
        self.ytdlp_status.pack(side="left", padx=10)
        
        self.jd_status = ctk.CTkLabel(
            engine_frame,
            text="📦 JDownloader: Checking...",
            font=("Arial", 10),
            text_color="gray"
        )
        self.jd_status.pack(side="left", padx=10)
        
        self.playwright_status = ctk.CTkLabel(
            engine_frame,
            text="🌐 Playwright: Ready",
            font=("Arial", 10),
            text_color="#00ff00"
        )
        self.playwright_status.pack(side="left", padx=10)
    
    def create_ai_command_section(self):
        """Create AI natural language command input"""
        if not self.ai_enabled:
            return  # Skip if AI not available
        
        ai_frame = ctk.CTkFrame(self)
        ai_frame.pack(pady=10, padx=20, fill="x")
        
        # Header with AI status
        header_frame = ctk.CTkFrame(ai_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        ai_label = ctk.CTkLabel(
            header_frame,
            text="🤖 AI Command (Natural Language)",
            font=("Arial", 13, "bold")
        )
        ai_label.pack(side="left")
        
        ai_status = ctk.CTkLabel(
            header_frame,
            text="✅ AI Ready" if self.ai_enabled else "❌ AI Unavailable",
            font=("Arial", 10),
            text_color="#00ff00" if self.ai_enabled else "#ff0000"
        )
        ai_status.pack(side="left", padx=10)
        
        # AI command input
        self.ai_command_entry = ctk.CTkEntry(
            ai_frame,
            placeholder_text='e.g., "Download all MrBeast shorts from December 2024"',
            height=40,
            font=("Arial", 12)
        )
        self.ai_command_entry.pack(padx=10, pady=5, fill="x")
        
        # Buttons
        button_frame = ctk.CTkFrame(ai_frame, fg_color="transparent")
        button_frame.pack(pady=(0, 10))
        
        parse_btn = ctk.CTkButton(
            button_frame,
            text="🚀 Parse with AI",
            command=self.parse_ai_command,
            width=150,
            height=35,
            fg_color="#0066cc",
            hover_color="#0052a3"
        )
        parse_btn.pack(side="left", padx=5)
        
        manual_btn = ctk.CTkButton(
            button_frame,
            text="⚙️ Manual Filters",
            command=self.toggle_manual_mode,
            width=150,
            height=35
        )
        manual_btn.pack(side="left", padx=5)
    
    def create_interpretation_panel(self):
        """Create AI interpretation display panel"""
        self.interpretation_frame = ctk.CTkFrame(self)
        # Initially hidden, shown after AI parsing
        
        label = ctk.CTkLabel(
            self.interpretation_frame,
            text="✅ AI Interpretation:",
            font=("Arial", 12, "bold")
        )
        label.pack(anchor="w", padx=10, pady=(10, 5))
        
        self.interpretation_text = ctk.CTkTextbox(
            self.interpretation_frame,
            height=100,
            font=("Arial", 10),
            state="disabled"
        )
        self.interpretation_text.pack(padx=10, pady=(0, 5), fill="x")
        
        # Action buttons
        action_frame = ctk.CTkFrame(self.interpretation_frame, fg_color="transparent")
        action_frame.pack(pady=(0, 10))
        
        self.accept_btn = ctk.CTkButton(
            action_frame,
            text="✓ Accept",
            command=self.accept_ai_config,
            width=120,
            fg_color="#00aa00",
            hover_color="#008800"
        )
        self.accept_btn.pack(side="left", padx=5)
        
        edit_btn = ctk.CTkButton(
            action_frame,
            text="✎ Edit Manually",
            command=self.edit_ai_config,
            width=120
        )
        edit_btn.pack(side="left", padx=5)
    
    def create_dynamic_filters_section(self):
        """Create dynamic site-aware filter options with SCROLLING"""
        # Use scrollable frame to ensure all controls are accessible
        self.filters_frame = ctk.CTkScrollableFrame(
            self,
            label_text="🎯 Dynamic Filters (Site-Aware)",
            label_font=("Arial", 14, "bold"),
            height=300  # Fixed height to enable scrolling
        )
        self.filters_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        # Site info label
        self.site_info_label = ctk.CTkLabel(
            self.filters_frame,
            text="Paste a URL above to see site-specific options",
            font=("Arial", 10),
            text_color="gray"
        )
        self.site_info_label.pack(anchor="w", padx=10, pady=(0, 10))
        
        # Filter controls (dynamically populated)
        self.filter_controls_frame = ctk.CTkFrame(self.filters_frame, fg_color="transparent")
        self.filter_controls_frame.pack(padx=10, pady=(0, 10), fill="both", expand=True)
    
    def create_input_section(self):
        """Create URL input area"""
        input_frame = ctk.CTkFrame(self)
        input_frame.pack(pady=10, padx=20, fill="x")
        
        label = ctk.CTkLabel(input_frame, text="URL Input (one per line):", font=("Arial", 13, "bold"))
        label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Text box for URLs
        self.url_entry = ctk.CTkTextbox(
            input_frame,
            height=100,
            font=("Consolas", 11),
            border_width=2
        )
        self.url_entry.pack(padx=10, pady=5, fill="x")
        
        # Button row
        button_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        button_frame.pack(pady=(0, 10))
        
        paste_btn = ctk.CTkButton(
            button_frame,
            text="📋 Paste",
            command=self.paste_url,
            width=120,
            height=32
        )
        paste_btn.pack(side="left", padx=5)
        
        clear_btn = ctk.CTkButton(
            button_frame,
            text="🗑️ Clear",
            command=self.clear_input,
            width=120,
            height=32
        )
        clear_btn.pack(side="left", padx=5)
    
    def create_settings_section(self):
        """Create settings dropdowns"""
        settings_frame = ctk.CTkFrame(self)
        settings_frame.pack(pady=5, padx=20, fill="x")
        
        settings_grid = ctk.CTkFrame(settings_frame, fg_color="transparent")
        settings_grid.pack(pady=10, padx=10)
        
        # Mode selector
        mode_label = ctk.CTkLabel(settings_grid, text="Mode:", font=("Arial", 12, "bold"))
        mode_label.grid(row=0, column=0, padx=10, pady=5, sticky="e")
        
        self.mode_var = ctk.StringVar(value="All Videos (Best Quality)")
        mode_dropdown = ctk.CTkOptionMenu(
            settings_grid,
            variable=self.mode_var,
            values=["All Videos (Best Quality)", "Audio Only", "Shorts Only (Vertical Filter)", "Bulk Channel"],
            width=200
        )
        mode_dropdown.grid(row=0, column=1, padx=10, pady=5)
        
        # Quality selector
        quality_label = ctk.CTkLabel(settings_grid, text="Quality:", font=("Arial", 12, "bold"))
        quality_label.grid(row=0, column=2, padx=10, pady=5, sticky="e")
        
        self.quality_var = ctk.StringVar(value="Best Available")
        quality_dropdown = ctk.CTkOptionMenu(
            settings_grid,
            variable=self.quality_var,
            values=["Best Available", "1080p", "720p", "480p", "Audio Only"],
            width=180
        )
        quality_dropdown.grid(row=0, column=3, padx=10, pady=5)
        
        # Max Downloads (NEW)
        max_label = ctk.CTkLabel(settings_grid, text="Max Videos:", font=("Arial", 12, "bold"))
        max_label.grid(row=0, column=4, padx=10, pady=5, sticky="e")
        
        self.max_downloads_entry = ctk.CTkEntry(
            settings_grid,
            placeholder_text="Leave empty for all",
            width=120
        )
        self.max_downloads_entry.grid(row=0, column=5, padx=10, pady=5)
        
        # Format selector (NEW)
        format_label = ctk.CTkLabel(settings_grid, text="Format:", font=("Arial", 12, "bold"))
        format_label.grid(row=1, column=0, padx=10, pady=5, sticky="e")
        
        self.format_var = ctk.StringVar(value="Video + Audio (MP4)")
        format_dropdown = ctk.CTkOptionMenu(
            settings_grid,
            variable=self.format_var,
            values=[
                "Video + Audio (MP4)",
                "Video Only (MP4)",
                "Audio Only (MP3)",
                "Audio Only (M4A)",
                "Best Available (Auto)"
            ],
            width=200
        )
        format_dropdown.grid(row=1, column=1, padx=10, pady=5)
        
        # Engine override
        engine_label = ctk.CTkLabel(settings_grid, text="Engine:", font=("Arial", 12, "bold"))
        engine_label.grid(row=1, column=2, padx=10, pady=5, sticky="e")
        
        self.engine_var = ctk.StringVar(value="Auto-Detect")
        engine_dropdown = ctk.CTkOptionMenu(
            settings_grid,
            variable=self.engine_var,
            values=["Auto-Detect", "Force yt-dlp", "Force JDownloader", "Force Playwright"],
            width=180
        )
        engine_dropdown.grid(row=1, column=3, padx=10, pady=5)
        
        # START DOWNLOAD button (moved here for visibility)
        self.start_btn = ctk.CTkButton(
            settings_grid,
            text="▶ START DOWNLOAD",
            command=self.start_download,
            width=200,
            height=40,
            fg_color="#00aa00",
            hover_color="#008800",
            font=("Arial", 14, "bold")
        )
        self.start_btn.grid(row=2, column=1, columnspan=2, padx=10, pady=5)
        
        # STOP button (also inline)
        self.stop_btn = ctk.CTkButton(
            settings_grid,
            text="⏹ STOP",
            command=self.stop_download,
            width=100,
            height=40,
            fg_color="#cc0000",
            hover_color="#aa0000",
            font=("Arial", 12, "bold"),
            state="disabled"
        )
        self.stop_btn.grid(row=0, column=4, padx=10, pady=5)
        
        # Drive API Toggle (NEW) - DEFAULT ENABLED
        drive_api_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        drive_api_frame.pack(pady=(5, 0), padx=10)
        
        self.drive_api_checkbox = ctk.CTkCheckBox(
            drive_api_frame,
            text="📤 Upload via Google Drive API (for shared folders)",
            font=("Arial", 11),
            command=self.toggle_drive_api
        )
        self.drive_api_checkbox.pack(side="left", padx=5)
        self.drive_api_checkbox.select()  # Check by default
        
        self.drive_api_status = ctk.CTkLabel(
            drive_api_frame,
            text="✅ API Mode: Downloads → Temp → Drive → Cleanup",
            font=("Arial", 9),
            text_color="#00ff00"
        )
        self.drive_api_status.pack(side="left", padx=10)
        
        # Set initial state
        self.use_drive_api_var = True
    
    def create_console_section(self):
        """Create live console log"""
        console_frame = ctk.CTkFrame(self)
        console_frame.pack(pady=5, padx=20, fill="both", expand=True)
        
        label = ctk.CTkLabel(console_frame, text="Console Log:", font=("Arial", 13, "bold"))
        label.pack(anchor="w", padx=10, pady=(10, 5))
        
        self.console = ctk.CTkTextbox(
            console_frame,
            height=200,
            font=("Consolas", 9),
            state="disabled",
            border_width=2
        )
        self.console.pack(padx=10, pady=(0, 10), fill="both", expand=True)
        
        # Add initial welcome message
        self.log("=" * 80)
        self.log("OmniStream Archiver - Ready")
        self.log(f"Storage: {self.base_path}")
        self.log("=" * 80)
    
    def create_progress_section(self):
        """Create progress indicators"""
        progress_frame = ctk.CTkFrame(self)
        progress_frame.pack(pady=5, padx=20, fill="x")
        
        # Overall progress
        overall_label = ctk.CTkLabel(progress_frame, text="Overall Progress:", font=("Arial", 11, "bold"))
        overall_label.pack(anchor="w", padx=10, pady=(10, 2))
        
        self.overall_progress = ctk.CTkProgressBar(progress_frame, width=500, height=20)
        self.overall_progress.pack(padx=10, pady=(0, 5))
        self.overall_progress.set(0)
        
        self.overall_label = ctk.CTkLabel(
            progress_frame,
            text="Ready to download",
            font=("Arial", 10)
        )
        self.overall_label.pack(padx=10, pady=(0, 5))
        
        # Current file progress
        current_label = ctk.CTkLabel(progress_frame, text="Current File:", font=("Arial", 11, "bold"))
        current_label.pack(anchor="w", padx=10, pady=(5, 2))
        
        self.current_progress = ctk.CTkProgressBar(progress_frame, width=500, height=15)
        self.current_progress.pack(padx=10, pady=(0, 5))
        self.current_progress.set(0)
        
        self.current_label = ctk.CTkLabel(
            progress_frame,
            text="No active download",
            font=("Arial", 9)
        )
        self.current_label.pack(padx=10, pady=(0, 10))
    
    def create_control_section(self):
        """Create control buttons"""
        control_frame = ctk.CTkFrame(self, fg_color="transparent")
        control_frame.pack(pady=15)
        
        self.start_btn = ctk.CTkButton(
            control_frame,
            text="▶ START DOWNLOAD",
            command=self.start_download,
            width=220,
            height=45,
            fg_color="#00aa00",
            hover_color="#008800",
            font=("Arial", 15, "bold")
        )
        self.start_btn.pack(side="left", padx=10)
        
        self.stop_btn = ctk.CTkButton(
            control_frame,
            text="⏹ STOP",
            command=self.stop_download,
            width=220,
            height=45,
            fg_color="#cc0000",
            hover_color="#aa0000",
            font=("Arial", 15, "bold"),
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=10)
    
    def create_status_bar(self):
        """Create bottom status bar"""
        status_frame = ctk.CTkFrame(self, height=30)
        status_frame.pack(side="bottom", fill="x", padx=5, pady=5)
        
        self.status_text = ctk.CTkLabel(
            status_frame,
            text="Ready",
            font=("Arial", 10),
            anchor="w"
        )
        self.status_text.pack(side="left", padx=10)
    
    def check_jdownloader_status(self):
        """Check if JDownloader is running"""
        self.jdownloader_engine = JDownloaderEngine(self.base_path, self.log)
        
        if self.jdownloader_engine.jd_connected:
            self.jd_status.configure(text="📦 JDownloader: Connected", text_color="#00ff00")
        else:
            self.jd_status.configure(text="📦 JDownloader: Not Running", text_color="#ff6600")
    
    def log(self, message: str, level: str = "INFO"):
        """Add message to console with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color coding
        color_map = {
            "INFO": "white",
            "SUCCESS": "#00ff00",
            "WARNING": "#ffaa00",
            "ERROR": "#ff0000"
        }
        color = color_map.get(level, "white")
        
        formatted = f"[{timestamp}] [{level}] {message}\n"
        
        self.console.configure(state="normal")
        self.console.insert("end", formatted)
        self.console.see("end")
        self.console.configure(state="disabled")
        
        # Also update status bar
        self.status_text.configure(text=message[:100])
    
    def paste_url(self):
        """Paste from clipboard"""
        try:
            clipboard_text = self.clipboard_get()
            current_text = self.url_entry.get("1.0", "end").strip()
            if current_text:
                self.url_entry.insert("end", "\n" + clipboard_text)
            else:
                self.url_entry.insert("1.0", clipboard_text)
            self.log("URLs pasted from clipboard")
        except Exception as e:
            self.log(f"Failed to paste: {str(e)}", "ERROR")
    
    def clear_input(self):
        """Clear URL input"""
        self.url_entry.delete("1.0", "end")
        self.log("Input cleared")
    
    def start_download(self):
        """Start download process"""
        urls = self.url_entry.get("1.0", "end").strip().split("\n")
        urls = [url.strip() for url in urls if url.strip()]
        
        if not urls:
            self.log("No URLs provided", "ERROR")
            return
        
        self.is_downloading = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        
        # Start download in background thread
        self.download_thread = threading.Thread(
            target=self.download_worker,
            args=(urls,)
        )
        self.download_thread.start()
    
    def parse_ai_command(self):
        """Parse natural language command with AI and AUTO-START download"""
        
        command = self.ai_command_input.get("1.0", "end-1c").strip()
        
        if not command:
            self.log("⚠️ No command entered", "WARNING")
            return
        
        self.log(f"🤖 Parsing command: {command}", "INFO")
        
        # Detect URL from command
        import re
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, command)
        detected_url = urls[0] if urls else None
        
        # Parse with AI
        try:
            config = self.ai_parser.parse_command(command, detected_url)
            
            confidence = config.get('confidence', 0)
            interpretation = config.get('interpretation', 'Unknown')
            
            self.log(f"📊 Confidence: {confidence}%", "INFO")
            self.log(f"💡 Interpretation: {interpretation}", "INFO")
            
            # Apply configuration to UI
            if config.get('url'):
                self.url_input.delete("1.0", "end")
                self.url_input.insert("1.0", config['url'])
            
            # Set content type (mode)
            content_type = config.get('content_type', 'All Videos')
            if 'Shorts' in content_type:
                self.mode_var.set("Shorts Only (Vertical Filter)")
            elif 'Audio' in content_type:
                self.mode_var.set("Audio Only (MP3)")
            else:
                self.mode_var.set("All Videos (Best Quality)")
            
            # Set max downloads
            if config.get('count'):
                self.max_downloads_entry.delete(0, "end")
                self.max_downloads_entry.insert(0, str(config['count']))
            
            # Set quality
            quality = config.get('quality', 'Best Available')
            self.quality_var.set(quality)
            
            # Show success
            self.log(f"✅ Configuration applied!", "SUCCESS")
            
            # 🚀 AUTO-START DOWNLOAD if confidence is high enough
            if confidence >= 70 and config.get('url'):
                self.log(f"🚀 Auto-starting download (confidence: {confidence}%)", "SUCCESS")
                # Wait a moment for UI to update
                self.after(500, self.start_download)
            else:
                if confidence < 70:
                    self.log(f"⚠️ Low confidence ({confidence}%) - please review settings and click START manually", "WARNING")
                if not config.get('url'):
                    self.log(f"⚠️ No URL detected - please paste URL and click START", "WARNING")
        
        except Exception as e:
            self.log(f"❌ AI parsing failed: {str(e)}", "ERROR")
            self.log(f"💡 Try using manual settings instead", "INFO")
    
    def show_interpretation(self, config: dict):
        """Display AI interpretation results"""
        if not hasattr(self, 'interpretation_frame'):
            return
        
        # Show interpretation frame
        self.interpretation_frame.pack(pady=5, padx=20, fill="x", after=self.url_entry.master)
        
        # Build interpretation text
        interpretation = f"🎯 {config.get('interpretation', 'Parsed successfully')}\n\n"
        interpretation += f"📊 Confidence: {config.get('confidence', 0)}%\n"
        
        if config.get('url'):
            interpretation += f"🔗 URL: {config['url']}\n"
        if config.get('content_type'):
            interpretation += f"📹 Content: {config['content_type']}\n"
        if config.get('quality'):
            interpretation += f"🎨 Quality: {config['quality']}\n"
        if config.get('max_downloads'):
            interpretation += f"📦 Count: {config['max_downloads']} videos\n"
        if config.get('date_from') or config.get('date_to'):
            interpretation += f"📅 Date Range: {config.get('date_from', 'any')} to {config.get('date_to', 'now')}\n"
        
        if config.get('warnings'):
            interpretation += f"\n⚠️ Warnings:\n"
            for warning in config['warnings']:
                interpretation += f"  • {warning}\n"
        
        if config.get('ambiguities'):
            interpretation += f"\n❓ Ambiguities:\n"
            for amb in config['ambiguities']:
                interpretation += f"  • {amb}\n"
        
        # Update text
        self.interpretation_text.configure(state="normal")
        self.interpretation_text.delete("1.0", "end")
        self.interpretation_text.insert("1.0", interpretation)
        self.interpretation_text.configure(state="disabled")
        
        confidence = config.get('confidence', 0)
        self.log(f"✓ AI parsed with {confidence}% confidence", "SUCCESS")
        
        # Apply configuration to UI
        url = config.get('url')
        if url:
            # Fill URL field
            self.url_entry.delete("1.0", "end")
            self.url_entry.insert("1.0", url)
            self.log(f"📎 URL extracted: {url}", "INFO")
        
        # Set max downloads
        max_downloads = config.get('max_downloads') or config.get('count')
        if max_downloads:
            if hasattr(self, 'max_downloads_entry'):
                self.max_downloads_entry.delete(0, "end")
                self.max_downloads_entry.insert(0, str(max_downloads))
                self.log(f"📊 Max videos: {max_downloads}", "INFO")
        
        # Set mode based on content type
        content_type = config.get('content_type', 'All Videos')
        if 'Shorts' in content_type:
            self.mode_var.set("Shorts Only (Vertical Filter)")
            self.log(f"🎬 Mode: Shorts Only", "INFO")
        elif 'Audio' in content_type:
            self.mode_var.set("Audio Only (MP3)")
            self.log(f"🎵 Mode: Audio Only", "INFO")
        
        self.log("✓ AI configuration accepted", "SUCCESS")
        
        # 🚀 AUTO-START if confidence is good and URL is present
        if confidence >= 60 and url:
            self.log(f"🚀 Auto-starting download...", "SUCCESS")
            # Start download after a brief delay
            self.after(1000, self.start_download)
        elif not url:
            self.log("⚠️ No URL detected - please paste URL in the URL field", "WARNING")
        else:
            self.log(f"⚠️ Low confidence ({confidence}%) - review settings and click START manually", "WARNING")
    
    def detect_url_and_update_ui(self, event=None):
        """Detect URL and update UI dynamically"""
        url = self.url_entry.get("1.0", "end").strip()
        if not url:
            return
        
        # Detect site
        site_info = SiteDetector.detect_site(url)
        self.current_site_info = site_info
        
        # Update filters
        self.update_filters_for_site(site_info)
        
        self.log(f"Detected site: {site_info['icon']} {site_info['name']}")
    
    def update_filters_for_site(self, site_info: dict):
        """Update filter controls based on detected site"""
        if not hasattr(self, 'filters_frame'):
            return
        
        # Show filters frame
        self.filters_frame.pack(pady=5, padx=20, fill="x", before=self.console.master)
        
        # Update site info
        self.site_info_label.configure(
            text=f"{site_info['icon']} Detected: {site_info['name']} | Available: {', '.join(site_info['content_types'][:3])}"
        )
        
        # Clear existing controls
        for widget in self.filter_controls_frame.winfo_children():
            widget.destroy()
        
        # Create dynamic controls
        row = 0
        
        # Content Type (if site supports multiple)
        if len(site_info['content_types']) > 1:
            ctk.CTkLabel(
                self.filter_controls_frame,
                text="Content Type:",
                font=("Arial", 11, "bold")
            ).grid(row=row, column=0, padx=10, pady=5, sticky="e")
            
            self.content_type_var = ctk.StringVar(value=site_info['content_types'][0])
            ctk.CTkOptionMenu(
                self.filter_controls_frame,
                variable=self.content_type_var,
                values=site_info['content_types'],
                width=180
            ).grid(row=row, column=1, padx=10, pady=5, sticky="w")
            row += 1
        
        # Date Filter (if supported)
        if site_info['date_filter']:
            ctk.CTkLabel(
                self.filter_controls_frame,
                text="Date Range:",
                font=("Arial", 11, "bold")
            ).grid(row=row, column=0, padx=10, pady=5, sticky="e")
            
            date_frame = ctk.CTkFrame(self.filter_controls_frame, fg_color="transparent")
            date_frame.grid(row=row, column=1, padx=10, pady=5, sticky="w")
            
            self.date_from_var = ctk.StringVar()
            ctk.CTkEntry(
                date_frame,
                textvariable=self.date_from_var,
                placeholder_text="From (YYYY-MM-DD or 'last week')",
                width=200
            ).pack(side="left", padx=2)
            
            self.date_to_var = ctk.StringVar()
            ctk.CTkEntry(
                date_frame,
                textvariable=self.date_to_var,
                placeholder_text="To (YYYY-MM-DD or 'today')",
                width=200
            ).pack(side="left", padx=2)
            row += 1
        
        # Max Downloads (for bulk operations)
        if site_info['bulk_support']:
            ctk.CTkLabel(
                self.filter_controls_frame,
                text="Max Downloads:",
                font=("Arial", 11, "bold")
            ).grid(row=row, column=0, padx=10, pady=5, sticky="e")
            
            self.max_downloads_var = ctk.StringVar()
            ctk.CTkEntry(
                self.filter_controls_frame,
                textvariable=self.max_downloads_var,
                placeholder_text="Leave empty for all",
                width=180
            ).grid(row=row, column=1, padx=10, pady=5, sticky="w")
    
    def accept_ai_config(self):
        """Accept AI configuration and proceed"""
        if not self.current_ai_config:
            return
        
        # Apply config to UI
        if self.current_ai_config.get('url'):
            self.url_entry.delete("1.0", "end")
            self.url_entry.insert("1.0", self.current_ai_config['url'])
        
        self.log("✓ AI configuration accepted", "SUCCESS")
        
        # Hide interpretation panel
        if hasattr(self, 'interpretation_frame'):
            self.interpretation_frame.pack_forget()
    
    def edit_ai_config(self):
        """Edit AI configuration manually"""
        self.log("Switching to manual configuration mode")
        
        # Hide interpretation panel
        if hasattr(self, 'interpretation_frame'):
            self.interpretation_frame.pack_forget()
        
        # Show filters
        if self.current_site_info:
            self.update_filters_for_site(self.current_site_info)
    
    def toggle_manual_mode(self):
        """Toggle between AI and manual mode"""
        if hasattr(self, 'filters_frame') and self.filters_frame.winfo_ismapped():
            self.filters_frame.pack_forget()
            self.log("Switched to AI mode")
        else:
            url = self.url_entry.get("1.0", "end").strip()
            if url:
                self.detect_url_and_update_ui()
            else:
                self.log("Please enter a URL first", "WARNING")
    
    def download_worker(self, urls: list):
        """Background worker for downloads"""
        total_urls = len(urls)
        self.log(f"Starting batch download: {total_urls} URL(s)")
        self.log("=" * 80)
        
        success_count = 0
        failed_count = 0
        
        for idx, url in enumerate(urls, 1):
            if not self.is_downloading:
                self.log("Download stopped by user", "WARNING")
                break
            
            # Update overall progress
            progress = (idx - 1) / total_urls
            self.overall_progress.set(progress)
            self.overall_label.configure(text=f"Processing {idx}/{total_urls}")
            
            self.log(f"\n[{idx}/{total_urls}] Processing: {url}")
            
            # Choose engine
            if self.engine_var.get() == "Auto-Detect":
                engine_choice = EngineRouter.choose_engine(url)
            elif self.engine_var.get() == "Force yt-dlp":
                engine_choice = "yt-dlp"
            elif self.engine_var.get() == "Force JDownloader":
                engine_choice = "jdownloader"
            else:  # Force Playwright
                engine_choice = "playwright"
            
            self.log(f"Selected engine: {engine_choice.upper()}")
            
            # Create organized folder
            output_path = self.create_organized_folder(url)
            self.log(f"Output directory: {output_path}")
            
            # Execute download with selected engine
            success = False
            message = ""
            
            try:
                if engine_choice == "yt-dlp":
                    engine = YtDlpEngine(
                        output_path,
                        self.update_progress,
                        self.log,
                        use_drive_api=self.use_drive_api_var
                    )
                    quality = self.get_quality_mapping()
                    
                    # Get max downloads if specified
                    max_downloads = None
                    try:
                        max_text = self.max_downloads_entry.get().strip()
                        if max_text:
                            max_downloads = int(max_text)
                    except:
                        pass
                    
                    # Determine mode
                    if 'Shorts Only' in self.mode_var.get():
                        mode = 'shorts_only'
                    elif 'Audio Only' in self.mode_var.get():
                        mode = 'audio'
                    else:
                        # Default: All Videos (Best Quality) - no filtering
                        mode = 'video'
                    
                    success, message = engine.download(url, quality, mode, max_downloads)
                
                elif engine_choice == "jdownloader":
                    if not self.jdownloader_engine:
                        self.jdownloader_engine = JDownloaderEngine(output_path, self.log)
                    
                    if self.jdownloader_engine.jd_connected:
                        success, message = self.jdownloader_engine.download(url)
                    else:
                        self.log("JDownloader not available, falling back to Playwright", "WARNING")
                        engine_choice = "playwright"
                
                if engine_choice == "playwright":
                    engine = PlaywrightEngine(output_path, self.log)
                    success, message = engine.download(url)
                
                if success:
                    self.log(f"✓ {message}", "SUCCESS")
                    success_count += 1
                else:
                    self.log(f"✗ {message}", "ERROR")
                    failed_count += 1
                    
            except Exception as e:
                self.log(f"✗ Unexpected error: {str(e)}", "ERROR")
                failed_count += 1
            
            # Reset current file progress
            self.current_progress.set(0)
            self.current_label.configure(text="Ready for next file")
        
        # Final summary
        self.log("=" * 80)
        self.log(f"Batch download complete: {success_count} succeeded, {failed_count} failed")
        self.log("=" * 80)
        
        self.overall_progress.set(1.0)
        self.overall_label.configure(text=f"Complete: {success_count}/{total_urls} successful")
        
        self.reset_ui()
    
    def create_organized_folder(self, url: str) -> str:
        """Create organized folder based on URL"""
        # Detect platform
        url_lower = url.lower()
        
        if any(x in url_lower for x in ['youtube.com', 'youtu.be']):
            platform = 'YouTube'
        elif 'tiktok.com' in url_lower:
            platform = 'TikTok'
        elif 'instagram.com' in url_lower:
            platform = 'Instagram'
        elif 'twitter.com' in url_lower or 'x.com' in url_lower:
            platform = 'Twitter'
        elif any(x in url_lower for x in EngineRouter.FILE_HOSTS):
            platform = 'FileHosts'
        else:
            domain = urlparse(url).netloc.replace('www.', '')
            platform = f"Generic_Sites/{domain}"
        
        # Create platform folder (NO date-based subfolders)
        folder_path = os.path.join(self.base_path, platform)
        os.makedirs(folder_path, exist_ok=True)
        
        return folder_path
    
    def get_quality_mapping(self) -> str:
        """Map UI quality selection to engine format"""
        quality_map = {
            "Best Available": "best",
            "1080p": "1080p",
            "720p": "720p",
            "480p": "480p",
            "Audio Only": "audio"
        }
        return quality_map.get(self.quality_var.get(), "best")
    
    def update_progress(self, data: dict):
        """Update progress bar from engine callback"""
        try:
            percentage_str = data.get('percentage', '0%').replace('%', '').strip()
            percentage = float(percentage_str) / 100
            
            self.current_progress.set(percentage)
            self.current_label.configure(
                text=f"{data.get('filename', 'Unknown')} - Speed: {data.get('speed', 'N/A')} | ETA: {data.get('eta', 'N/A')}"
            )
        except:
            pass
    
    def stop_download(self):
        """Stop download process"""
        self.is_downloading = False
        self.log("Stopping downloads...", "WARNING")
        self.stop_btn.configure(state="disabled")
    
    def reset_ui(self):
        """Reset UI after downloads complete"""
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.current_progress.set(0)
        self.current_label.configure(text="No active download")
        self.is_downloading = False
    
    def toggle_drive_api(self):
        """Toggle Google Drive API mode"""
        self.use_drive_api_var = self.drive_api_checkbox.get()
        
        if self.use_drive_api_var:
            self.drive_api_status.configure(
                text="✅ API Mode: Downloads → Temp → Drive → Cleanup",
                text_color="#00ff00"
            )
            self.log("📤 Drive API mode enabled - uploads will go directly to shared folder", "SUCCESS")
        else:
            self.drive_api_status.configure(
                text="",
                text_color="gray"
            )
            self.log("Local storage mode - files save to Google Drive mount", "INFO")


# Main application entry point
if __name__ == "__main__":
    app = OmniStreamApp()
    app.mainloop()
