---
trigger: always_on
---

# OmniStream Archiver - Golden Rules & Architectural Principles

## CORE ARCHITECTURE PRINCIPLES

### Rule 1: Direct-Stream Priority
* ALWAYS write downloads directly to the Google Drive mount point when detected
* NEVER download to local storage first and then upload (double-handling forbidden)
* If Google Drive is unavailable, use minimal local temp storage with clear cleanup
* Streaming efficiency is non-negotiable - optimize for single-pass data flow

### Rule 2: Engine Selection Intelligence
* yt-dlp is PRIMARY engine for all video/audio platforms (YouTube, TikTok, Instagram, etc.)
* JDownloader is SECONDARY engine for file hosting services (Mega, MediaFire, etc.)
* Playwright is FALLBACK engine for any site not supported by primary/secondary
* ALWAYS attempt engines in this order: yt-dlp → JDownloader → Playwright
* Cache successful engine choices per domain for future optimization

### Rule 3: Zero Configuration by Default
* Application MUST work immediately after launch with sensible defaults
* Auto-detect Google Drive mount points without user configuration
* Auto-detect cookies from browsers automatically
* Only ask users for input when absolutely necessary
* Provide smart defaults for quality, format, and organization

## ANTI-DETECTION & STEALTH

### Rule 4: Human-Like Behavior is Mandatory
* ALWAYS implement random delays between requests (3-15 seconds minimum)
* NEVER make concurrent requests to the same domain
* Rotate user agents using fake_useragent library for every request session
* Implement exponential backoff on rate limiting (2x delay after each 429 error)
* Session management: create fresh sessions every 10-15 downloads

### Rule 5: Cookie Management Excellence
* Auto-detect cookies.txt in application directory on every launch
* Support browser cookie extraction (Chrome, Firefox, Edge, Safari)
* Never store credentials in plaintext
* Provide clear instructions when authentication is required
* Handle expired sessions gracefully with user notification

### Rule 6: Stealth Configuration Hierarchy
* Site-specific stealth profiles override global settings
* High-risk sites (Instagram, TikTok) default to maximum stealth
* Low-risk sites (YouTube, Vimeo) use moderate stealth for speed
* Allow user override but warn about detection risks
* Log all detection warnings for user awareness

## FILE ORGANIZATION & STORAGE

### Rule 7: Intelligent Folder Structure
* Default structure: [Drive]/OmniDownloads/[Platform]/[Creator]/[Year-Month]/
* ALWAYS sanitize folder names (remove special characters, limit length)
* Handle duplicate names intelligently (append counter, not random strings)
* Preserve original upload dates in folder organization when available
* Create parent directories automatically with appropriate permissions

### Rule 8: Metadata Preservation
* ALWAYS save original metadata alongside downloaded content
* Include: source URL, download date, original filename, creator info
* Store metadata in sidecar files (.json format) for each download
* Generate metadata index file for entire archive
* Never lose source information - traceability is critical

### Rule 9: Storage Management
* Monitor available space before starting downloads
* Warn user if storage will be exceeded
* Implement cleanup policies for failed/incomplete downloads
* Never leave orphaned temp files
* Provide storage usage analytics and recommendations

## ERROR HANDLING & RELIABILITY

### Rule 10: Graceful Failure Recovery
* NEVER crash the application on download failures
* Implement retry logic: 3 attempts with exponential backoff
* Log detailed error information for troubleshooting
* Provide actionable error messages to users (not generic exceptions)
* Continue processing queue even if individual items fail

### Rule 11: Network Resilience
* Handle connection drops gracefully with auto-resume
* Implement timeout management (connection: 30s, read: 300s)
* Detect and adapt to throttling automatically
* Support pause/resume for all download operations
* Maintain queue state across application restarts

### Rule 12: Data Integrity
* Verify file completeness after every download
* Implement checksum validation when available
* Detect corrupted downloads and auto-retry
* Never report success for incomplete downloads
* Quarantine failed downloads for manual inspection

## USER EXPERIENCE & INTERFACE

### Rule 13: Real-Time Transparency
* Show live progress for every operation
* Display which engine is handling each URL
* Provide detailed console logging in UI
* Show current file, speed, ETA, and completion percentage
* Never leave user guessing about system status

### Rule 14: Responsive Controls
* All UI buttons MUST respond within 200ms
* Implement threaded operations - never block the UI
* Allow cancellation of any operation within 1 second
* Provide immediate visual feedback for all actions
* Support keyboard shortcuts for power users

### Rule 15: Progressive Disclosure
* Show simple interface by default
* Advanced options available but not prominent
* Provide tooltips and contextual help
* Never overwhelm users with technical details
* Expert mode available but opt-in only

## CODE QUALITY & MAINTENANCE

### Rule 16: Modular Architecture
* Each engine (yt-dlp, JDownloader, Playwright) in separate module
* Clear separation: UI layer, business logic, download engines, storage
* No circular dependencies between modules
* Each module independently testable
* Follow single responsibility principle strictly

### Rule 17: Comprehensive Logging
* Log all operations with timestamp, severity, and context
* Separate log files: application.log, downloads.log, errors.log
* Implement log rotation (max 10MB per file, keep 5 historical)
* Never log sensitive information (passwords, tokens)
* Provide debug mode for troubleshooting

### Rule 18: Configuration Management
* All settings in central configuration file (config.json)
* Support configuration backup/restore
* Validate configuration on load with schema
* Provide configuration reset to defaults
* Never hardcode paths or settings in code

## PERFORMANCE & SCALABILITY

