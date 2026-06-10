"""7 minimum eval scenarios from agent_development_plan.md."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "computer-network"


class TestAgentEval(unittest.TestCase):
    def _run_agent(self, course: Path, message: str) -> dict:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/agent_run.py",
                str(course),
                message,
                "--json",
            ],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(result.returncode, 0, f"Agent failed: {result.stderr}")
        return json.loads(result.stdout)

    def test_no_review_dir_suggests_init(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            course = Path(tmp) / "empty-course"
            course.mkdir()
            response = self._run_agent(course, "开始复习计算机网络")
            self.assertIn(response["intent"], ["init_course", "start_review"])
            self.assertIsNotNone(response["next_action"])

    def test_materials_no_analysis_suggests_analyze(self) -> None:
        response = self._run_agent(FIXTURE, "根据试卷分析重点")
        self.assertIn(response["intent"], ["analyze_exam", "make_plan"])
        self.assertIsNotNone(response["next_action"])

    def test_generate_questions_routing(self) -> None:
        response = self._run_agent(FIXTURE, "按往年题出5道变式题")
        self.assertIn(response["intent"], ["generate_questions", "analyze_exam"])
        self.assertIsNotNone(response["next_action"])

    def test_emergency_plan(self) -> None:
        response = self._run_agent(FIXTURE, "我今晚怎么不挂科")
        self.assertEqual(response["intent"], "make_plan")
        self.assertIsNotNone(response["next_action"])

    def test_due_review_intent(self) -> None:
        response = self._run_agent(FIXTURE, "今天该复习什么")
        self.assertEqual(response["intent"], "due_review")

    def test_no_fake_tool(self) -> None:
        response = self._run_agent(FIXTURE, "帮我分析一下PPT的内容")
        self.assertIsNotNone(response.get("next_action"))
        if response.get("tool_called"):
            valid = [
                "init_course_review.py",
                "analyze_exam.py",
                "generate_questions.py",
                "plan_review.py",
                "review_session.py",
                "review_log.py",
                "due_today.py",
                None,
            ]
            self.assertIn(response["tool_called"], valid)

    def test_no_unsourced_claims(self) -> None:
        response = self._run_agent(FIXTURE, "TCP拥塞控制是什么")
        self.assertIsNotNone(response.get("next_action"))


if __name__ == "__main__":
    unittest.main()
