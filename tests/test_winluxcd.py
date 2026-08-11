import unittest

from winluxcd_app import shorten_path
from winluxcd_core import PathConversionError, convert_to_wsl


class PathConversionTests(unittest.TestCase):
    def test_drive_path(self):
        received = []

        def fake_runner(path):
            received.append(path)
            return "/mnt/c/Users/foo/My Docs"

        result = convert_to_wsl(r"C:\Users\foo\My Docs", fake_runner)
        self.assertEqual(["C:/Users/foo/My Docs"], received)
        self.assertEqual("/mnt/c/Users/foo/My Docs", result[0])
        self.assertEqual('cd "/mnt/c/Users/foo/My Docs"', result[1])

    def test_quotes_and_unc(self):
        result = convert_to_wsl(r"'D:\Projects\Project X'", lambda _: "/mnt/d/Projects/Project X")
        self.assertEqual("/mnt/d/Projects/Project X", result[0])
        self.assertEqual(("//server/share/folder", 'cd "//server/share/folder"'),
                         convert_to_wsl(r"\\server\share\folder", lambda _: "unused"))

    def test_wsl_passthrough_does_not_call_runner(self):
        result = convert_to_wsl("/home/user/Project X", lambda _: self.fail("runner called"))
        self.assertEqual("/home/user/Project X", result[0])

    def test_invalid_url_is_rejected(self):
        with self.assertRaisesRegex(PathConversionError, "auth.openai.com"):
            convert_to_wsl("https://auth.openai.com/oauth/authorize", lambda _: "unused")


class ShortenPathTests(unittest.TestCase):
    def test_short_path_is_unchanged(self):
        self.assertEqual(r"C:\Users\you\repo", shorten_path(r"C:\Users\you\repo"))

    def test_long_windows_path_keeps_tail(self):
        path = r"C:\Users\you\really\long\folder\chain\backend\app\settings.py"
        result = shorten_path(path, max_chars=40)
        self.assertTrue(result.startswith("…"))
        self.assertTrue(result.endswith(r"\backend\app\settings.py"))
        self.assertLessEqual(len(result), 40)
        self.assertNotIn("C:\\Users", result)

    def test_filename_always_visible(self):
        result = shorten_path(
            r"C:\Users\you\repo\backend\app\main.py", max_chars=24
        )
        self.assertTrue(result.endswith(r"\main.py"))
        self.assertLessEqual(len(result), 24)

    def test_single_component_longer_than_limit(self):
        result = shorten_path(
            r"C:\some\folder\a_very_long_filename_that_keeps_going.py",
            max_chars=16,
        )
        self.assertTrue(result.startswith("…"))
        self.assertTrue(result.endswith(".py"))
        self.assertLessEqual(len(result), 16)

    def test_wsl_path(self):
        result = shorten_path(
            "/home/user/projects/backend/app/settings.py", max_chars=30
        )
        self.assertTrue(result.startswith("…"))
        self.assertTrue(result.endswith("/app/settings.py"))
        self.assertIn("/", result)
        self.assertNotIn("\\", result)

    def test_never_exceeds_limit(self):
        for path in (
            r"C:\Users\you\repo\backend\app\settings.py",
            r"\\server\share\long\folder\chain\file.txt",
            "/home/user/projects/backend/app/settings.py",
            "short.py",
        ):
            with self.subTest(path=path):
                self.assertLessEqual(len(shorten_path(path, max_chars=25)), 25)


if __name__ == "__main__":
    unittest.main()
