"""Mistake log and due-today routes."""

from __future__ import annotations

from fastapi import APIRouter

from ..core.config import COURSES_ROOT
from ..core.runner import python_script, run_script

router = APIRouter(tags=["mistakes"])


@router.get("/due-today")
def due_today(subject: str | None = None) -> dict:
    cmd = python_script("due_today.py", str(COURSES_ROOT), "--json")
    if subject:
        cmd.extend(["--subject", subject])
    return run_script(cmd)
