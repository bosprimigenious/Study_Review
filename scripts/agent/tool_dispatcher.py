"""Dispatch agent intents to CLI scripts."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"


def dispatch(intent: str, course_dir: Path | None = None, **kwargs: Any) -> dict:
    """Run the appropriate CLI script and return structured result."""
    workspace = (
        str(course_dir.resolve())
        if course_dir is not None
        else str(PROJECT_ROOT / "tests" / "fixtures")
    )
    goal = kwargs.get("goal", "pass")

    intent_to_script: dict[str, list[str]] = {
        "init_course": [
            sys.executable,
            str(SCRIPTS_DIR / "init_course_review.py"),
            workspace,
        ],
        "analyze_exam": [
            sys.executable,
            str(SCRIPTS_DIR / "analyze_exam.py"),
            workspace,
            "--force",
        ],
        "generate_questions": [
            sys.executable,
            str(SCRIPTS_DIR / "generate_questions.py"),
            workspace,
            "--count",
            "5",
            "--force",
        ],
        "make_plan": [
            sys.executable,
            str(SCRIPTS_DIR / "plan_review.py"),
            workspace,
            "--minutes",
            "90",
            "--goal",
            goal,
            "--force",
        ],
        "start_review": [
            sys.executable,
            str(SCRIPTS_DIR / "review_session.py"),
            workspace,
            "--source",
            "generated",
            "--limit",
            "1",
            "--non-interactive",
            "--answer",
            "",
        ],
        "due_review": [
            sys.executable,
            str(SCRIPTS_DIR / "due_today.py"),
            str(PROJECT_ROOT / "tests" / "fixtures")
            if course_dir is None
            else str(course_dir.parent),
        ],
    }

    cmd = intent_to_script.get(intent)
    if not cmd:
        return {
            "error": f"No tool for intent: {intent}",
            "tool_called": None,
            "status": "unavailable",
        }

    if intent != "start_review":
        cmd.append("--json")

    env = {
        **os.environ,
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
    }
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        encoding="utf-8",
        errors="replace",
        env=env,
    )

    output: dict[str, Any] = {}
    if result.returncode == 0 and result.stdout.strip():
        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError:
            output = {"raw_output": result.stdout[:500]}

    script_name = Path(cmd[1]).name if len(cmd) > 1 else None
    return {
        "intent": intent,
        "tool_called": script_name,
        "status": "success" if result.returncode == 0 else "failed",
        "exit_code": result.returncode,
        "stderr": result.stderr[:500] if result.stderr else None,
        "output": output,
    }
