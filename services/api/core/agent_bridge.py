"""Bridge to StudyReviewOrchestrator."""

from __future__ import annotations

from pathlib import Path

from agent.orchestrator import run  # noqa: E402


def run_agent(course_path: Path, message: str, goal: str = "pass") -> dict:
    return run(course_path, message, goal)
