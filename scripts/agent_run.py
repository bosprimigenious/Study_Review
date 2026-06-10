#!/usr/bin/env python3
"""StudyReviewOrchestrator CLI entry point."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from agent.orchestrator import run  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Study Review Agent")
    parser.add_argument("course", help="Course directory path")
    parser.add_argument("message", help="Natural language request (Chinese)")
    parser.add_argument("--goal", choices=["pass", "score_high"], default="pass")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    course_path = Path(args.course).resolve()
    if not course_path.exists():
        print(f"Course not found: {course_path}", file=sys.stderr)
        raise SystemExit(1)

    response = run(course_path, args.message, args.goal)

    if args.json:
        print(json.dumps(response, ensure_ascii=False, indent=2))
    else:
        print(f"\n意图：{response['intent']}")
        print(f"状态：{response['state_before']} → {response['state_after']}")
        if response.get("tool_called"):
            print(f"工具：{response['tool_called']}")
        print(f"\n{response['message']}")
        if response.get("next_action"):
            print(f"\n下一步：{response['next_action']['label']}")
        if response.get("warnings"):
            print(f"\n⚠ {response['warnings']}")

    if response.get("warnings") and not response.get("tool_called"):
        has_blocking_warning = any(
            "failed" in warning.lower() or "not found" in warning.lower()
            for warning in response["warnings"]
        )
        if has_blocking_warning:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
