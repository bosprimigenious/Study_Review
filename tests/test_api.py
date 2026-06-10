"""API integration tests using TestClient."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
os.environ["COURSES_ROOT"] = str(PROJECT_ROOT / "tests" / "fixtures")

from services.api.app import app  # noqa: E402

client = TestClient(app)


class TestAPI(unittest.TestCase):
    def test_health(self) -> None:
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_list_courses(self) -> None:
        response = client.get("/courses")
        self.assertEqual(response.status_code, 200)
        self.assertIn("courses", response.json())

    def test_materials(self) -> None:
        response = client.get("/courses/computer-network/materials")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["course_id"], "computer-network")
        self.assertGreater(len(data["files"]), 0)

    def test_agent_run_make_plan(self) -> None:
        response = client.post(
            "/agent/run",
            params={
                "course_id": "computer-network",
                "message": "今晚怎么不挂科",
                "goal": "pass",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(data["intent"], ["make_plan", "start_review"])

    def test_agent_run_due_review(self) -> None:
        response = client.post(
            "/agent/run",
            params={
                "course_id": "computer-network",
                "message": "今天该复习什么",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["intent"], "due_review")

    def test_due_today(self) -> None:
        response = client.get("/due-today")
        self.assertEqual(response.status_code, 200)
        self.assertIn("courses", response.json())

    def test_start_session_and_answer(self) -> None:
        start = client.post(
            "/review-session/start",
            params={
                "course_id": "computer-network",
                "source": "generated",
                "limit": 1,
            },
        )
        self.assertEqual(start.status_code, 200)
        payload = start.json()
        session_id = payload["session_id"]
        answer = client.post(
            "/review-session/answer",
            params={"session_id": session_id, "answer": "拥塞控制面向网络"},
        )
        self.assertEqual(answer.status_code, 200)
        self.assertIn(answer.json()["verdict"], ["correct", "partial", "wrong"])
        self.assertTrue(answer.json().get("awaiting_rating"))

        rate = client.post(
            "/review-session/rate",
            params={"session_id": session_id, "rating": "还行"},
        )
        self.assertEqual(rate.status_code, 200)
        rate_data = rate.json()
        self.assertEqual(rate_data["rating"], "还行")
        self.assertIn("due", rate_data)

    def test_404_course(self) -> None:
        response = client.post(
            "/agent/run",
            params={"course_id": "nonexistent", "message": "开始复习"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("warnings", response.json())


if __name__ == "__main__":
    unittest.main()
