#!/usr/bin/env python3
"""Shared IO helpers for course review YAML and Markdown state."""

from __future__ import annotations

import os
import re
import tempfile
import zlib
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import yaml

_REQUIRED_CARD_FIELDS = frozenset(
    {"id", "course_id", "subject", "topic", "prompt", "answer", "schedule"}
)

_RATING_INTERVALS: dict[str, list[int]] = {
    "忘了": [0, 1],
    "困难": [1],
    "还行": [3],
    "很熟": [7],
}

_YAML_BOOL_WORDS = frozenset(
    {"yes", "no", "on", "off", "true", "false", "y", "n"}
)

_LAST_REVIEWED_RE = re.compile(r"^(- 最近复习：).*$", re.MULTILINE)
_NEXT_ACTION_RE = re.compile(r"^(- 下一步：).*$", re.MULTILINE)
_WEAKEST_TOPICS_RE = re.compile(r"^(- 当前最弱：).*$", re.MULTILINE)


class YamlParseError(Exception):
    """Raised when a YAML file cannot be parsed."""

    def __init__(self, message: str, path: Path) -> None:
        self.path = path
        super().__init__(f"{message}: {path}")


def _topic_slug(topic: str) -> str:
    ascii_slug = re.sub(r"[^a-zA-Z0-9]+", "-", topic).strip("-").lower()
    if ascii_slug:
        return ascii_slug
    suffix = format(zlib.crc32(topic.encode("utf-8")) & 0xffffffff, "08x")[-4:]
    return suffix


def _represent_str(dumper: yaml.Dumper, data: str) -> Any:
    if data.lower() in _YAML_BOOL_WORDS:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style='"')
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


yaml.add_representer(str, _represent_str, Dumper=yaml.SafeDumper)


