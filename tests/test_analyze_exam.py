#!/usr/bin/env python3
"""Unit tests for analyze_exam output schema (Epic 5-06)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_SOURCE = Path(__file__).parent / "fixtures" / "computer-network"
ANALYZE_SCRIPT = ROOT / "scripts" / "analyze_exam.py"


class TestAnalyzeExamOutput(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.course = Path(self.tmp.name) / "computer-network"
        shutil.copytree(FIXTURE_SOURCE, self.course)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_priorities_count_and_evidence(self) -> None:
        r = subprocess.run(
            [
                sys.executable,
                str(ANALYZE_SCRIPT),
                str(self.course),
                "--force",
                "--json",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        data = json.loads(r.stdout)
        self.assertGreaterEqual(data["priorities_count"], 3)
        self.assertIn("confidence", data)

        analysis = yaml.safe_load(
            (self.course / "review" / "exam-analysis.yaml").read_text(encoding="utf-8")
        )
        priorities = analysis["analysis"]["priorities"]
        self.assertGreaterEqual(len(priorities), 3)
        for priority in priorities:
            self.assertIn("evidence", priority)
            self.assertGreater(len(priority["evidence"]), 0)
            self.assertIn("weight", priority)
            self.assertIn("question_types", priority)


if __name__ == "__main__":
    unittest.main()
