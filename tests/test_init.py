#!/usr/bin/env python3
"""Unit tests for init_course_review idempotency (Epic 5-01)."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INIT_SCRIPT = ROOT / "scripts" / "init_course_review.py"


class TestInitIdempotent(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.course = Path(self.tmp.name) / "test-course"
        self.course.mkdir()
        (self.course / "slides.pptx").touch()
        (self.course / "sample_exam.pdf").touch()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_double_init_no_overwrite(self) -> None:
        r1 = subprocess.run(
            [sys.executable, str(INIT_SCRIPT), str(self.course)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(r1.returncode, 0, msg=r1.stderr)
        progress_path = self.course / "review" / "progress.md"
        self.assertTrue(progress_path.exists())
        progress_content = progress_path.read_text(encoding="utf-8")

        r2 = subprocess.run(
            [sys.executable, str(INIT_SCRIPT), str(self.course)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(r2.returncode, 0, msg=r2.stderr)
        self.assertIn("skipped", r2.stdout.lower())
        self.assertEqual(progress_path.read_text(encoding="utf-8"), progress_content)

    def test_dry_run_no_write(self) -> None:
        r = subprocess.run(
            [sys.executable, str(INIT_SCRIPT), str(self.course), "--dry-run"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertFalse((self.course / "review").exists())


if __name__ == "__main__":
    unittest.main()
