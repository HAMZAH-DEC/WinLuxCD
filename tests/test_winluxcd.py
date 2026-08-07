import unittest

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


if __name__ == "__main__":
    unittest.main()
