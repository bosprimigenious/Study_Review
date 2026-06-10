"""Run CLI scripts from API routes."""

from __future__ import annotations

import json
import subprocess
import sys

from fastapi import HTTPException

from .config import PROJECT_ROOT, SCRIPTS_DIR, SUBPROCESS_ENV


def run_script(cmd: list[str]) -> dict:
    """Execute a script and parse JSON stdout."""
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(PROJECT_ROOT),
        env=SUBPROCESS_ENV,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "Script failed").strip()
        raise HTTPException(status_code=500, detail=detail)
    stdout = (result.stdout or "").strip()
    if not stdout:
        return {}
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"Invalid JSON: {exc}") from exc


def python_script(script_name: str, *args: str) -> list[str]:
    return [sys.executable, str(SCRIPTS_DIR / script_name), *args]
