#!/usr/bin/env python3
"""Initialize a course review workspace without overwriting existing files."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

STUDY_EXTENSIONS = {".pdf", ".ppt", ".pptx", ".md", ".txt", ".doc", ".docx", ".jpg", ".jpeg", ".png"}

TYPE_KEYWORDS: list[tuple[str, list[str]]] = [
    ("past_exam", ["往年", "真题", "历年", "试题", "期末考试", "试卷"]),
    ("mock_exam", ["样题", "模拟", "sample", "mock"]),
    ("homework_answer", ["作业答案", "习题答案", "作业解答", "hw", "homework"]),
    ("teacher_focus", ["重点", "范围", "考纲", "划范围", "考点", "复习提纲"]),
    ("notes", ["笔记", "note", "总结", "整理"]),
]


def slugify(value: str) -> str:
    ascii_slug = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return ascii_slug or "course"


def yaml_scalar(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def guess_material_type(path: Path) -> str:
    original_name = path.name
    lowered = original_name.lower()
    for material_type, keywords in TYPE_KEYWORDS:
        for keyword in keywords:
            if keyword.isascii():
                if keyword.lower() in lowered:
                    return material_type
            elif keyword in original_name:
                return material_type
    if path.suffix.lower() in {".ppt", ".pptx"}:
        return "slides"
    return "other"


def collect_materials(course_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(course_dir.rglob("*")):
        if "review" in path.parts:
            continue
        if path.is_file() and path.suffix.lower() in STUDY_EXTENSIONS:
            files.append(path)
    return files


def chapter_lines(files: list[Path], course_dir: Path) -> list[str]:
    lines: list[str] = []
    seen: set[str] = set()
    for path in files:
        stem = path.stem
        if stem in seen:
            continue
        seen.add(stem)
        try:
            display = str(path.relative_to(course_dir))
        except ValueError:
            display = path.name
        lines.append(f"- [ ] {display}")
    return lines or ["- [ ] 待根据课程资料补充"]


def build_files_yaml(course_dir: Path, files: list[Path]) -> str:
    course_name = course_dir.name
    course_id = slugify(course_name)
    today = date.today().isoformat()
    lines = [
        "course:",
        f"  id: {yaml_scalar(course_id)}",
        f"  name: {yaml_scalar(course_name)}",
        f"  created_at: {yaml_scalar(today)}",
        "",
        "files:",
    ]
    if not files:
        lines.append("  []")
        return "\n".join(lines) + "\n"

    for index, path in enumerate(files, start=1):
        relative = path.relative_to(course_dir)
        material_type = guess_material_type(path)
        file_id = f"file-{course_id}-{index:03d}"
        lines.extend(
            [
                f"  - id: {yaml_scalar(file_id)}",
                f"    path: {yaml_scalar(str(relative))}",
                f"    name: {yaml_scalar(path.name)}",
                f"    material_type: {yaml_scalar(material_type)}",
                f"    ext: {yaml_scalar(path.suffix.lower())}",
                "    status: ready",
                "    tags: []",
                "    notes: \"\"",
            ]
        )
    return "\n".join(lines) + "\n"


def build_progress_md(course_dir: Path, files: list[Path]) -> str:
    today = date.today().isoformat()
    counts: dict[str, int] = {}
    for path in files:
        material_type = guess_material_type(path)
        counts[material_type] = counts.get(material_type, 0) + 1
    chapters = "\n".join(chapter_lines(files, course_dir))
    return f"""# {course_dir.name}复习进度

## 当前状态
- 阶段：诊断
- 最近复习：{today}
- 当前目标：待确认
- 当前最弱：待诊断
- 下一步：先做 5 题诊断；如果有往年题/样题，优先分析题型。

## 资料状态
- 课件：{counts.get("slides", 0)}
- 往年题：{counts.get("past_exam", 0)}
- 样题：{counts.get("mock_exam", 0)}
- 作业答案：{counts.get("homework_answer", 0)}
- 老师重点：{counts.get("teacher_focus", 0)}
- 笔记：{counts.get("notes", 0)}

## 章节/资料进度
{chapters}

## 最近错因
- 暂无
"""


def initial_files(course_dir: Path, files: list[Path]) -> dict[str, str]:
    return {
        "files.yaml": build_files_yaml(course_dir, files),
        "progress.md": build_progress_md(course_dir, files),
        "mistake-log.md": "# 错题记录\n\n暂无。\n",
        "cards.yaml": "cards: []\n",
        "exam-analysis.yaml": "analysis: null\n",
        "past-exam-patterns.yaml": "patterns: []\n",
        "generated-questions.yaml": "questions: []\n",
        "plan.md": "# 复习计划\n\n暂无。先完成诊断或试卷分析。\n",
    }


def write_if_missing(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.write_text(content, encoding="utf-8")
    return True


def initialize_course(
    course_dir: Path,
    *,
    dry_run: bool = False,
) -> dict[str, object]:
    review_dir = course_dir / "review"
    files = collect_materials(course_dir)
    planned = initial_files(course_dir, files)
    created: list[str] = []
    skipped: list[str] = []

    if dry_run:
        for name in planned:
            if (review_dir / name).exists():
                skipped.append(name)
            else:
                created.append(name)
    else:
        review_dir.mkdir(exist_ok=True)
        for name, content in planned.items():
            if write_if_missing(review_dir / name, content):
                created.append(name)
            else:
                skipped.append(name)

    return {
        "schema_version": 1,
        "course_id": slugify(course_dir.name),
        "course_dir": str(course_dir.resolve()),
        "review_dir": str(review_dir.resolve()),
        "materials_count": len(files),
        "created": created,
        "skipped": skipped,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("course", help="Course directory to initialize")
    parser.add_argument("--dry-run", action="store_true", help="Print planned files without writing")
    parser.add_argument("--json", action="store_true", help="Output result as JSON")
    args = parser.parse_args()

    course_dir = Path(args.course).resolve()
    if not course_dir.exists() or not course_dir.is_dir():
        print(f"Course directory not found: {course_dir}", file=sys.stderr)
        raise SystemExit(1)

    result = initialize_course(course_dir, dry_run=args.dry_run)

    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        review_dir = course_dir / "review"
        print(f"Course: {course_dir}")
        print(f"Materials detected: {result['materials_count']}")
        print(f"Review directory: {review_dir}")
        if args.dry_run:
            for name in result["created"]:
                print(f"- create: {review_dir / name}")
            for name in result["skipped"]:
                print(f"- exists: {review_dir / name}")
        else:
            for name in result["created"]:
                print(f"- created: {review_dir / name}")
            for name in result["skipped"]:
                print(f"- skipped existing: {review_dir / name}")
            print(
                f"Done. created={len(result['created'])}, "
                f"skipped={len(result['skipped'])}"
            )


if __name__ == "__main__":
    main()
