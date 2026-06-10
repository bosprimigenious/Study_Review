#!/usr/bin/env python3
"""Build an executable review plan from exam analysis and course state."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from review_io import (  # noqa: E402
    get_review_dir,
    load_cards,
    load_exam_analysis,
    load_files_yaml,
    update_progress_next_action,
)

ALL_CHAPTERS = ("Transport", "Network", "Data Link", "Physical", "Application")

_CHAPTER_KEYWORDS: dict[str, list[str]] = {
    "Transport": ["transport", "传输", "tcp", "udp", "拥塞"],
    "Network": ["network", "网络", "ip", "路由", "子网", "计网", "计算机网络"],
    "Data Link": ["datalink", "数据链路", "mac", "帧"],
    "Physical": ["physical", "物理", "编码", "调制"],
    "Application": ["application", "应用", "http", "dns"],
}

_CHAPTER_TOPICS: dict[str, str] = {
    "Transport": "TCP congestion control",
    "Network": "IP routing and subnetting",
    "Data Link": "Error detection and MAC",
    "Physical": "Physical layer encoding",
    "Application": "Application layer protocols",
}

_CHAPTER_ACTIONS: dict[str, str] = {
    "Transport": "闭卷回忆 TCP 拥塞控制四个阶段",
    "Network": "练习子网划分与路由选择步骤",
    "Data Link": "闭卷回忆帧结构与差错校验流程",
    "Physical": "回忆奈奎斯特与香农公式适用条件",
    "Application": "按流程描述 DNS 与 HTTP 请求过程",
}


@dataclass
class PlanTask:
    duration: int
    action: str
    source: str
    topic: str
    chapter: str
    optional: bool = False
    day: int | None = None


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


def _course_name(files_data: dict[str, Any], course_path: Path) -> str:
    course = files_data.get("course")
    if isinstance(course, dict):
        name = course.get("name")
        if name:
            return str(name)
    return course_path.name


def _parse_progress(progress_path: Path) -> tuple[str, str]:
    if not progress_path.exists():
        return "诊断", "待诊断"
    content = progress_path.read_text(encoding="utf-8")
    stage_match = re.search(r"^- 阶段：(.+)$", content, re.MULTILINE)
    weak_match = re.search(r"^- 当前最弱：(.+)$", content, re.MULTILINE)
    stage = stage_match.group(1).strip() if stage_match else "诊断"
    weakest = weak_match.group(1).strip() if weak_match else "待诊断"
    return stage, weakest


def _count_due_cards(review_dir: Path, today: date) -> int:
    cards_data = load_cards(review_dir)
    count = 0
    for card in cards_data.get("cards") or []:
        if not isinstance(card, dict):
            continue
        schedule = card.get("schedule") or {}
        due_value = schedule.get("due")
        if not due_value:
            continue
        try:
            due_day = date.fromisoformat(str(due_value))
        except ValueError:
            continue
        if due_day <= today:
            count += 1
    return count


def _match_chapter(filename: str) -> str | None:
    lowered = filename.lower()
    for chapter, keywords in _CHAPTER_KEYWORDS.items():
        if any(keyword.lower() in lowered for keyword in keywords):
            return chapter
    return None


def _priorities_from_files(files_data: dict[str, Any]) -> list[dict[str, Any]]:
    priorities: list[dict[str, Any]] = []
    weight_by_type = {
        "past_exam": 5,
        "mock_exam": 4,
        "teacher_focus": 4,
        "homework_answer": 3,
        "slides": 2,
    }
    for file_entry in files_data.get("files") or []:
        if not isinstance(file_entry, dict):
            continue
        filename = str(file_entry.get("name") or file_entry.get("path") or "")
        chapter = _match_chapter(filename)
        if not chapter:
            continue
        material_type = str(file_entry.get("material_type") or "other")
        priorities.append(
            {
                "topic": _CHAPTER_TOPICS.get(chapter, chapter),
                "chapter": chapter,
                "weight": weight_by_type.get(material_type, 2),
                "question_types": ["short_answer"],
                "evidence": [
                    {
                        "source_file": str(file_entry.get("path") or filename),
                        "reason": f"inferred from {material_type} filename",
                    }
                ],
                "recommended_action": _CHAPTER_ACTIONS.get(
                    chapter,
                    f"复习 {chapter} 核心考点",
                ),
            }
        )
    merged: dict[str, dict[str, Any]] = {}
    for priority in priorities:
        chapter = priority["chapter"]
        if chapter not in merged or priority["weight"] > merged[chapter]["weight"]:
            merged[chapter] = priority
    return sorted(merged.values(), key=lambda item: (-int(item["weight"]), item["chapter"]))


def _priority_source(priority: dict[str, Any]) -> str:
    evidence = priority.get("evidence") or []
    if evidence and isinstance(evidence[0], dict):
        source = evidence[0].get("source_file")
        if source:
            return str(source)
    return "exam-analysis"


def _load_hard_topics(review_dir: Path) -> set[str]:
    from review_io import load_generated_questions

    data = load_generated_questions(review_dir)
    hard_topics: set[str] = set()
    for question in data.get("questions") or []:
        if not isinstance(question, dict):
            continue
        if str(question.get("difficulty")) == "hard":
            topic = question.get("topic")
            if topic:
                hard_topics.add(str(topic))
    return hard_topics


def _sort_priorities(
    priorities: list[dict[str, Any]],
    weakest: str,
    goal: str,
    hard_topics: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    weak_tokens = {token.strip() for token in re.split(r"[、,，/]", weakest) if token.strip()}

    def sort_key(priority: dict[str, Any]) -> tuple[int, int, str]:
        topic = str(priority.get("topic") or "")
        is_weak = any(token in topic or token in str(priority.get("chapter") or "") for token in weak_tokens)
        is_hard = topic in hard_topics
        weight = int(priority.get("weight") or 1)
        if goal == "pass" and is_hard:
            return (0, weight, topic)
        if is_weak:
            return (2, weight, topic)
        return (3, weight, topic)

    ranked = sorted(priorities, key=sort_key, reverse=True)
    primary: list[dict[str, Any]] = []
    deferred: list[dict[str, Any]] = []
    for priority in ranked:
        topic = str(priority.get("topic") or "")
        if goal == "pass" and topic in hard_topics:
            deferred.append(priority)
        else:
            primary.append(priority)
    return primary, deferred


def _task_from_priority(
    priority: dict[str, Any],
    duration: int,
    action: str | None = None,
    optional: bool = False,
    day: int | None = None,
) -> PlanTask:
    return PlanTask(
        duration=duration,
        action=action or str(priority.get("recommended_action") or priority.get("topic")),
        source=_priority_source(priority),
        topic=str(priority.get("topic") or ""),
        chapter=str(priority.get("chapter") or ""),
        optional=optional,
        day=day,
    )


def _allocate_minutes_30(
    priorities: list[dict[str, Any]],
    weakest: str,
    due_count: int,
    goal: str,
    hard_topics: set[str],
) -> tuple[list[PlanTask], list[PlanTask], list[PlanTask]]:
    primary, deferred = _sort_priorities(priorities, weakest, goal, hard_topics)
    if not primary and deferred:
        primary = deferred[:1]
        deferred = deferred[1:]

    tasks: list[PlanTask] = []
    if primary:
        top = primary[0]
        tasks.append(_task_from_priority(top, 15))
        qtypes = top.get("question_types") or ["short_answer"]
        second_action = f"完成 1 道 {qtypes[0]} 变式题（generated-questions.yaml）"
        tasks.append(_task_from_priority(top, 10, action=second_action))

    weak_priority = None
    for priority in primary[1:] + deferred:
        topic = str(priority.get("topic") or "")
        if topic and (topic in weakest or priority.get("chapter", "") in weakest):
            weak_priority = priority
            break
    if weak_priority is None and len(primary) > 1:
        weak_priority = primary[1]
    elif weak_priority is None and deferred:
        weak_priority = deferred[0]

    if due_count > 0:
        tasks.append(
            PlanTask(
                duration=5,
                action="复查今日 due 错题",
                source="cards.yaml",
                topic="due mistakes",
                chapter="",
            )
        )
    elif weak_priority:
        tasks.append(_task_from_priority(weak_priority, 5, action=f"补强弱项：{weak_priority.get('topic')}"))

    wrap = PlanTask(
        duration=5,
        action="快速过一遍今日关键词和评分点",
        source="progress.md",
        topic="wrap-up",
        chapter="",
    )
    return tasks, [], [wrap]


def _allocate_minutes_90(
    priorities: list[dict[str, Any]],
    weakest: str,
    due_count: int,
    goal: str,
    hard_topics: set[str],
) -> tuple[list[PlanTask], list[PlanTask], list[PlanTask]]:
    primary, deferred = _sort_priorities(priorities, weakest, goal, hard_topics)
    durations = [25, 20, 20]
    tasks: list[PlanTask] = []
    for index, priority in enumerate(primary[:3]):
        tasks.append(_task_from_priority(priority, durations[index]))

    if due_count > 0:
        tasks.append(
            PlanTask(
                duration=10,
                action=f"复查 {due_count} 条 due 错题",
                source="cards.yaml",
                topic="due mistakes",
                chapter="",
            )
        )

    later: list[PlanTask] = []
    for priority in primary[3:]:
        later.append(_task_from_priority(priority, 15))
    for priority in deferred:
        later.append(
            _task_from_priority(
                priority,
                15,
                optional=True,
                action=f"选做：{priority.get('recommended_action')}",
            )
        )

    wrap = PlanTask(
        duration=15,
        action="收尾：复查错题记录并更新 progress.md",
        source="mistake-log.md",
        topic="wrap-up",
        chapter="",
    )
    return tasks, later, [wrap]


def _allocate_days(
    days: int,
    priorities: list[dict[str, Any]],
    weakest: str,
    due_count: int,
    goal: str,
    hard_topics: set[str],
) -> tuple[list[PlanTask], list[PlanTask], list[PlanTask]]:
    primary, deferred = _sort_priorities(priorities, weakest, goal, hard_topics)
    day_templates: list[list[tuple[int, str]]] = []

    if days == 3:
        day_templates = [
            [(30, "诊断性自测 + 最高频 topic"), (25, "高频 topic 闭卷回忆"), (35, "变式题练习")],
            [(35, "次高频 topic 复习"), (30, "弱项补强"), (25, "协议流程题")],
            [(30, "综合回顾"), (25, "错题复查"), (35, "模拟自测")],
        ]
    else:
        labels = [
            "诊断 + 最高频 topic",
            "次高频 topic",
            "弱项补强",
            "协议/流程题",
            "计算题",
            "综合回顾",
            "错题复查 + 模拟自测",
        ]
        for label in labels[:days]:
            day_templates.append([(30, label), (30, f"完成 {label} 配套练习"), (30, "当日复盘")])

    tasks: list[PlanTask] = []
    priority_cycle = primary or deferred
    for day_index, template in enumerate(day_templates, start=1):
        for slot_index, (duration, label) in enumerate(template):
            if not priority_cycle:
                break
            priority = priority_cycle[(day_index + slot_index - 2) % len(priority_cycle)]
            action = f"{label}：{priority.get('recommended_action')}"
            tasks.append(_task_from_priority(priority, duration, action=action, day=day_index))

    if due_count > 0 and days >= 3:
        tasks.append(
            PlanTask(
                duration=10,
                action=f"复查 {due_count} 条 due 错题",
                source="cards.yaml",
                topic="due mistakes",
                chapter="",
                day=days,
            )
        )

    later = [
        _task_from_priority(
            priority,
            20,
            optional=True,
            action=f"选做：{priority.get('recommended_action')}",
        )
        for priority in deferred
    ]
    wrap = [
        PlanTask(
            duration=15,
            action="最后一天：快速过关键词 + 更新 progress.md",
            source="progress.md",
            topic="wrap-up",
            chapter="",
            day=days,
        )
    ]
    return tasks, later, wrap


def _covered_chapters(tasks: list[PlanTask]) -> set[str]:
    return {task.chapter for task in tasks if task.chapter}


def _skipped_topics(covered: set[str]) -> list[str]:
    skipped: list[str] = []
    for chapter in ALL_CHAPTERS:
        if chapter not in covered:
            label = f"{chapter} Layer" if chapter == "Application" else chapter
            skipped.append(label)
    return skipped


def _format_task_line(task: PlanTask) -> str:
    prefix = f"Day{task.day} · " if task.day else ""
    optional = "（选做）" if task.optional else ""
    return f"- {prefix}{task.duration}min: {task.action}{optional}（{task.source}）"


def _build_plan_markdown(
    course_name: str,
    goal: str,
    time_label: str,
    analysis_id: str | None,
    stage: str,
    weakest: str,
    due_count: int,
    first_tasks: list[PlanTask],
    later_tasks: list[PlanTask],
    skipped: list[str],
    wrap_tasks: list[PlanTask],
    wrap_minutes: int,
    first_action: str,
    used_files_fallback: bool,
) -> str:
    goal_label = "保底" if goal == "pass" else "高分"
    lines = [
        f"# {course_name}复习计划",
        "",
        "## 目标",
        f"- {goal_label} | {time_label}",
        "",
        "## 依据",
    ]
    if analysis_id:
        lines.append(f"- exam-analysis.yaml（analysis id: {analysis_id}）")
    elif used_files_fallback:
        lines.append("- files.yaml（无 exam-analysis，按资料清单降级生成）")
    lines.append(f"- progress.md（当前阶段：{stage}，最弱：{weakest}）")
    if due_count > 0:
        lines.append(f"- cards.yaml（due items: {due_count} 条）")

    lines.extend(["", "## 先做"])
    if first_tasks:
        lines.extend(_format_task_line(task) for task in first_tasks)
    else:
        lines.append("- 暂无可用任务，请先运行 analyze_exam.py")

    lines.extend(["", "## 后做"])
    if later_tasks:
        lines.extend(_format_task_line(task) for task in later_tasks)
    else:
        lines.append("- 无次要任务")

    lines.extend(["", "## 可以先放弃"])
    if skipped:
        lines.extend(f"- {topic}" for topic in skipped)
    else:
        lines.append("- 无")

    lines.extend(["", f"## 最后 {wrap_minutes} 分钟"])
    if wrap_tasks:
        lines.extend(_format_task_line(task) for task in wrap_tasks)
    else:
        lines.append(f"- {wrap_minutes}min: 快速过关键词并记录下一步")

    lines.extend(["", "## 现在开始", first_action, ""])
    return "\n".join(lines)


def _session_command(course_path: Path) -> str:
    display_path = course_path.as_posix() if course_path.is_absolute() else str(course_path)
    return (
        f"运行 `python scripts/review_session.py {display_path} "
        f"--source generated --limit 5`"
    )


def build_plan(
    course_path: Path,
    goal: str,
    minutes: int | None,
    days: int | None,
    force: bool,
) -> dict[str, Any]:
    review_dir = get_review_dir(course_path)
    if not review_dir.exists():
        raise SystemExit("Run init_course_review.py first")

    exam_path = review_dir / "exam-analysis.yaml"
    progress_path = review_dir / "progress.md"
    cards_path = review_dir / "cards.yaml"
    files_path = review_dir / "files.yaml"

    has_exam_file = exam_path.exists()
    has_progress = progress_path.exists()
    has_cards = cards_path.exists()
    has_files = files_path.exists()

    if not has_exam_file and not has_progress and not has_cards and not has_files:
        raise SystemExit(
            "No course state available. Run init_course_review and analyze_exam first."
        )

    files_data = load_files_yaml(review_dir)
    analysis_data = load_exam_analysis(review_dir)
    analysis = analysis_data.get("analysis")
    warnings: list[str] = []
    used_files_fallback = False
    priorities: list[dict[str, Any]] = []
    analysis_id: str | None = None

    if isinstance(analysis, dict) and analysis.get("priorities"):
        priorities = [item for item in analysis["priorities"] if isinstance(item, dict)]
        analysis_id = str(analysis.get("id") or "")
    else:
        used_files_fallback = True
        print(
            "WARN: No exam analysis found, plan based on material counts only",
            file=sys.stderr,
        )
        priorities = _priorities_from_files(files_data)

    if not priorities:
        raise SystemExit(
            "No course state available. Run init_course_review and analyze_exam first."
        )

    stage, weakest = _parse_progress(progress_path)
    due_count = _count_due_cards(review_dir, date.today())
    hard_topics = _load_hard_topics(review_dir)
    course_name = _course_name(files_data, course_path)

    if minutes == 30:
        first_tasks, later_tasks, wrap_tasks = _allocate_minutes_30(
            priorities, weakest, due_count, goal, hard_topics
        )
        time_label = "30 分钟"
        wrap_minutes = 5
    elif minutes == 90:
        first_tasks, later_tasks, wrap_tasks = _allocate_minutes_90(
            priorities, weakest, due_count, goal, hard_topics
        )
        time_label = "90 分钟"
        wrap_minutes = 15
    elif days in (3, 7):
        first_tasks, later_tasks, wrap_tasks = _allocate_days(
            days, priorities, weakest, due_count, goal, hard_topics
        )
        time_label = f"{days} 天"
        wrap_minutes = 15
    else:
        raise SystemExit("Unsupported time budget")

    covered = _covered_chapters(first_tasks + later_tasks)
    skipped = _skipped_topics(covered)
    first_action = _session_command(course_path.resolve())

    plan_body = _build_plan_markdown(
        course_name=course_name,
        goal=goal,
        time_label=time_label,
        analysis_id=analysis_id,
        stage=stage,
        weakest=weakest,
        due_count=due_count,
        first_tasks=first_tasks,
        later_tasks=later_tasks,
        skipped=skipped,
        wrap_tasks=wrap_tasks,
        wrap_minutes=wrap_minutes,
        first_action=first_action,
        used_files_fallback=used_files_fallback,
    )

    plan_path = review_dir / "plan.md"
    wrote = False
    if plan_path.exists() and not force:
        print("plan.md already exists, use --force to overwrite", file=sys.stderr)
    else:
        _atomic_write_text(plan_path, plan_body)
        update_progress_next_action(review_dir, first_action)
        wrote = True

    result: dict[str, Any] = {
        "schema_version": 1,
        "goal": goal,
        "first_action": (
            f"python scripts/review_session.py {course_path} --source generated --limit 5"
        ),
        "artifact": "plan.md",
        "skipped_topics": skipped,
        "warnings": warnings,
        "wrote": wrote,
    }
    if minutes is not None:
        result["minutes"] = minutes
    if days is not None:
        result["days"] = days
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("course", help="Course directory path")
    parser.add_argument("--minutes", type=int, choices=(30, 90))
    parser.add_argument("--days", type=int, choices=(3, 7))
    parser.add_argument("--goal", choices=("pass", "score_high"), default="pass")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.minutes is not None and args.days is not None:
        raise SystemExit("Use --minutes or --days, not both")

    minutes = args.minutes
    days = args.days
    if minutes is None and days is None:
        minutes = 90

    result = build_plan(
        Path(args.course),
        args.goal,
        minutes,
        days,
        args.force,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        if result.get("minutes"):
            print(f"minutes={result['minutes']}")
        if result.get("days"):
            print(f"days={result['days']}")
        print(f"goal={result['goal']}")
        print(result["first_action"])
        print(result["artifact"])


if __name__ == "__main__":
    main()
