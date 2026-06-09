#!/usr/bin/env python3
"""Print unchecked review-log lines due today or earlier."""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path


DUE_RE = re.compile(r"^- \[ \] (?P<due>\d{4}-\d{2}-\d{2})")
HEADING_RE = re.compile(r"^## (?P<heading>.+)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", nargs="?", default="复习记录.md")
    args = parser.parse_args()

    log_path = Path(args.log)
    if not log_path.exists():
        print(f"No review log found: {log_path}")
        return

    today = date.today()
    current_heading = ""
    found = False
    for line in log_path.read_text(encoding="utf-8").splitlines():
        heading = HEADING_RE.match(line)
        if heading:
            current_heading = heading.group("heading")
            continue
        due = DUE_RE.match(line)
        if due and date.fromisoformat(due.group("due")) <= today:
            found = True
            print(f"- {due.group('due')} | {current_heading}")

    if not found:
        print("No due items today.")


if __name__ == "__main__":
    main()
