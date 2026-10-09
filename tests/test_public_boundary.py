"""Reject common accidental publication paths using synthetic, disposable files."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

module_path = Path(__file__).resolve().parents[1] / "scripts/check_public_boundary.py"
spec = importlib.util.spec_from_file_location("boundary", module_path)
boundary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(boundary)


class PublicBoundary(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "README.md").write_text("Reproducible cipher code and method notes.\n")

    def tearDown(self):
        self.temp.cleanup()

    def test_code_and_notes_allowed(self):
        (self.root / "checker.py").write_text("print('PASS')\n")
        self.assertEqual(boundary.check(self.root)["status"], "PASS")

    def test_media_submission_directory_rejected(self):
        (self.root / "press").mkdir()
        (self.root / "press/draft.md").write_text("Synthetic submission draft.\n")
        with self.assertRaises(ValueError):
            boundary.check(self.root)

    def test_archive_with_uninspected_contents_rejected(self):
        (self.root / "bundle.zip").write_bytes(b"synthetic archive placeholder")
        with self.assertRaises(ValueError):
            boundary.check(self.root)

    def test_mail_headers_rejected_in_renamed_text_file(self):
        (self.root / "result.md").write_text("From: reviewer@example.invalid\nSubject: synthetic test\n")
        with self.assertRaises(ValueError):
            boundary.check(self.root)

    def test_conversation_log_rejected(self):
        (self.root / "notes.txt").write_text("USER: synthetic private test message\n")
        with self.assertRaises(ValueError):
            boundary.check(self.root)

    def test_symlink_rejected(self):
        (self.root / "shortcut").symlink_to(self.root / "README.md")
        with self.assertRaises(ValueError):
            boundary.check(self.root)


if __name__ == "__main__":
    unittest.main()
