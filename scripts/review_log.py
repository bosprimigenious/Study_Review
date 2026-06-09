#!/usr/bin/env python3
"""Append structured study mistakes to a Markdown review log."""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path


INTERVALS = {
    "忘了": [0, 1],
    "困难": [1],
    "还行": [3],
    "很熟": [7],
}


def build_entry(subject: str, topic: str, question: str, mistake: str, correction: str, rating: str) -> str:
    today = date.today()
    offsets = INTERVALS.get(rating, [1, 3, 7])
    due_lines = "\n".join(f"- [ ] {(today + timedelta(days=offset)).isoformat()}" for offset in offsets)
    return f"""
## {today.isoformat()} - {subject}

### 知识点
- {topic}

### 原题/问题
{question}

### 我的错误
{mistake}

### 正确理解
{correction}

### 下次复查
{due_lines}
""".lstrip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", default="复习记录.md")
    parser.add_argument("--subject", required=True)
    parser.add_argument("--topic", required=True)
    parser.add_argument("--question", required=True)
    parser.add_argument("--mistake", required=True)
    parser.add_argument("--correction", required=True)
    parser.add_argument("--rating", choices=sorted(INTERVALS), default="困难")
    args = parser.parse_args()

    log_path = Path(args.log)
    entry = build_entry(args.subject, args.topic, args.question, args.mistake, args.correction, args.rating)
    with log_path.open("a", encoding="utf-8") as handle:
        if log_path.stat().st_size > 0:
            handle.write("\n")
        handle.write(entry)
    print(log_path)


if __name__ == "__main__":
    main()
