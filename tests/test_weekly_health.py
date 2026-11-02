"""Tests for the weekly health check's pure helpers (no network)."""

import unittest

from scripts import weekly_health as wh


class ScanAddedLinesTest(unittest.TestCase):
    def test_flags_and_masks_a_secret(self):
        patch = "+API = 'sk-ant-" + "a" * 30 + "'\n"
        findings = wh.scan_added_lines("app.py", patch)
        self.assertTrue(any("Anthropic key" in f for f in findings))
        self.assertFalse(any("a" * 30 in f for f in findings), "secret must be masked")

    def test_flags_an_absolute_local_path_in_any_case(self):
        findings = wh.scan_added_lines("README.md", "+See c:/Users/Kevin/OneDrive/notes\n")
        self.assertIn("absolute local path in `README.md`", findings)

    def test_flags_a_spanish_code_comment_only_in_code(self):
        patch = "+# Arregla el error de los catalogos para que no fallen\n"
        self.assertTrue(wh.scan_added_lines("tool.py", patch))
        self.assertEqual(wh.scan_added_lines("README.es.md", patch), [])

    def test_ignores_removed_lines_and_placeholder_database_urls(self):
        patch = "-old = 'sk-ant-" + "b" * 30 + "'\n+url = 'postgresql://user:password@localhost/db'\n"
        self.assertEqual(wh.scan_added_lines("config.py", patch), [])

    def test_english_comment_is_clean(self):
        self.assertEqual(wh.scan_added_lines("tool.py", "+# Fix the catalog so the tests pass\n"), [])


class RenderTest(unittest.TestCase):
    def test_clean_week_reads_green(self):
        text = wh.render([wh.RepoReport("CV", ci="green")], 8)
        self.assertIn("Everything is green and clean", text)


if __name__ == "__main__":
    unittest.main()
