#!/usr/bin/env python3
"""Generate practice questions from past-exam patterns or exam analysis."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from string import Template
from typing import Any

import yaml
from yaml import SafeDumper

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from review_io import get_review_dir, load_exam_analysis, load_files_yaml, load_yaml  # noqa: E402

FORBIDDEN = re.compile(r"押题|必考|命中|预测|今年一定|很可能考")

TEMPLATES: dict[str, dict[str, str]] = {
    "contrast": {
        "prompt": "比较 $A 和 $B 的$dimension。",
        "answer_shape": "控制对象 → 使用场景 → 关键区别",
    },
    "flow": {
        "prompt": "从 $start 到 $end，按顺序描述 $protocol 的交互过程。",
        "answer_shape": "起始 → 步骤1 → ... → 结束",
    },
    "short_answer": {
        "prompt": "请简述 $concept 的定义和核心要点。",
        "answer_shape": "定义 → 要点1 → 要点2 → 要点3",
    },
    "calculation": {
        "prompt": "已知 $given，求 $target。请写出计算步骤。",
        "answer_shape": "公式 → 条件检查 → 代入 → 结果 → 单位",
    },
    "formula": {
        "prompt": "写出 $formula_name 的公式，说明每个符号的含义和适用条件。",
        "answer_shape": "公式 → 符号 → 条件",
    },
}

TIME_LIMITS = {"basic": 120, "medium": 180, "hard": 300}

_YAML_BOOL_WORDS = frozenset({"yes", "no", "on", "off", "true", "false", "y", "n"})


def _represent_str(dumper: yaml.Dumper, data: str) -> Any:
    if data.lower() in _YAML_BOOL_WORDS:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style='"')
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


yaml.add_representer(str, _represent_str, Dumper=SafeDumper)


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
        Dumper=SafeDumper,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )


def _atomic_write_yaml(path: Path, data: dict[str, Any]) -> None:
    content = _dump_yaml(data)
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


def _course_id_from_files(files_data: dict[str, Any], course_path: Path) -> str:
    course = files_data.get("course")
    if isinstance(course, dict):
        course_id = course.get("course_id") or course.get("id")
        if course_id:
            return str(course_id)
    return course_path.name


def load_past_exam_patterns(review_dir: Path) -> dict[str, Any]:
    data = load_yaml(review_dir / "past-exam-patterns.yaml")
    if data is None:
        return {"patterns": []}
    if data.get("patterns") is None:
        data["patterns"] = []
    return data


def _load_patterns_or_priorities(
    review_dir: Path,
    source: str,
) -> tuple[list[dict[str, Any]], str]:
    patterns_data = load_past_exam_patterns(review_dir)
    patterns = [
        item for item in patterns_data.get("patterns", []) if isinstance(item, dict)
    ]
    analysis_data = load_exam_analysis(review_dir)
    analysis = analysis_data.get("analysis")

    if source == "patterns":
        if patterns:
            return patterns, "patterns"
        if isinstance(analysis, dict) and analysis.get("priorities"):
            return _priorities_as_patterns(analysis), "analysis"
        raise SystemExit("Run analyze_exam.py first")

    if isinstance(analysis, dict) and analysis.get("priorities"):
        return _priorities_as_patterns(analysis), "analysis"
    if patterns:
        return patterns, "patterns"
    raise SystemExit("Run analyze_exam.py first")


def _priorities_as_patterns(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    patterns: list[dict[str, Any]] = []
    course_id = str(analysis.get("course_id") or "course")
    for index, priority in enumerate(analysis.get("priorities") or [], start=1):
        if not isinstance(priority, dict):
            continue
        question_type = (priority.get("question_types") or ["short_answer"])[0]
        template = TEMPLATES.get(question_type, TEMPLATES["short_answer"])
        patterns.append(
            {
                "id": f"pattern-{course_id}-fallback-{index:03d}",
                "course_id": course_id,
                "source_file": (priority.get("evidence") or [{}])[0].get("source_file", ""),
                "question_type": question_type,
                "topic": priority.get("topic", "review topic"),
                "chapter": priority.get("chapter"),
                "difficulty": "medium",
                "answer_shape": template["answer_shape"],
                "scoring_points": _scoring_points_from_shape(template["answer_shape"]),
            }
        )
    return patterns


def _scoring_points_from_shape(answer_shape: str) -> list[str]:
    parts = [part.strip() for part in answer_shape.replace("...", "").split("→") if part.strip()]
    if len(parts) < 2:
        return ["说明核心定义", "说明关键步骤或条件"]
    return [f"说明{part}" for part in parts[:5]]


def _split_contrast_topic(topic: str) -> tuple[str, str]:
    for separator in (" vs ", " VS ", "和", "与", "对比", "比较"):
        if separator in topic:
            left, right = topic.split(separator, 1)
            return left.strip(), right.strip()
    return topic, "相关概念"


def _extract_protocol(topic: str) -> str:
    for token in ("TCP", "UDP", "IP", "HTTP", "DNS", "ARP"):
        if token.lower() in topic.lower():
            return token
    return topic.split()[0] if topic else "协议"


def _fill_template(pattern: dict[str, Any]) -> tuple[str, list[str]]:
    question_type = str(pattern.get("question_type") or "short_answer")
    template_info = TEMPLATES.get(question_type, TEMPLATES["short_answer"])
    topic = str(pattern.get("topic") or "该知识点")
    a_side, b_side = _split_contrast_topic(topic)
    protocol = _extract_protocol(topic)

    values = {
        "A": a_side,
        "B": b_side,
        "dimension": "核心区别",
        "start": "客户端发起请求",
        "end": "收到响应",
        "protocol": protocol,
        "concept": topic,
        "given": "题目条件",
        "target": "求解目标",
        "formula_name": topic,
        "topic": topic,
    }
    prompt_template = Template(template_info["prompt"])
    prompt = prompt_template.safe_substitute(values)
    if "$" in prompt:
        prompt = prompt.replace("$", "")
        if topic not in prompt:
            prompt = f"{prompt}（{topic}）"
    scoring_points = pattern.get("scoring_points") or _scoring_points_from_shape(
        template_info["answer_shape"]
    )
    if not isinstance(scoring_points, list) or len(scoring_points) < 2:
        scoring_points = _scoring_points_from_shape(template_info["answer_shape"])
    return prompt, [str(point) for point in scoring_points[:5]]


def _pattern_weight(pattern: dict[str, Any], analysis: dict[str, Any] | None) -> int:
    if not isinstance(analysis, dict):
        return 1
    topic = pattern.get("topic")
    for priority in analysis.get("priorities") or []:
        if isinstance(priority, dict) and priority.get("topic") == topic:
            return int(priority.get("weight") or 1)
    return 1


def _next_question_ids(existing: list[dict[str, Any]], course_id: str, count: int) -> list[str]:
    max_number = 0
    for question in existing:
        if not isinstance(question, dict):
            continue
        question_id = str(question.get("id") or "")
        match = re.search(r"-(\d+)$", question_id)
        if match:
            max_number = max(max_number, int(match.group(1)))
    return [f"gen-{course_id}-{index:03d}" for index in range(max_number + 1, max_number + 1 + count)]


def _source_materials(pattern: dict[str, Any], files_data: dict[str, Any]) -> list[str]:
    source_file = pattern.get("source_file")
    if source_file:
        return [str(source_file)]
    chapter = str(pattern.get("chapter") or "").lower()
    materials: list[str] = []
    for file_entry in files_data.get("files") or []:
        if not isinstance(file_entry, dict):
            continue
        path = str(file_entry.get("path") or "")
        if chapter and chapter.lower() in path.lower():
            materials.append(path)
    return materials or [
        str(item.get("path"))
        for item in files_data.get("files") or []
        if isinstance(item, dict) and item.get("path")
    ][:1]


def _scan_forbidden(text: str) -> None:
    if FORBIDDEN.search(text):
        print(
            "WARN: may contain prediction language, manual review recommended",
            file=sys.stderr,
        )


def generate_questions(
    course_path: Path,
    count: int,
    source: str,
    goal: str,
    force: bool,
) -> dict[str, Any]:
    review_dir = get_review_dir(course_path)
    if not review_dir.exists():
        raise SystemExit("Run analyze_exam.py first")

    patterns, _source_name = _load_patterns_or_priorities(review_dir, source)
    if not patterns:
        raise SystemExit("Run analyze_exam.py first")

    files_data = load_files_yaml(review_dir)
    course_id = _course_id_from_files(files_data, course_path)
    analysis_data = load_exam_analysis(review_dir)
    analysis = analysis_data.get("analysis") if isinstance(analysis_data.get("analysis"), dict) else None

    ranked_patterns = sorted(
        patterns,
        key=lambda item: (-_pattern_weight(item, analysis), str(item.get("topic"))),
    )

    selected: list[dict[str, Any]] = []
    seen_topics: set[str] = set()
    for pattern in ranked_patterns:
        topic = str(pattern.get("topic") or "")
        if topic in seen_topics:
            continue
        selected.append(pattern)
        seen_topics.add(topic)
        if len(selected) >= count:
            break

    while len(selected) < count:
        for pattern in ranked_patterns:
            selected.append(pattern)
            if len(selected) >= count:
                break

    questions_path = review_dir / "generated-questions.yaml"
    if force:
        existing_questions: list[dict[str, Any]] = []
    else:
        existing_data = load_yaml(questions_path) or {"questions": []}
        existing_questions = [
            item for item in existing_data.get("questions", []) if isinstance(item, dict)
        ]

    question_ids = _next_question_ids(existing_questions, course_id, len(selected))
    new_questions: list[dict[str, Any]] = []

    for pattern, question_id in zip(selected, question_ids):
        prompt, scoring_points = _fill_template(pattern)
        difficulty = str(pattern.get("difficulty") or "medium")
        question = {
            "id": question_id,
            "course_id": course_id,
            "based_on_pattern_id": str(pattern.get("id") or ""),
            "source_materials": _source_materials(pattern, files_data),
            "question_type": str(pattern.get("question_type") or "short_answer"),
            "topic": str(pattern.get("topic") or ""),
            "difficulty": difficulty,
            "similarity": "same_type",
            "label": "变式题",
            "prompt": prompt,
            "expected_answer": "",
            "scoring_points": scoring_points,
            "time_limit_sec": TIME_LIMITS.get(difficulty, 180),
        }
        scan_text = " ".join(
            [question["prompt"], question["expected_answer"], *question["scoring_points"]]
        )
        _scan_forbidden(scan_text)
        new_questions.append(question)

    all_questions = existing_questions + new_questions
    output = {"schema_version": 1, "questions": all_questions}
    _atomic_write_yaml(questions_path, output)

    return {
        "schema_version": 1,
        "questions_count": len(new_questions),
        "question_ids": [item["id"] for item in new_questions],
        "artifact": "generated-questions.yaml",
        "total_questions": len(all_questions),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("course", help="Course directory path")
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--source", choices=("patterns", "analysis"), default="patterns")
    parser.add_argument("--goal", choices=("pass", "score_high"), default="pass")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = generate_questions(
        Path(args.course),
        args.count,
        args.source,
        args.goal,
        args.force,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"questions_count={result['questions_count']}")
        print(f"total_questions={result['total_questions']}")
        for question_id in result["question_ids"]:
            print(question_id)


if __name__ == "__main__":
    main()
