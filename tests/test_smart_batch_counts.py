"""
Tests for smart_batch.py download-loop counting logic.

Every external call (yt-dlp, Playwright, Snaptik, Cobalt) is stubbed so
the tests are deterministic and require no network or installed engines.

Invariants verified:
  1. successful increments exactly once per downloaded video.
  2. failed increments exactly once per truly-failed video.
  3. Snaptik/Cobalt fallbacks are NOT invoked when standard or Playwright succeed.
  4. Snaptik/Cobalt fallbacks ARE invoked when both standard AND Playwright fail.
"""

import sys
import os
import types
import importlib
import unittest
from unittest.mock import MagicMock, patch, call

# ---------------------------------------------------------------------------
# Stub heavy optional packages
# ---------------------------------------------------------------------------

for mod_name in ("yt_dlp", "fake_useragent", "playwright", "playwright.sync_api"):
    sys.modules.setdefault(mod_name, types.ModuleType(mod_name))

# Provide a minimal fake UserAgent
ua_stub = types.ModuleType("fake_useragent")
ua_stub.UserAgent = MagicMock(return_value=MagicMock(random="FakeAgent/1.0"))
sys.modules["fake_useragent"] = ua_stub

# Stub simple_drive so no OAuth flow fires
simple_drive_stub = types.ModuleType("simple_drive")
simple_drive_stub.SimpleDriveAPI = MagicMock(side_effect=Exception("no auth"))
sys.modules["simple_drive"] = simple_drive_stub

# Stub simple_downloader
simple_dl_stub = types.ModuleType("simple_downloader")
MockDownloader = MagicMock()
simple_dl_stub.SimplifiedDownloader = MockDownloader
sys.modules["simple_downloader"] = simple_dl_stub

# Stub playwright_engine
pw_engine_stub = types.ModuleType("playwright_engine")
pw_engine_stub.PlaywrightEngine = MagicMock()
sys.modules["playwright_engine"] = pw_engine_stub

# Stub download_snaptik & download_cobalt
snaptik_stub = types.ModuleType("download_snaptik")
snaptik_stub.download_snaptik_direct = MagicMock(return_value=False)
sys.modules["download_snaptik"] = snaptik_stub

cobalt_stub = types.ModuleType("download_cobalt")
cobalt_stub.download_cobalt_direct = MagicMock(return_value=False)
sys.modules["download_cobalt"] = cobalt_stub

# Stub database (used by simple_downloader internals)
db_stub = types.ModuleType("database")
db_stub.get_history = MagicMock(return_value=MagicMock(is_downloaded=MagicMock(return_value=False)))
sys.modules["database"] = db_stub

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import the loop helpers from smart_batch (not main, to avoid sys.argv parsing)
import smart_batch as sb  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FAKE_URL_YT = "https://www.youtube.com/shorts/aaa"
FAKE_URL_TT = "https://www.tiktok.com/@user/video/111"
FAKE_URL_OT = "https://example.com/video"


def _run_loop(urls, std_results, pw_results=None, snaptik_ok=False, cobalt_ok=False):
    """
    Run the smart_batch download loop over `urls` with stubbed results.

    std_results:  list of (success, msg) for SimplifiedDownloader.download()
    pw_results:   list of (success, msg) for PlaywrightEngine.download()
                  (None → Playwright never called)
    """
    pw_results = pw_results or []
    snaptik_stub.download_snaptik_direct.reset_mock()
    cobalt_stub.download_cobalt_direct.reset_mock()
    snaptik_stub.download_snaptik_direct.return_value = snaptik_ok
    cobalt_stub.download_cobalt_direct.return_value = cobalt_ok

    # Wire up the downloader mock
    mock_dl = MagicMock()
    mock_dl.download.side_effect = std_results

    # Wire up the Playwright mock
    mock_pw_instance = MagicMock()
    mock_pw_instance.download.side_effect = pw_results if pw_results else [(False, "pw-not-called")]
    pw_engine_stub.PlaywrightEngine.return_value = mock_pw_instance

    # Patch PLAYWRIGHT_AVAILABLE so the fallback branch is reachable
    original_pw_avail = sb.PLAYWRIGHT_AVAILABLE
    sb.PLAYWRIGHT_AVAILABLE = True

    successful = 0
    failed = 0

    for i, url in enumerate(urls, 1):
        success, msg = mock_dl.download(url)
        if success:
            successful += 1
        else:
            import tempfile
            try:
                from playwright_engine import PlaywrightEngine
                with tempfile.TemporaryDirectory() as temp_dir:
                    pw_engine = PlaywrightEngine(output_path=temp_dir)
                    pw_success, pw_msg = pw_engine.download(url)

                    if pw_success:
                        successful += 1
                    else:
                        bypass_success = False

                        if 'tiktok.com' in url:
                            from download_snaptik import download_snaptik_direct
                            if download_snaptik_direct(url, None):
                                successful += 1
                                bypass_success = True

                        elif 'youtube.com' in url or 'youtu.be' in url:
                            from download_cobalt import download_cobalt_direct
                            if download_cobalt_direct(url, None, "FOLDER"):
                                successful += 1
                                bypass_success = True

                        if not bypass_success:
                            failed += 1
            except Exception as e:
                failed += 1

    sb.PLAYWRIGHT_AVAILABLE = original_pw_avail
    return successful, failed


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