### Rule 19: Resource Management
* Limit concurrent downloads (default: 3, configurable)
* Monitor CPU and memory usage
* Implement bandwidth throttling options
* Clean up resources immediately after use
* Never leak file handles or network connections

### Rule 20: Queue Optimization
* Prioritize small files for quick wins
* Group downloads by domain for efficiency
* Implement smart scheduling (peak/off-peak awareness)
* Support batch processing with progress aggregation
* Allow manual queue reordering

## SECURITY & PRIVACY

### Rule 21: User Privacy First
* Never send user data to external services (except target sites)
* No telemetry or analytics without explicit consent
* Store all sensitive data encrypted at rest
* Clear session data on application close
* Provide privacy mode for sensitive downloads

### Rule 22: Safe Defaults
* Always validate and sanitize user inputs
* Block execution of downloaded files automatically
* Warn users about executable content
* Implement safe file type whitelist
* Sandbox Playwright operations

## DOCUMENTATION & SUPPORT

### Rule 23: Self-Documenting Code
* All functions must have clear docstrings
* Complex logic must include inline comments
* Configuration options documented in-app
* Error messages include troubleshooting steps
* Provide example usage in README

### Rule 24: User-Friendly Documentation
* README must include step-by-step setup for all platforms
* Include troubleshooting section for common issues
* Provide site-specific configuration examples
* Document all command-line options
* Include FAQ section based on user needs

## PLATFORM COMPATIBILITY

### Rule 25: Cross-Platform Excellence
* Test on Windows, macOS, and Linux before release
* Handle path separators correctly (os.path.join always)
* Detect platform-specific features gracefully
* Provide platform-specific instructions when needed
* Never assume a single platform environment

## TESTING & VALIDATION

### Rule 26: Test Before Deploy
* Every feature must include error case testing
* Test with various site types and edge cases
* Validate Google Drive integration thoroughly
* Test network failure scenarios
* Verify cleanup operations work correctly

### Rule 27: Real-World Validation
* Test with actual sites, not just mocks
* Verify anti-detection effectiveness regularly
* Test with different network conditions
* Validate with large files (5GB+)
* Confirm long-running stability (24+ hours)

## CONTINUOUS IMPROVEMENT

### Rule 28: Learn and Adapt
* Log successful strategies per site
* Build site profile database from experience
* Update anti-detection patterns as needed
* Monitor success/failure rates per engine
* Implement feedback loop for optimization

### Rule 29: Stay Updated
* Check for yt-dlp updates weekly
* Monitor for site structure changes
* Update user agents periodically
* Refresh browser cookie extraction methods
* Keep dependencies current with security patches

### Rule 30: User Feedback Integration
* Provide easy mechanism for user feedback
* Log feature requests automatically
* Prioritize issues affecting reliability
* Implement most-requested features first
* Maintain changelog for transparency
# Project Specification: Universal Downloader System ("OmniStream")

## 1. Project Overview
Build a local Python desktop application capable of downloading video and media from any URL. The application must feature a modern GUI, utilize a dual-engine architecture for maximum compatibility, and prioritize direct-to-cloud storage via Google Drive for Desktop.

## 2. Core Architecture
The system must use a "Dual-Engine" approach to handle different types of URLs:

### Engine A: The Video Streamer (`yt-dlp`)
* **Trigger:** Use this engine if the URL belongs to a known video platform (YouTube, TikTok, Vimeo, Twitch, Twitter/X).
* **Configuration:** * Enable `ignore-errors`.
    * Enable `geo-bypass`.
    * **Crucial:** Look for a `cookies.txt` file in the project root. If present, load it to authenticate (solves age-gating and premium content issues).
* **TikTok Specifics:** For TikTok URLs, ensure the filename format includes the Creator Name and Upload Date to prevent duplicates.

### Engine B: The Universal Scanner (`playwright`)
* **Trigger:** Use this engine for any URL *not* handled by Engine A (e.g., news sites, blogs, generic file hosts).
* **Logic:**
    1.  Launch Playwright (Headless Mode).
    2.  Navigate to the URL.
    3.  Sniff network traffic and DOM for media extensions (`.mp4`, `.m3u8`, `.pdf`, `.jpg`, `.png`).
    4.  Present a list of downloadable assets to the user in the GUI.

## 3. Smart Storage Logic (Google Drive Integration)
**Do not use the Google Drive API.** Instead, utilize the local file system paths created by "Google Drive for Desktop."

* **On Launch:** The app must check for the existence of the following paths in this order:
    1.  Mac: `/Volumes/GoogleDrive/My Drive/`
    2.  Windows: `G:/My Drive/` or `G:/`
* **If Found:** Set the base download path to `[Drive_Path]/OmniDownloads/`.
* **If Not Found:** Fallback to the local `~/Downloads/OmniDownloads/` folder.
* **Organization:** Inside the base folder, auto-create subfolders based on the Source:
    * `.../OmniDownloads/YouTube/[Channel_Name]/`
    * `.../OmniDownloads/TikTok/[Creator_Name]/`

## 4. Anti-Detection & Stealth Protocols
To prevent IP bans during bulk operations:
1.  **Random Pacing:** Implement a mandatory `random_sleep(min=4, max=12)` function between downloads when processing lists/channels.
2.  **Header Rotation:** Use the `fake-useragent` library to rotate User-Agent headers for every new request.
3.  **Browser Masquerade:** When using `yt-dlp`, strictly enforce the `--cookies-from-browser chrome` argument (if `cookies.txt` is missing) to mimic a real user session.

## 5. UI Requirements (`customtkinter`)
Create a modern, dark-mode GUI with the following ele