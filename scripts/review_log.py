#!/usr/bin/env python3
"""Append structured study mistakes to course review/ workspace."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from review_io import (  # noqa: E402
    append_card,
    due_dates_from_rating,
    get_review_dir,
    load_cards,
    load_files_yaml,
    make_course_id,
    next_id,
)

RATINGS = ("忘了", "困难", "还行", "很熟")
DIFFICULTIES = ("basic", "medium", "hard")

_TAG_RULES: list[tuple[str, str]] = [
    ("混淆", "概念混淆"),
    ("区别", "概念混淆"),
    ("公式", "公式条件"),
    ("条件", "公式条件"),
    ("流程", "流程遗漏"),
    ("步骤", "流程遗漏"),
    ("握手", "流程遗漏"),
    ("计算", "计算错误"),
    ("子网", "计算错误"),
    ("没说", "表达不完整"),
    ("只说了", "表达不完整"),
    ("没说清楚", "表达不完整"),
    ("忘记", "记忆缺口"),
    ("没背", "记忆缺口"),
    ("没记", "记忆缺口"),
]


def _atomic_append_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = ""
    if path.exists() and path.stat().st_size > 0:
        existing = path.read_text(encoding="utf-8")
        if not existing.endswith("\n"):
            existing += "\n"
        existing += "\n"
    payload = f"{existing}{content}"
    fd, tmp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def infer_mistake_tags(mistake: str, topic: str, question: str) -> list[str]:
    text = f"{mistake} {topic} {question}"
    tags: list[str] = []
    for keyword, tag in _TAG_RULES:
        if keyword in text and tag not in tags:
            tags.append(tag)
    if not tags:
        tags.append("表达不完整")
    return tags


def resolve_course_id(review_dir: Path, subject: str, course_path: Path) -> str:
    files_data = load_files_yaml(review_dir)
    course = files_data.get("course")
    if isinstance(course, dict):
        course_id = course.get("course_id") or course.get("id")
        if course_id:
            return str(course_id)
    return make_course_id(course_path.name or subject)


def build_mistake_entry(
    subject: str,
    topic: str,
    question: str,
    mistake: str,
    correction: str,
    due_dates: list[date],
    tags: list[str],
    today: date,
) -> str:
    due_lines = "\n".join(f"- [ ] {due_day.isoformat()}" for due_day in due_dates)
    tag_lines = "\n".join(f"- {tag}" for tag in tags)
    return (
        f"## {today.isoformat()} - {subject}\n\n"
        f"### 知识点\n"
        f"- {topic}\n\n"
        f"### 原题/问题\n"
        f"{question}\n\n"
        f"### 我的错误\n"
        f"{mistake}\n\n"
        f"### 正确理解\n"
        f"{correction}\n\n"
        f"### 错因标签\n"
        f"{tag_lines}\n\n"
        f"### 下次复查\n"
        f"{due_lines}\n"
    )


def build_card_dict(
    card_id: str,
    course_id: str,
    subject: str,
    topic: str,
    question: str,
    correction: str,
    rating: str,
    due_dates: list[date],
    today: date,
    chapter: str | None,
    difficulty: str,
    tags: list[str],
    source: str | None,
) -> dict:
    schedule = {
        "rating": rating,
        "last_reviewed": today.isoformat(),
        "due": due_dates[0].isoformat(),
    }
    card = {
        "id": card_id,
        "course_id": course_id,
        "subject": subject,
        "topic": topic,
        "card_type": "mistake_review",
        "prompt": question,
        "answer": correction,
        "scoring_points": [],
        "difficulty": difficulty,
        "tags": tags,
        "schedule": schedule,
    }
    if chapter:
        card["chapter"] = chapter
    if source:
        card["source"] = {"file": source, "evidence": "mistake log"}
    return card


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--course", required=True, help="Course directory path")
    parser.add_argument("--subject", required=True)
    parser.add_argument("--topic", required=True)
    parser.add_argument("--question", required=True)
    parser.add_argument("--mistake", required=True)
    parser.add_argument("--correction", required=True)
    parser.add_argument("--rating", choices=RATINGS, default="困难")
    parser.add_argument("--chapter", default=None)
    parser.add_argument("--difficulty", choices=DIFFICULTIES, default="medium")
    parser.add_argument("--tags", default=None, help="Comma-separated tags")
    parser.add_argument("--source", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    course_path = Path(args.course)
    review_dir = get_review_dir(course_path)
    review_dir.mkdir(parents=True, exist_ok=True)

    today = date.today()
    due_dates = due_dates_from_rating(args.rating, today)
    tags = (
        [tag.strip() for tag in args.tags.split(",") if tag.strip()]
        if args.tags
        else infer_mistake_tags(args.mistake, args.topic, args.question)
    )

    cards_data = load_cards(review_dir)
    existing_ids = {
        str(card.get("id"))
        for card in cards_data.get("cards", [])
        if isinstance(card, dict) and card.get("id")
    }
    course_id = resolve_course_id(review_dir, args.subject, course_path)
    card_id = next_id("card", course_id, existing_ids, args.topic)

    mistake_log_path = review_dir / "mistake-log.md"
    entry = build_mistake_entry(
        args.subject,
        args.topic,
        args.question,
        args.mistake,
        args.correction,
        due_dates,
        tags,
        today,
    )
    _atomic_append_text(mistake_log_path, entry)

    cards_yaml_path = review_dir / "cards.yaml"
    card_dict = build_card_dict(
        card_id=card_id,
        course_id=course_id,
        subject=args.subject,
        topic=args.topic,
        question=args.question,
        correction=args.correction,
        rating=args.rating,
        due_dates=due_dates,
        today=today,
        chapter=args.chapter,
        difficulty=args.difficulty,
        tags=tags,
        source=args.source,
    )

    try:
        append_card(review_dir, card_dict)
    except Exception as exc:
        print(f"ERROR: failed to write cards.yaml: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    result = {
        "schema_version": 1,
        "card_id": card_id,
        "mistake_log_path": str(mistake_log_path),
        "cards_yaml_path": str(cards_yaml_path),
        "due_dates": [due_day.isoformat() for due_day in due_dates],
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(mistake_log_path)
        print(cards_yaml_path)
        print(card_id)


if __name__ == "__main__":
    main()
