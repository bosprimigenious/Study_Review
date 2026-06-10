#!/usr/bin/env python3
"""Phase 4 validation — full review chain on fixture or real course path."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
DEFAULT_COURSE = ROOT / "tests" / "fixtures" / "computer-network"
REPORT_PATH = ROOT / "tests" / "phase4_results.md"


def run_step(name: str, cmd: list[str]) -> tuple[int, float, str]:
    start = time.perf_counter()
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
    )
    elapsed = round(time.perf_counter() - start, 3)
    output = (result.stdout or "") + (result.stderr or "")
    return result.returncode, elapsed, output


def main() -> int:
    course = Path(os.environ.get("COURSE_PATH", str(DEFAULT_COURSE))).resolve()
    workspace = course.parent

    if not course.exists():
        print(f"Course path not found: {course}", file=sys.stderr)
        return 1

    steps = [
        ("init", [sys.executable, str(SCRIPTS / "init_course_review.py"), str(course), "--json"]),
        ("analyze", [sys.executable, str(SCRIPTS / "analyze_exam.py"), str(course), "--force", "--json"]),
        (
            "generate",
            [
                sys.executable,
                str(SCRIPTS / "generate_questions.py"),
                str(course),
                "--count",
                "5",
                "--force",
                "--json",
            ],
        ),
        (
            "plan",
            [
                sys.executable,
                str(SCRIPTS / "plan_review.py"),
                str(course),
                "--minutes",
                "90",
                "--goal",
                "pass",
                "--force",
                "--json",
            ],
        ),
        (
            "session",
            [
                sys.executable,
                str(SCRIPTS / "review_session.py"),
                str(course),
                "--source",
                "generated",
                "--limit",
                "1",
                "--non-interactive",
                "--answer",
                "拥塞控制面向网络避免过载",
            ],
        ),
        ("due", [sys.executable, str(SCRIPTS / "due_today.py"), str(workspace), "--json"]),
    ]

    results: list[dict] = []
    all_ok = True
    for name, cmd in steps:
        code, elapsed, output = run_step(name, cmd)
        ok = code == 0
        all_ok = all_ok and ok
        results.append(
            {
                "step": name,
                "exit_code": code,
                "seconds": elapsed,
                "pass": ok,
                "output_tail": output[-300:] if output else "",
            }
        )
        if not ok:
            print(f"FAILED {name}: {output}", file=sys.stderr)
            break

    report = {
        "date": date.today().isoformat(),
        "course_path": str(course),
        "mode": "real" if course != DEFAULT_COURSE.resolve() else "fixture",
        "all_pass": all_ok,
        "steps": results,
    }

    lines = [
        "# Phase 4 Validation Results",
        "",
        f"Date: {report['date']}",
        f"Course: `{course}`",
        f"Mode: **{report['mode']}**",
        "",
        "| Step | Exit | Seconds | Pass |",
        "|------|------|---------|------|",
    ]
    for item in results:
        lines.append(
            f"| {item['step']} | {item['exit_code']} | {item['seconds']} | {'PASS' if item['pass'] else 'FAIL'} |"
        )
    lines.extend(["", f"**Overall: {'PASS' if all_ok else 'FAIL'}**", "", "```json", json.dumps(report, ensure_ascii=False, indent=2), "```"])
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"all_pass": all_ok, "report": str(REPORT_PATH)}, ensure_ascii=False))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
