#!/usr/bin/env python3
"""Unit tests for due_today scanning and JSON output (Epic 5-03~5-05)."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DUE_SCRIPT = ROOT / "scripts" / "due_today.py"


class TestDueTodayMultiCourse(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        today = date.today().isoformat()
        future = (date.today() + timedelta(days=30)).isoformat()

        self.course_a = self.root / "course-a"
        (self.course_a / "review").mkdir(parents=True)
        cards_a = (
            "schema_version: 1\n"
            "cards:\n"
            "  - id: card-a-001\n"
            "    course_id: course-a\n"
            "    subject: 科目A\n"
            "    topic: test-topic-a\n"
            "    prompt: 问题A\n"
            "    answer: 答案A\n"
            "    schedule:\n"
            f'      due: "{today}"\n'
        )
        (self.course_a / "review" / "cards.yaml").write_text(cards_a, encoding="utf-8")

        self.course_b = self.root / "course-b"
        (self.course_b / "review").mkdir(parents=True)
        cards_b = (
            "schema_version: 1\n"
            "cards:\n"
            "  - id: card-b-001\n"
            "    course_id: course-b\n"
            "    subject: 科目B\n"
            "    topic: test-topic-b\n"
            "    prompt: 问题B\n"
            "    answer: 答案B\n"
            "    schedule:\n"
            f'      due: "{future}"\n'
        )
        (self.course_b / "review" / "cards.yaml").write_text(cards_b, encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_two_courses_only_a_shows(self) -> None:
        r = subprocess.run(
            [sys.executable, str(DUE_SCRIPT), str(self.root)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("course-a", r.stdout)
        self.assertIn("card-a-001", r.stdout)
        self.assertNotIn("card-b-001", r.stdout)

    def test_json_output(self) -> None:
        r = subprocess.run(
            [sys.executable, str(DUE_SCRIPT), str(self.root), "--json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(len(data["courses"]), 1)
        self.assertEqual(data["courses"][0]["course_id"], "course-a")

    def test_json_structure_keys(self) -> None:
        r = subprocess.run(
            [sys.executable, str(DUE_SCRIPT), str(self.root), "--json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        data = json.loads(r.stdout)
        course = data["courses"][0]
        self.assertIn("course_id", course)
        self.assertIn("name", course)
        self.assertIn("items", course)
        item = course["items"][0]
        self.assertIn("id", item)
        self.assertIn("topic", item)
        self.assertIn("prompt", item)
        self.assertIn("due", item)
        self.assertIn("source", item)

    def test_bad_yaml_tolerance(self) -> None:
        (self.course_b / "review" / "cards.yaml").write_text(
            "cards:\n  - [unclosed\n  - broken: *bad_alias\n",
            encoding="utf-8",
        )
        r = subprocess.run(
            [sys.executable, str(DUE_SCRIPT), str(self.root)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("card-a-001", r.stdout)
        self.assertIn("WARN", r.stderr)


if __name__ == "__main__":
    unittest.main()
