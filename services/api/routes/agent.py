"""POST /agent/run — natural language routing."""

from __future__ import annotations

from fastapi import APIRouter

from ..core.agent_bridge import run_agent
from ..core.config import COURSES_ROOT

router = APIRouter(tags=["agent"])


@router.post("/agent/run")
def agent_run(course_id: str, message: str, goal: str = "pass") -> dict:
    course_path = COURSES_ROOT / course_id
    if not course_path.exists():
        return {
            "intent": "init_course",
            "state_before": "EMPTY",
            "tool_called": None,
            "state_after": "EMPTY",
            "message": f"课程目录不存在：{course_path}。请先创建课程目录并放入课件。",
            "next_action": {"label": "创建课程目录", "intent": "init_course"},
            "artifacts": [],
            "warnings": ["course not found"],
        }
    return run_agent(course_path, message, goal)
