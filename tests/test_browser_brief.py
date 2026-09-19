"""No browser, clipboard, subprocess, or network access: all external calls are mocked."""

import importlib.util
from contextlib import redirect_stderr
import io
from pathlib import Path
import subprocess
import unittest
from unittest.mock import Mock


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("browser_brief", ROOT / "macos/karabiner/browser_brief.py")
brief = importlib.util.module_from_spec(spec)
spec.loader.exec_module(brief)
URL = "https://www.youtube.com/watch?v=abcdefghijk&list=test"


class BrowserBriefTests(unittest.TestCase):
    def setUp(self):
        self.errors = io.StringIO()
        redirect = redirect_stderr(self.errors)
        redirect.__enter__()
        self.addCleanup(redirect.__exit__, None, None, None)

    def test_transcript_and_full_dispatch(self):
        for mode, expected in (("transcript", ["/mock/brief", "-t", URL]),
                               ("full", ["/mock/brief", URL])):
            with self.subTest(mode=mode):
                run = Mock(side_effect=[subprocess.CompletedProcess([], 0, URL + "\n"),
                                        subprocess.CompletedProcess([], 0)])
                self.assertEqual(brief.main([mode], run=run, brief_path="/mock/brief"), 0)
                self.assertEqual(run.call_count, 2)
                self.assertEqual(run.call_args_list[0].args[0][:2], ["/usr/bin/osascript", "-e"])
                self.assertEqual(run.call_args_list[0].kwargs["timeout"], 10)
                run.assert_called_with(expected, check=False)

    def test_non_youtube_never_launches_brief(self):
        for url in ("", "secret clipboard text", "https://example.com/?youtube.com",
                    "https://youtube.com.evil.test/watch?v=id", "file:///etc/passwd",
                    "https://evil.test@youtube.com/watch", "https://youtube.com:bad/watch",
                    "https://youtube.com/watch\nother", "-t"):
            with self.subTest(url=url):
                run = Mock(return_value=subprocess.CompletedProcess([], 0, url))
                self.assertEqual(brief.main(["transcript"], run=run), 1)
                self.assertEqual(run.call_count, 1)

    def test_supported_youtube_urls(self):
        for url in (URL, "https://youtu.be/abcdefghijk", "https://m.youtube.com/watch?v=id",
                    "https://www.youtube.com/shorts/id"):
            self.assertTrue(brief.youtube_url(url))

    def test_browser_failure_never_launches_brief(self):
        for error in (subprocess.CalledProcessError(1, "osascript"),
                      subprocess.TimeoutExpired("osascript", 10), FileNotFoundError()):
            run = Mock(side_effect=error)
            self.assertEqual(brief.main(["full"], run=run), 1)
            self.assertEqual(run.call_count, 1)

    def test_invalid_mode_never_reads_browser(self):
        for args in ([], ["wrong"], ["full", "extra"]):
            run = Mock()
            self.assertEqual(brief.main(args, run=run), 2)
            run.assert_not_called()

    def test_brief_failure_is_propagated(self):
        run = Mock(side_effect=[subprocess.CompletedProcess([], 0, URL),
                                subprocess.CompletedProcess([], 7)])
        self.assertEqual(brief.main(["full"], run=run, brief_path="/mock/brief"), 7)


if __name__ == "__main__":
    unittest.main()
