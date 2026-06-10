#!/usr/bin/env python3
"""Unit tests for generate_questions field completeness (Epic 5-07)."""

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
GENERATE_SCRIPT = ROOT / "scripts" / "generate_questions.py"

REQUIRED_FIELDS = [
    "id",
    "course_id",
    "based_on_pattern_id",
    "source_materials",
    "question_type",
    "topic",
    "difficulty",
    "similarity",
    "label",
    "prompt",
    "expected_answer",
    "scoring_points",
    "time_limit_sec",
]


class TestGenerateQuestions(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.course = Path(self.tmp.name) / "computer-network"
        shutil.copytree(FIXTURE_SOURCE, self.course)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_five_questions_with_all_fields(self) -> None:
        r = subprocess.run(
            [
                sys.executable,
                str(GENERATE_SCRIPT),
                str(self.course),
                "--count",
                "5",
                "--force",
                "--json",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(r.returncode, 0, msg=r.stderr)

        payload = json.loads(r.stdout)
        self.assertEqual(payload["questions_count"], 5)

        generated = yaml.safe_load(
            (self.course / "review" / "generated-questions.yaml").read_text(
                encoding="utf-8"
            )
        )
        questions = generated["questions"]
        self.assertEqual(len(questions), 5)

        forbidden = ["押题", "必考", "命中", "预测"]
        for question in questions:
            for field in REQUIRED_FIELDS:
                self.assertIn(
                    field,
                    question,
                    f"Question {question.get('id', '?')} missing field: {field}",
                )
            self.assertGreaterEqual(
                len(question["scoring_points"]),
                2,
                f"Question {question['id']} has < 2 scoring_points",
            )
            self.assertIn(
                question["label"],
                ("模拟题", "变式题"),
                f"Question {question['id']} label is: {question['label']}",
            )
            combined = (
                question["prompt"]
                + question.get("expected_answer", "")
                + " ".join(question["scoring_points"])
            )
            for word in forbidden:
                self.assertNotIn(
                    word,
                    combined,
                    f"Question {question['id']} contains forbidden word: {word}",
                )


if __name__ == "__main__":
    unittest.main()
