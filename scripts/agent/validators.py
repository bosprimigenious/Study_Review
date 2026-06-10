"""Validate agent output before returning to user."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

LOCAL_SOURCE_PATTERNS = [
    "tests/fixtures",
    "计算机网络",
    "概率论",
    "毛概",
    "计组",
    "理论计算机",
]


def validate_agent_output(response: dict, course_snapshot: dict | None = None) -> list[str]:
    """Return list of warnings. Empty list = valid."""
    del course_snapshot
    warnings: list[str] = []

    for field in ["intent", "message", "next_action"]:
        if field not in response:
            warnings.append(f"Missing required field: {field}")

    message = response.get("message", "")
    suspicious = ["根据教材", "第X章说", "书上提到", "考试重点"]
    for pattern in suspicious:
        if pattern in message and not any(
            local in message for local in LOCAL_SOURCE_PATTERNS
        ):
            warnings.append(f"Message may contain unsourced claim: '{pattern}'")

    if response.get("tool_to_call") and response.get("should_call_tool"):
        valid_tools = [
            "init_course_review.py",
            "analyze_exam.py",
            "generate_questions.py",
            "plan_review.py",
            "review_session.py",
            "review_log.py",
            "due_today.py",
        ]
        tool = response.get("tool_to_call", "")
        if tool not in valid_tools:
            warnings.append(f"Tool not implemented: {tool}")

    return warnings
