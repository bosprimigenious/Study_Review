#!/usr/bin/env python3
"""Analyze exam-like materials from files.yaml metadata and filenames."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import Any

import yaml
from yaml import SafeDumper

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from review_io import get_review_dir, load_files_yaml  # noqa: E402

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

CHAPTER_KEYWORDS: dict[str, list[str]] = {
    "Transport": [
        "传输层",
        "transport",
        "tcp",
        "udp",
        "拥塞",
        "流量",
        "拥塞控制",
        "滑动窗口",
    ],
    "Network": [
        "网络层",
        "network",
        "ip",
        "路由",
        "子网",
        "arp",
        "rip",
        "ospf",
        "bgp",
        "计网",
        "计算机网络",
    ],
    "Data Link": ["数据链路", "datalink", "mac", "帧", "差错", "crc", "csma"],
    "Physical": ["物理层", "physical", "编码", "调制", "奈奎斯特", "香农"],
    "Application": ["应用层", "application", "http", "dns", "smtp", "ftp", "pop3"],
}

CHAPTER_TOPICS: dict[str, str] = {
    "Transport": "TCP congestion control",
    "Network": "IP routing and subnetting",
    "Data Link": "Error detection and MAC",
    "Physical": "Physical layer encoding",
    "Application": "Application layer protocols",
}

CHAPTER_ACTIONS: dict[str, str] = {
    "Transport": "闭卷回忆 TCP 拥塞控制四个阶段",
    "Network": "练习子网划分与路由选择步骤",
    "Data Link": "闭卷回忆帧结构与差错校验流程",
    "Physical": "回忆奈奎斯特与香农公式适用条件",
    "Application": "按流程描述 DNS 与 HTTP 请求过程",
}

HIGH_VALUE_TYPES = frozenset(
    {"past_exam", "mock_exam", "homework_answer", "teacher_focus"}
)

ANSWER_SHAPES: dict[str, str] = {
    "short_answer": "定义 → 要点 → 例子",
    "contrast": "对象 → 区别维度 → 具体差异",
    "flow": "起始 → 步骤1 → 步骤2 → ... → 结束",
    "calculation": "公式 → 条件 → 代入 → 结果",
    "formula": "公式名 → 符号含义 → 适用条件",
}

REUSABLE_TEMPLATES: dict[str, str] = {
    "short_answer": "简答题按定义、要点、例子组织答案。",
    "contrast": "比较题按对象、区别维度、具体差异组织答案。",
    "flow": "流程题按起始、关键步骤、结束组织答案。",
    "calculation": "计算题按公式、条件、代入、结果组织答案。",
    "formula": "公式题按公式、符号含义、适用条件组织答案。",
}

WEIGHT_BY_TYPE: dict[str, int] = {
    "past_exam": 5,
    "mock_exam": 4,
    "teacher_focus": 4,
    "homework_answer": 3,
    "slides": 2,
}


def _atomic_write_yaml(path: Path, data: dict[str, Any]) -> None:
    _check_no_bool_values(data)
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


def _match_chapters(filename: str) -> list[str]:
    lowered = filename.lower()
    matched: list[str] = []
    for chapter, keywords in CHAPTER_KEYWORDS.items():
        if any(keyword.lower() in lowered for keyword in keywords):
            matched.append(chapter)
    return matched


def _infer_question_types(filename: str) -> list[str]:
    lowered = filename.lower()
    if re.search(r"计算(?!机)", lowered) or any(
        key in lowered for key in ("子网", "划分")
    ):
        return ["calculation"]
    if any(key in lowered for key in ("协议", "流程", "过程", "步骤")):
        return ["flow"]
    if any(key in lowered for key in ("区别", "对比", "比较")):
        return ["contrast"]
    if any(key in lowered for key in ("简述", "简答", "名词", "定义")):
        return ["short_answer"]
    return ["short_answer"]


def _weight_for_file(material_type: str, has_keyword: bool) -> int:
    if not has_keyword:
        return 1
    return WEIGHT_BY_TYPE.get(material_type, 2)


def _scoring_points_from_shape(answer_shape: str) -> list[str]:
    parts = [part.strip() for part in answer_shape.split("→") if part.strip()]
    if not parts:
        return ["说明核心要点", "说明关键条件"]
    return [f"说明{part}" for part in parts]


def _build_priority(
    chapter: str,
    source_file: str,
    material_type: str,
    filename: str,
) -> dict[str, Any]:
    topic = CHAPTER_TOPICS.get(chapter, f"{chapter} review")
    question_types = _infer_question_types(filename)
    return {
        "topic": topic,
        "chapter": chapter,
        "weight": _weight_for_file(material_type, True),
        "question_types": question_types,
        "evidence": [
            {
                "source_file": source_file,
                "reason": (
                    f"found in {material_type} file, chapter keyword matched in filename"
                ),
            }
        ],
        "recommended_action": CHAPTER_ACTIONS.get(
            chapter,
            f"闭卷回忆 {topic} 的核心得分点",
        ),
    }


def _merge_priority(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    if incoming["weight"] > existing["weight"]:
        existing["weight"] = incoming["weight"]
    for evidence in incoming.get("evidence", []):
        if evidence not in existing["evidence"]:
            existing["evidence"].append(evidence)
    for question_type in incoming.get("question_types", []):
        if question_type not in existing["question_types"]:
            existing["question_types"].append(question_type)
    return existing


def _infer_priorities(
    primary_files: list[dict[str, Any]],
    all_files: list[dict[str, Any]],
    used_slides_fallback: bool,
) -> list[dict[str, Any]]:
    priority_map: dict[str, dict[str, Any]] = {}

    for file_entry in primary_files:
        if not isinstance(file_entry, dict):
            continue
        material_type = str(file_entry.get("material_type") or "other")
        source_file = str(file_entry.get("path") or file_entry.get("name") or "")
        filename = str(file_entry.get("name") or source_file)
        chapters = _match_chapters(filename)
        if not chapters and material_type == "slides":
            chapters = _match_chapters(source_file)
        for chapter in chapters:
            priority = _build_priority(chapter, source_file, material_type, filename)
            key = chapter
            if key in priority_map:
                priority_map[key] = _merge_priority(priority_map[key], priority)
            else:
                priority_map[key] = priority

    priorities = sorted(
        priority_map.values(),
        key=lambda item: (-int(item["weight"]), item["chapter"]),
    )

    if len(priorities) < 3:
        slide_entries = [
            item
            for item in all_files
            if isinstance(item, dict) and item.get("material_type") == "slides"
        ]
        for file_entry in slide_entries:
            source_file = str(file_entry.get("path") or file_entry.get("name") or "")
            filename = str(file_entry.get("name") or source_file)
            for chapter in _match_chapters(filename) or ["Transport"]:
                if any(item["chapter"] == chapter for item in priorities):
                    continue
                priority = _build_priority(chapter, source_file, "slides", filename)
                priority["weight"] = 2
                priority["evidence"][0]["reason"] += "; slides fallback (confidence: low)"
                priorities.append(priority)
                if len(priorities) >= 3:
                    break
            if len(priorities) >= 3:
                break

    if len(priorities) < 3:
        slide_entries = [
            item
            for item in all_files
            if isinstance(item, dict) and item.get("material_type") == "slides"
        ]
        fallback_slide = slide_entries[0] if slide_entries else None
        if fallback_slide:
            source_file = str(
                fallback_slide.get("path") or fallback_slide.get("name") or ""
            )
            filename = str(fallback_slide.get("name") or source_file)
            for chapter in CHAPTER_TOPICS:
                if len(priorities) >= 3:
                    break
                if any(item["chapter"] == chapter for item in priorities):
                    continue
                priority = _build_priority(chapter, source_file, "slides", filename)
                priority["weight"] = 2
                priority["evidence"][0]["reason"] += (
                    "; default chapter supplement (confidence: low)"
                )
                priorities.append(priority)

    if used_slides_fallback and priorities:
        for priority in priorities:
            if priority["weight"] <= 2:
                for evidence in priority["evidence"]:
                    if "confidence: low" not in evidence["reason"]:
                        evidence["reason"] += "; confidence: low"

    return priorities[: max(3, len(priorities))]


def _determine_confidence(files: list[dict[str, Any]], degraded: bool) -> str:
    if degraded:
        return "low"
    types = {str(item.get("material_type")) for item in files if isinstance(item, dict)}
    if "past_exam" in types:
        return "high"
    if types & {"mock_exam", "teacher_focus", "homework_answer"}:
        return "medium"
    return "low"


def _build_summary(priorities: list[dict[str, Any]]) -> str:
    if not priorities:
        return "资料不足，建议先上传往年题或老师重点。"
    top = priorities[0]
    second = priorities[1] if len(priorities) > 1 else priorities[0]
    top_type = top["question_types"][0]
    type_label = {
        "calculation": "计算",
        "flow": "协议流程",
        "contrast": "概念辨析",
        "short_answer": "简答",
        "formula": "公式",
    }.get(top_type, "简答")
    return (
        f"{top['chapter']} 和 {second['chapter']} 题型优先级较高，"
        f"建议先做 {type_label} 题"
    )


def _build_patterns(
    priorities: list[dict[str, Any]],
    course_id: str,
    source_files: list[str],
) -> list[dict[str, Any]]:
    patterns: list[dict[str, Any]] = []
    default_source = source_files[0] if source_files else ""
    for index, priority in enumerate(priorities, start=1):
        question_type = priority["question_types"][0]
        answer_shape = ANSWER_SHAPES.get(question_type, ANSWER_SHAPES["short_answer"])
        patterns.append(
            {
                "id": f"pattern-{course_id}-{index:03d}",
                "course_id": course_id,
                "source_file": priority["evidence"][0]["source_file"] or default_source,
                "year": None,
                "question_type": question_type,
                "topic": priority["topic"],
                "chapter": priority["chapter"],
                "difficulty": "medium",
                "answer_shape": answer_shape,
                "scoring_points": _scoring_points_from_shape(answer_shape),
                "reusable_template": REUSABLE_TEMPLATES.get(
                    question_type,
                    REUSABLE_TEMPLATES["short_answer"],
                ),
            }
        )
    return patterns


def analyze_course(
    course_path: Path,
    goal: str,
    force: bool,
    dry_run: bool,
) -> dict[str, Any]:
    review_dir = get_review_dir(course_path)
    if not review_dir.exists():
        raise SystemExit("Run init_course_review.py first")

    files_data = load_files_yaml(review_dir)
    files = files_data.get("files") or []
    if not files:
        raise SystemExit("No materials registered")

    course_id = _course_id_from_files(files_data, course_path)
    high_value = [
        item
        for item in files
        if isinstance(item, dict) and item.get("material_type") in HIGH_VALUE_TYPES
    ]
    warnings: list[str] = []
    degraded = False
    analysis_files = high_value
    if not high_value:
        degraded = True
        analysis_files = [
            item for item in files if isinstance(item, dict) and item.get("material_type") == "slides"
        ]
        warnings.append("No exam-like files found; degraded to slides with confidence: low")

    priorities = _infer_priorities(
        analysis_files if not degraded else files,
        files,
        degraded,
    )
    if len(priorities) < 3:
        raise SystemExit("Could not infer at least 3 priorities from local materials")

    confidence = _determine_confidence(analysis_files if not degraded else files, degraded)
    source_files = [
        str(item.get("path") or item.get("name"))
        for item in (high_value or analysis_files)
        if isinstance(item, dict)
    ]

    analysis = {
        "id": f"exam-analysis-{course_id}-001",
        "course_id": course_id,
        "generated_at": date.today().isoformat(),
        "goal": goal,
        "source_files": source_files,
        "summary": _build_summary(priorities),
        "priorities": priorities,
        "plan_refs": ["plan.md"],
        "confidence": confidence,
    }

    patterns = _build_patterns(priorities, course_id, source_files)
    exam_analysis_doc = {"schema_version": 1, "analysis": analysis}
    patterns_doc = {"schema_version": 1, "patterns": patterns}

    exam_path = review_dir / "exam-analysis.yaml"
    patterns_path = review_dir / "past-exam-patterns.yaml"

    if dry_run:
        return {
            "analysis_id": analysis["id"],
            "priorities_count": len(priorities),
            "confidence": confidence,
            "warnings": warnings,
            "artifacts": [str(exam_path), str(patterns_path)],
            "dry_run": True,
        }

    if exam_path.exists() and not force:
        print("exam-analysis.yaml already exists, use --force to overwrite", file=sys.stderr)
    else:
        _atomic_write_yaml(exam_path, exam_analysis_doc)

    if patterns_path.exists() and not force:
        print(
            "past-exam-patterns.yaml already exists, use --force to overwrite",
            file=sys.stderr,
        )
    else:
        _atomic_write_yaml(patterns_path, patterns_doc)

    return {
        "schema_version": 1,
        "analysis_id": analysis["id"],
        "priorities_count": len(priorities),
        "confidence": confidence,
        "warnings": warnings,
        "artifacts": ["exam-analysis.yaml", "past-exam-patterns.yaml"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("course", help="Course directory path")
    parser.add_argument("--goal", choices=("pass", "score_high"), default="pass")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = analyze_course(Path(args.course), args.goal, args.force, args.dry_run)
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"analysis_id={result['analysis_id']}")
        print(f"priorities_count={result['priorities_count']}")
        print(f"confidence={result['confidence']}")
        for artifact in result["artifacts"]:
            print(artifact)


if __name__ == "__main__":
    main()