def _check_no_bool_values(value: Any, path: str = "") -> None:
    if isinstance(value, bool):
        raise ValueError(f"YAML field must not be Python bool at {path or 'root'}")
    if isinstance(value, dict):
        for key, item in value.items():
            _check_no_bool_values(item, f"{path}.{key}" if path else str(key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _check_no_bool_values(item, f"{path}[{index}]")


def _dump_yaml(data: dict[str, Any]) -> str:
    _check_no_bool_values(data)
    return yaml.dump(
        data,
        Dumper=yaml.SafeDumper,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def load_yaml(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    if path.stat().st_size == 0:
        return {}
    try:
        raw = path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise YamlParseError(str(exc), path) from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise YamlParseError("YAML root must be a mapping", path)
    return data


def get_review_dir(course_path: Path) -> Path:
    resolved = course_path.resolve()
    if resolved.name == "review":
        return resolved
    return resolved / "review"


def write_if_missing(path: Path, content: str) -> bool:
    if path.exists():
        return False
    _atomic_write_text(path, content)
    return True


def append_yaml_list(path: Path, key: str, item: dict[str, Any]) -> None:
    data = load_yaml(path)
    if data is None:
        data = {key: [item]}
    else:
        values = data.get(key)
        if values is None:
            data[key] = [item]
        elif not isinstance(values, list):
            raise ValueError(f"YAML key {key!r} must be a list in {path}")
        else:
            values.append(item)
    _atomic_write_text(path, _dump_yaml(data))


def make_course_id(name: str) -> str:
    ascii_slug = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    if ascii_slug:
        return ascii_slug
    suffix = format(zlib.crc32(name.encode("utf-8")) & 0xffffffff, "08x")[-4:]
    return f"course-{suffix}"


def next_id(
    prefix: str,
    course_id: str,
    existing_ids: set[str],
    topic: str = "",
) -> str:
    topic_part = _topic_slug(topic) if topic else "item"
    number = 1
    while True:
        candidate = f"{prefix}-{course_id}-{topic_part}-{number}"
        if candidate not in existing_ids:
            return candidate
        number += 1


def due_dates_from_rating(rating: str, today: date) -> list[date]:
    offsets = _RATING_INTERVALS.get(rating)
    if offsets is None:
        raise ValueError(f"Unknown rating: {rating}")
    return [today + timedelta(days=offset) for offset in offsets]


def append_card(review_dir: Path, card_dict: dict[str, Any]) -> str:
    missing = _REQUIRED_CARD_FIELDS - set(card_dict)
    if missing:
        missing_fields = ", ".join(sorted(missing))
        raise ValueError(f"Missing required card fields: {missing_fields}")

    cards_path = review_dir / "cards.yaml"
    data = load_yaml(cards_path)
    if data is None:
        data = {"schema_version": 1, "cards": []}
    cards = data.setdefault("cards", [])
    if not isinstance(cards, list):
        raise ValueError(f"cards must be a list in {cards_path}")

    _check_no_bool_values(card_dict)
    cards.append(card_dict)
    _atomic_write_text(cards_path, _dump_yaml(data))
    return str(card_dict["id"])


def _minimal_progress_template(next_action: str, today: date) -> str:
    return (
        "# 课程复习进度\n\n"
        "## 当前状态\n"
        "- 阶段：诊断\n"
        f"- 最近复习：{today.isoformat()}\n"
        "- 当前目标：待确认\n"
        "- 当前最弱：待诊断\n"
        f"- 下一步：{next_action}\n\n"
        "## 最近错因\n"
        "- 暂无\n"
    )


def update_progress_next_action(
    review_dir: Path,
    next_action: str,
    **kwargs: Any,
) -> bool:
    progress_path = review_dir / "progress.md"
    today = date.today()

    if not progress_path.exists():
        _atomic_write_text(progress_path, _minimal_progress_template(next_action, today))
        return True

    content = progress_path.read_text(encoding="utf-8")

    if _LAST_REVIEWED_RE.search(content):
        content = _LAST_REVIEWED_RE.sub(
            rf"\1{today.isoformat()}",
            content,
            count=1,
        )
    else:
        content = content.replace(
            "## 当前状态\n",
            f"## 当前状态\n- 最近复习：{today.isoformat()}\n",
            1,
        )

    if _NEXT_ACTION_RE.search(content):
        content = _NEXT_ACTION_RE.sub(rf"\1{next_action}", content, count=1)
    else:
        content = content.replace(
            "## 当前状态\n",
            f"## 当前状态\n- 下一步：{next_action}\n",
            1,
        )

    weakest_topics = kwargs.get("weakest_topics")
    if weakest_topics is not None:
        weakest_text = (
            weakest_topics
            if isinstance(weakest_topics, str)
            else "、".join(str(item) for item in weakest_topics)
        )
        if _WEAKEST_TOPICS_RE.search(content):
            content = _WEAKEST_TOPICS_RE.sub(rf"\1{weakest_text}", content, count=1)
        else:
            content = content.replace(
                "## 当前状态\n",
                f"## 当前状态\n- 当前最弱：{weakest_text}\n",
                1,
            )

    _atomic_write_text(progress_path, content)
    return True


def _normalize_files_data(data: dict[str, Any]) -> dict[str, Any]:
    course = data.get("course")
    if isinstance(course, dict):
        if "course_id" not in course and "id" in course:
            course["course_id"] = course["id"]
        elif "id" not in course and "course_id" in course:
            course["id"] = course["course_id"]
    files = data.get("files")
    if files is None:
        data["files"] = []
    return data


def load_files_yaml(review_dir: Path) -> dict[str, Any]:
    data = load_yaml(review_dir / "files.yaml")
    if data is None:
        return {"files": []}
    return _normalize_files_data(data)


def load_exam_analysis(review_dir: Path) -> dict[str, Any]:
    data = load_yaml(review_dir / "exam-analysis.yaml")
    if data is None:
        return {"analysis": None}
    if "analysis" not in data:
        data["analysis"] = None
    return data


def load_generated_questions(review_dir: Path) -> dict[str, Any]:
    data = load_yaml(review_dir / "generated-questions.yaml")
    if data is None:
        return {"questions": []}
    if data.get("questions") is None:
        data["questions"] = []
    return data


def load_cards(review_dir: Path) -> dict[str, Any]:
    data = load_yaml(review_dir / "cards.yaml")
    if data is None:
        return {"cards": []}
    if data.get("cards") is None:
        data["cards"] = []
    return data
