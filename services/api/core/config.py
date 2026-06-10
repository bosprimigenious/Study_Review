"""Shared API configuration."""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
DEFAULT_FIXTURES = (PROJECT_ROOT / "tests" / "fixtures").resolve()


def _resolve_courses_root() -> Path:
    """Always resolve to absolute path; fallback to bundled fixtures."""
    raw = os.environ.get("COURSES_ROOT", "").strip()
    if raw:
        candidate = Path(raw)
        if not candidate.is_absolute():
            candidate = (PROJECT_ROOT / candidate).resolve()
        else:
            candidate = candidate.resolve()
    else:
        candidate = DEFAULT_FIXTURES

    if candidate.exists():
        return candidate
    if DEFAULT_FIXTURES.exists():
        return DEFAULT_FIXTURES
    return candidate


COURSES_ROOT = _resolve_courses_root()

for path in (str(PROJECT_ROOT), str(SCRIPTS_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)

SUBPROCESS_ENV = {
    **os.environ,
    "COURSES_ROOT": str(COURSES_ROOT),
    "PYTHONIOENCODING": "utf-8",
    "PYTHONUTF8": "1",
}