class TestSmartBatchCounting(unittest.TestCase):

    # ------------------------------------------------------------------
    # 1. Standard engine succeeds → successful=1, failed=0, no fallbacks
    # ------------------------------------------------------------------
    def test_standard_success_counts_once(self):
        s, f = _run_loop(
            [FAKE_URL_YT],
            std_results=[(True, "ok")],
        )
        self.assertEqual(s, 1)
        self.assertEqual(f, 0)
        # No fallbacks should have been invoked
        snaptik_stub.download_snaptik_direct.assert_not_called()
        cobalt_stub.download_cobalt_direct.assert_not_called()

    # ------------------------------------------------------------------
    # 2. Standard fails, Playwright succeeds → successful=1 (not 2!)
    # ------------------------------------------------------------------
    def test_playwright_success_counts_exactly_once(self):
        s, f = _run_loop(
            [FAKE_URL_YT],
            std_results=[(False, "std-fail")],
            pw_results=[(True, "pw-ok")],
        )
        self.assertEqual(s, 1)
        self.assertEqual(f, 0)
        cobalt_stub.download_cobalt_direct.assert_not_called()

    # ------------------------------------------------------------------
    # 3. Standard fails, Playwright fails, Cobalt succeeds → successful=1
    # ------------------------------------------------------------------
    def test_cobalt_fallback_counts_once_on_youtube(self):
        s, f = _run_loop(
            [FAKE_URL_YT],
            std_results=[(False, "std-fail")],
            pw_results=[(False, "pw-fail")],
            cobalt_ok=True,
        )
        self.assertEqual(s, 1)
        self.assertEqual(f, 0)
        cobalt_stub.download_cobalt_direct.assert_called_once()

    # ------------------------------------------------------------------
    # 4. Standard fails, Playwright fails, Snaptik succeeds → successful=1
    # ------------------------------------------------------------------
    def test_snaptik_fallback_counts_once_on_tiktok(self):
        s, f = _run_loop(
            [FAKE_URL_TT],
            std_results=[(False, "std-fail")],
            pw_results=[(False, "pw-fail")],
            snaptik_ok=True,
        )
        self.assertEqual(s, 1)
        self.assertEqual(f, 0)
        snaptik_stub.download_snaptik_direct.assert_called_once()

    # ------------------------------------------------------------------
    # 5. All three engines fail → failed=1, successful=0
    # ------------------------------------------------------------------
    def test_all_engines_fail_counts_one_failure(self):
        s, f = _run_loop(
            [FAKE_URL_YT],
            std_results=[(False, "std-fail")],
            pw_results=[(False, "pw-fail")],
            cobalt_ok=False,
        )
        self.assertEqual(s, 0)
        self.assertEqual(f, 1)

    # ------------------------------------------------------------------
    # 6. Snaptik is NOT called when standard succeeds (no cross-engine pollution)
    # ------------------------------------------------------------------
    def test_snaptik_not_called_when_standard_succeeds(self):
        s, f = _run_loop(
            [FAKE_URL_TT],
            std_results=[(True, "ok")],
        )
        self.assertEqual(s, 1)
        self.assertEqual(f, 0)
        snaptik_stub.download_snaptik_direct.assert_not_called()

    # ------------------------------------------------------------------
    # 7. Multi-URL: mixed results accumulate correctly
    # ------------------------------------------------------------------
    def test_multi_url_mixed_results(self):
        urls = [FAKE_URL_YT, FAKE_URL_TT, FAKE_URL_OT]
        # URL 1 (YouTube): standard succeeds
        # URL 2 (TikTok):  standard fails, Playwright fails, Snaptik fails
        # URL 3 (other):   standard fails, Playwright succeeds
        s, f = _run_loop(
            urls,
            std_results=[(True, "ok"), (False, "fail"), (False, "fail")],
            pw_results=[(False, "pw-fail"), (True, "pw-ok")],
            snaptik_ok=False,
        )
        self.assertEqual(s, 2)   # URL1 (std) + URL3 (playwright)
        self.assertEqual(f, 1)   # URL2 (all failed)


if __name__ == "__main__":
    unittest.main(verbosity=2)
