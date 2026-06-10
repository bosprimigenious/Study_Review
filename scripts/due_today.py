#!/usr/bin/env python3
"""List due review cards and mistake-log items across a workspace."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from review_io import YamlParseError, load_files_yaml, load_yaml  # noqa: E402

_SKIP_DIRS = frozenset({"tests", ".git", "__pycache__", "node_modules"})
_DUE_CHECKBOX_RE = re.compile(r"^- \[ \] (?P<due>\d{4}-\d{2}-\d{2})\s*$")
_TOPIC_RE = re.compile(r"^- (?P<topic>.+)$")


@dataclass
class DueItem:
    course_id: str
    course_name: str
    item_id: str
    topic: str
    prompt: str
    due: date
    source: str


def _should_skip_relative(rel_parts: tuple[str, ...]) -> bool:
    return any(part in _SKIP_DIRS for part in rel_parts)


def _parse_due_value(value: object) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def _course_metadata(review_dir: Path) -> tuple[str, str]:
    files_data = load_files_yaml(review_dir)
    course = files_data.get("course")
    if isinstance(course, dict):
        course_id = str(course.get("course_id") or course.get("id") or "")
        course_name = str(course.get("name") or "")
        if course_id and course_name:
            return course_id, course_name
        if course_name:
            return course_id or course_name, course_name
        if course_id:
            return course_id, course_id
    course_dir = review_dir.parent
    return course_dir.name, course_dir.name


def _iter_review_files(workspace_root: Path, filename: str) -> list[Path]:
    root = workspace_root.resolve()
    if not root.exists():
        return []

    matches: list[Path] = []
    for path in root.rglob(filename):
        if path.parent.name != "review":
            continue
        try:
            rel_parts = path.relative_to(root).parts[:-2]
        except ValueError:
            continue
        if _should_skip_relative(rel_parts):
            continue
        matches.append(path)
    return sorted(matches)


def _load_cards_due_items(cards_path: Path, today: date) -> list[DueItem]:
    review_dir = cards_path.parent
    course_id, course_name = _course_metadata(review_dir)
    try:
        data = load_yaml(cards_path)
    except YamlParseError as exc:
        print(f"WARN: skipping {cards_path}: {exc}", file=sys.stderr)
        return []

    if data is None:
        return []

    cards = data.get("cards") or []
    if not isinstance(cards, list):
        print(f"WARN: skipping {cards_path}: cards must be a list", file=sys.stderr)
        return []

    items: list[DueItem] = []
    for card in cards:
        if not isinstance(card, dict):
            continue
        schedule = card.get("schedule") or {}
        due_day = _parse_due_value(schedule.get("due"))
        if due_day is None or due_day > today:
            continue
        topic = str(card.get("topic") or "未命名知识点")
        prompt = str(card.get("prompt") or topic)
        item_id = str(card.get("id") or f"card-{topic}")
        items.append(
            DueItem(
                course_id=course_id,
                course_name=course_name,
                item_id=item_id,
                topic=topic,
                prompt=prompt,
                due=due_day,
                source="card",
            )
        )
    return items


def _parse_mistake_log(log_path: Path, today: date) -> list[DueItem]:
    review_dir = log_path.parent
    course_id, course_name = _course_metadata(review_dir)

    try:
        lines = log_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        print(f"WARN: skipping {log_path}: {exc}", file=sys.stderr)
        return []

    items: list[DueItem] = []
    current_topic = ""
    in_knowledge_section = False
    for line in lines:
        if line.strip() == "### 知识点":
            in_knowledge_section = True
            current_topic = ""
            continue

        if in_knowledge_section and line.startswith("- "):
            topic_match = _TOPIC_RE.match(line)
            if topic_match:
                current_topic = topic_match.group("topic").strip()
            in_knowledge_section = False
            continue

        if line.startswith("### "):
            in_knowledge_section = False

        due_match = _DUE_CHECKBOX_RE.match(line)
        if not due_match or not current_topic:
            continue

        due_day = date.fromisoformat(due_match.group("due"))
        if due_day > today:
            continue

        item_id = f"mistake-{current_topic}-{due_day.isoformat()}"
        items.append(
            DueItem(
                course_id=course_id,
                course_name=course_name,
                item_id=item_id,
                topic=current_topic,
                prompt=current_topic,
                due=due_day,
                source="mistake_log",
            )
        )
    return items


def _dedupe_items(items: list[DueItem]) -> list[DueItem]:
    seen: set[tuple[str, str, str]] = set()
    deduped: list[DueItem] = []
    for item in items:
        key = (item.course_name, item.topic, item.due.isoformat())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def collect_due_items(workspace_root: Path, subject_filter: str | None, today: date) -> list[DueItem]:
    items: list[DueItem] = []
    for cards_path in _iter_review_files(workspace_root, "cards.yaml"):
        items.extend(_load_cards_due_items(cards_path, today))

    for log_path in _iter_review_files(workspace_root, "mistake-log.md"):
        items.extend(_parse_mistake_log(log_path, today))

    items = _dedupe_items(items)

    if subject_filter:
        items = [
            item
            for item in items
            if item.course_name == subject_filter or item.course_id == subject_filter
        ]

    items.sort(key=lambda item: (item.course_name, item.due, item.item_id))
    return items


def _group_by_course(items: list[DueItem]) -> list[tuple[str, str, list[DueItem]]]:
    grouped: dict[str, tuple[str, list[DueItem]]] = {}
    for item in items:
        bucket = grouped.setdefault(item.course_name, (item.course_id, []))
        bucket[1].append(item)
    return [(name, grouped[name][0], grouped[name][1]) for name in sorted(grouped)]


def print_human(items: list[DueItem]) -> None:
    if not items:
        print("No due items today.")
        return

    for course_name, _course_id, course_items in _group_by_course(items):
        print(f"## {course_name} ({len(course_items)})")
        for item in sorted(course_items, key=lambda entry: (entry.due, entry.item_id)):
            print(f"- {item.due.isoformat()} | {item.item_id} | {item.topic}")
        print()


def print_json(items: list[DueItem]) -> None:
    courses_payload = []
    for course_name, course_id, course_items in _group_by_course(items):
        courses_payload.append(
            {
                "course_id": course_id,
                "name": course_name,
                "items": [
                    {
                        "id": item.item_id,
                        "topic": item.topic,
                        "prompt": item.prompt,
                        "due": item.due.isoformat(),
                        "source": item.source,
                    }
                    for item in sorted(course_items, key=lambda entry: (entry.due, entry.item_id))
                ],
            }
        )
    payload = {"schema_version": 1, "courses": courses_payload}
    print(json.dumps(payload, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace_root", nargs="?", default=".")
    parser.add_argument("--subject")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    workspace_root = Path(args.workspace_root)
    today = date.today()
    items = collect_due_items(workspace_root, args.subject, today)

    if args.json:
        print_json(items)
    else:
        print_human(items)


if __name__ == "__main__":
    main()
