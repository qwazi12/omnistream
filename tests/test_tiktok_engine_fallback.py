"""
Smoke test for TikTokEngine._run_browser_fallback.

Uses unittest.mock to avoid any real network calls, Drive API,
or Playwright browser launches.

Patching strategy:
  - playwright_engine.PlaywrightEngine  — patched at the source module,
    because tiktok_engine does 'from playwright_engine import PlaywrightEngine'
    inside the function body.
  - tempfile.TemporaryDirectory         — patched at the standard library module
    because tiktok_engine does 'import tempfile' inside the function body.
  - os.listdir / shutil.copy            — patched at their stdlib modules.
"""

import sys
import os
import types
import unittest
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Stub out heavy optional packages so this test works without them installed
# ---------------------------------------------------------------------------

# Stub TikTokApi
tiktokapi_stub = types.ModuleType("TikTokApi")
tiktokapi_stub.TikTokApi = MagicMock()
sys.modules.setdefault("TikTokApi", tiktokapi_stub)

# Stub simple_drive so SimpleDriveAPI() doesn't try to authenticate
simple_drive_stub = types.ModuleType("simple_drive")
simple_drive_stub.SimpleDriveAPI = MagicMock(side_effect=Exception("no auth in test"))
sys.modules.setdefault("simple_drive", simple_drive_stub)

# Stub simple_downloader
simple_dl_stub = types.ModuleType("simple_downloader")
simple_dl_stub.SimplifiedDownloader = MagicMock()
sys.modules.setdefault("simple_downloader", simple_dl_stub)

# Stub playwright_engine at the module level so patch() can find it
pw_engine_stub = types.ModuleType("playwright_engine")
pw_engine_stub.PlaywrightEngine = MagicMock()
sys.modules.setdefault("playwright_engine", pw_engine_stub)

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from tiktok_engine import TikTokEngine  # noqa: E402


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_engine():
    """Build a TikTokEngine with Drive API disabled (no auth needed)."""
    engine = TikTokEngine.__new__(TikTokEngine)
    engine.folder_id = "FAKE_FOLDER_ID"
    engine.drive_api = None
    engine.downloader = MagicMock()
    return engine


def _make_tmpdir_ctx(path="/fake/tmp"):
    """Return a context manager that yields a fake temp-dir path."""
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=path)
    ctx.__exit__ = MagicMock(return_value=False)
    return ctx


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRunBrowserFallback(unittest.TestCase):

    # ------------------------------------------------------------------
    # Case 1: Playwright succeeds, mp4 file found → (True, "Saved locally")
    # ------------------------------------------------------------------
    @patch("playwright_engine.PlaywrightEngine")
    @patch("tempfile.TemporaryDirectory")
    @patch("os.listdir", return_value=["video_123.mp4"])
    @patch("shutil.copy")
    def test_playwright_success_file_found_returns_true(
        self, mock_copy, _mock_listdir, mock_tmpdir, MockPlaywright
    ):
        mock_tmpdir.return_value = _make_tmpdir_ctx()
        pw_instance = MagicMock()
        pw_instance.download.return_value = (True, "Downloaded OK")
        MockPlaywright.return_value = pw_instance

        success, msg = _make_engine()._run_browser_fallback(
            "https://www.tiktok.com/@testuser/video/123"
        )

        self.assertTrue(success)
        self.assertIn("saved locally", msg.lower())
        mock_copy.assert_called_once()   # file was moved out of temp dir

    # ------------------------------------------------------------------
    # Case 2: Playwright succeeds but NO mp4 in temp dir → (False, "File not found")
    # ------------------------------------------------------------------
    @patch("playwright_engine.PlaywrightEngine")
    @patch("tempfile.TemporaryDirectory")
    @patch("os.listdir", return_value=["something.txt"])  # no .mp4
    def test_playwright_success_no_file_returns_false(
        self, _mock_listdir, mock_tmpdir, MockPlaywright
    ):
        mock_tmpdir.return_value = _make_tmpdir_ctx()
        pw_instance = MagicMock()
        pw_instance.download.return_value = (True, "Downloaded OK")
        MockPlaywright.return_value = pw_instance

        success, msg = _make_engine()._run_browser_fallback(
            "https://www.tiktok.com/@testuser/video/456"
        )

        self.assertFalse(success)
        self.assertEqual(msg, "File not found")

    # ------------------------------------------------------------------
    # Case 3: Playwright fails → (False, reason)
    # ------------------------------------------------------------------
    @patch("playwright_engine.PlaywrightEngine")
    @patch("tempfile.TemporaryDirectory")
    def test_playwright_failure_returns_false(self, mock_tmpdir, MockPlaywright):
        mock_tmpdir.return_value = _make_tmpdir_ctx()
        pw_instance = MagicMock()
        pw_instance.download.return_value = (False, "Network error")
        MockPlaywright.return_value = pw_instance

        success, msg = _make_engine()._run_browser_fallback(
            "https://www.tiktok.com/@testuser/video/789"
        )

        self.assertFalse(success)
        self.assertEqual(msg, "Network error")

    # ------------------------------------------------------------------
    # Case 4: PlaywrightEngine import raises → (False, str(exception))
    # ------------------------------------------------------------------
    @patch("playwright_engine.PlaywrightEngine", side_effect=ImportError("playwright missing"))
    @patch("tempfile.TemporaryDirectory")
    def test_exception_returns_false(self, mock_tmpdir, _MockPW):
        mock_tmpdir.return_value = _make_tmpdir_ctx()

        success, msg = _make_engine()._run_browser_fallback(
            "https://www.tiktok.com/@testuser/video/999"
        )

        self.assertFalse(success)
        self.assertIn("playwright missing", msg)

    # ------------------------------------------------------------------
    # Case 5: Return type is always (bool, str)
    # ------------------------------------------------------------------
    @patch("playwright_engine.PlaywrightEngine")
    @patch("tempfile.TemporaryDirectory")
    @patch("os.listdir", return_value=[])
    def test_return_type_is_always_two_tuple(
        self, _mock_listdir, mock_tmpdir, MockPlaywright
    ):
        mock_tmpdir.return_value = _make_tmpdir_ctx()
        pw_instance = MagicMock()
        pw_instance.download.return_value = (True, "ok")
        MockPlaywright.return_value = pw_instance

        result = _make_engine()._run_browser_fallback(
            "https://www.tiktok.com/@testuser/video/000"
        )

        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], bool)
        self.assertIsInstance(result[1], str)


if __name__ == "__main__":
    unittest.main(verbosity=2)
