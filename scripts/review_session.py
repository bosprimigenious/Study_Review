#!/usr/bin/env python3
"""Interactive one-question-at-a-time review session with rule-based grading."""

from __future__ import annotations

import argparse
import json
import signal
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from agent.grading import grade_answer as llm_grade  # noqa: E402
from review_io import (  # noqa: E402
    get_review_dir,
    load_cards,
    load_files_yaml,
    load_generated_questions,
    update_progress_next_action,
)

VERDICT_LABELS = {
    "correct": "✓ 正确。",
    "partial": "△ 部分正确（{score_hint}）",
    "wrong": "✗ 错误（{score_hint}）",
}

session_results: list[dict[str, Any]] = []
_review_dir: Path | None = None


@dataclass
class Question:
    id: str
    prompt: str
    expected_answer: str
    scoring_points: list[str]
    topic: str
    time_limit_sec: int
    source: str


def _course_metadata(review_dir: Path, course_path: Path) -> tuple[str, str]:
    files_data = load_files_yaml(review_dir)
    course = files_data.get("course")
    if isinstance(course, dict):
        course_id = str(course.get("course_id") or course.get("id") or course_path.name)
        course_name = str(course.get("name") or course_path.name)
        return course_id, course_name
    return course_path.name, course_path.name


def _resolve_subject(review_dir: Path, course_path: Path) -> str:
    cards_data = load_cards(review_dir)
    for card in cards_data.get("cards") or []:
        if isinstance(card, dict) and card.get("subject"):
            return str(card["subject"])
    _course_id, course_name = _course_metadata(review_dir, course_path)
    return course_name


def grade_answer(
    user_answer: str,
    scoring_points: list[str],
    expected_answer: str,
    *,
    prompt: str = "",
) -> dict[str, Any]:
    """Grade via agent.grading (LLM with keyword fallback)."""
    result = llm_grade(prompt, expected_answer, scoring_points, user_answer)
    covered = list(result.get("covered_points") or [])
    omissions = list(result.get("omissions") or [])
    effective_total = max(
        len(scoring_points) or len(covered) + len(omissions),
        1,
    )
    coverage_pct = len(covered) / effective_total * 100
    return {
        "verdict": str(result.get("verdict") or "wrong"),
        "score_hint": str(
            result.get("score_hint")
            or f"{len(covered)}/{effective_total} scoring points covered"
        ),
        "covered_points": covered,
        "omissions": omissions,
        "coverage_pct": coverage_pct,
        "better_answer": result.get("better_answer"),
        "follow_up_question": result.get("follow_up_question"),
        "fallback": bool(result.get("fallback")),
    }


def _stable_answer(question: Question) -> str:
    if question.expected_answer.strip():
        return question.expected_answer.strip()
    if question.scoring_points:
        return "；".join(question.scoring_points)
    return "请参考课程资料补充完整答案。"


def _follow_up_question(omission: str, topic: str) -> str:
    text = omission
    if any(key in text for key in ("定义", "概念", "是什么")):
        return f"那 {text} 是什么？"
    if any(key in text for key in ("步骤", "过程", "流程")):
        return f"请按顺序说出 {topic} 的关键步骤。"
    if any(key in text for key in ("区别", "对比", "vs", "VS")):
        return f"再说说 {topic} 和相关概念的关键差异。"
    if any(key in text for key in ("条件", "前提", "假设")):
        return f"使用 {topic} 的前提条件是什么？"
    return f"你能补充一下 {text} 吗？"


def _load_generated(review_dir: Path, limit: int) -> list[Question]:
    data = load_generated_questions(review_dir)
    questions: list[Question] = []
    for item in data.get("questions") or []:
        if not isinstance(item, dict):
            continue
        questions.append(
            Question(
                id=str(item.get("id") or ""),
                prompt=str(item.get("prompt") or ""),
                expected_answer=str(item.get("expected_answer") or ""),
                scoring_points=[
                    str(point) for point in (item.get("scoring_points") or []) if point
                ],
                topic=str(item.get("topic") or ""),
                time_limit_sec=int(item.get("time_limit_sec") or 180),
                source="generated",
            )
        )
        if len(questions) >= limit:
            break
    return questions


def _load_cards_questions(review_dir: Path, limit: int) -> list[Question]:
    data = load_cards(review_dir)
    questions: list[Question] = []
    for card in data.get("cards") or []:
        if not isinstance(card, dict):
            continue
        questions.append(
            Question(
                id=str(card.get("id") or ""),
                prompt=str(card.get("prompt") or ""),
                expected_answer=str(card.get("answer") or ""),
                scoring_points=[
                    str(point) for point in (card.get("scoring_points") or []) if point
                ],
                topic=str(card.get("topic") or ""),
                time_limit_sec=180,
                source="cards",
            )
        )
        if len(questions) >= limit:
            break
    return questions


def _load_due_questions(
    workspace_root: Path,
    course_id: str,
    course_name: str,
    limit: int,
) -> list[Question]:
    due_script = SCRIPT_DIR / "due_today.py"
    result = subprocess.run(
        [sys.executable, str(due_script), str(workspace_root), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    try:
        payload = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        return []

    questions: list[Question] = []
    for course in payload.get("courses") or []:
        if not isinstance(course, dict):
            continue
        if course.get("course_id") != course_id and course.get("name") != course_name:
            continue
        for item in course.get("items") or []:
            if not isinstance(item, dict):
                continue
            questions.append(
                Question(
                    id=str(item.get("id") or ""),
                    prompt=str(item.get("prompt") or ""),
                    expected_answer="",
                    scoring_points=[],
                    topic=str(item.get("topic") or ""),
                    time_limit_sec=180,
                    source="due",
                )
            )
            if len(questions) >= limit:
                return questions
    return questions


def _load_questions(
    review_dir: Path,
    course_path: Path,
    source: str,
    limit: int,
) -> list[Question]:
    course_id, course_name = _course_metadata(review_dir, course_path)
    if source == "generated":
        return _load_generated(review_dir, limit)
    if source == "cards":
        return _load_cards_questions(review_dir, limit)
    if source == "due":
        workspace_root = course_path.parent
        return _load_due_questions(workspace_root, course_id, course_name, limit)
    raise SystemExit(f"Unknown source: {source}")


def _log_mistake(
    course_path: Path,
    subject: str,
    question: Question,
    user_answer: str,
    verdict: str,
) -> str | None:
    rating = "困难" if verdict == "partial" else "忘了"
    correction = _stable_answer(question)
    cmd = [
        sys.executable,
        str(SCRIPT_DIR / "review_log.py"),
        "--course",
        str(course_path),
        "--subject",
        subject,
        "--topic",
        question.topic,
        "--question",
        question.prompt,
        "--mistake",
        user_answer,
        "--correction",
        correction,
        "--rating",
        rating,
        "--json",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.stderr:
        print(result.stderr.strip(), file=sys.stderr)
    if result.returncode != 0:
        print("WARN: failed to log mistake", file=sys.stderr)
        return None
    try:
        payload = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        return None
    card_id = payload.get("card_id")
    if card_id:
        print(f"已记录错题卡：{card_id}", file=sys.stderr)
    return str(card_id) if card_id else None


def _print_feedback(question: Question, grade: dict[str, Any]) -> str | None:
    verdict = grade["verdict"]
    label = VERDICT_LABELS[verdict].format(score_hint=grade["score_hint"])
    print(label)

    follow_up: str | None = None
    if verdict == "correct":
        if grade["omissions"]:
            follow_up = _follow_up_question(grade["omissions"][0], question.topic)
            print(f"追问：\n  {follow_up}")
        return follow_up

    if grade["omissions"]:
        print("遗漏：")
        for omission in grade["omissions"]:
            print(f"  - {omission}")

    stable = grade.get("better_answer") or _stable_answer(question)
    print("更稳的答法：")
    print(f"  {stable}")

    if grade["omissions"]:
        follow_up = grade.get("follow_up_question") or _follow_up_question(
            grade["omissions"][0],
            question.topic,
        )
        print(f"追问：\n  {follow_up}")
    return follow_up


def _read_user_answer() -> str:
    print("你的答案（输入完成后按 Ctrl+D 或 Ctrl+Z 结束）：")
    print("> ", end="", flush=True)
    return sys.stdin.read().strip()


def _handle_sigint(_signum: int, _frame: Any) -> None:
    print("\n\n会话中断。已记录:")
    for result in session_results:
        print(
            f"  - {result['verdict']} | {result['topic']} | "
            f"card: {result.get('card_id', 'N/A')}"
        )
    if _review_dir is not None:
        next_action = f"继续第 {len(session_results) + 1} 题"
        update_progress_next_action(_review_dir, next_action)
    raise SystemExit(0)


def run_session(
    course_path: Path,
    source: str,
    limit: int,
    non_interactive: bool,
    answer_text: str | None,
) -> int:
    global _review_dir
    review_dir = get_review_dir(course_path)
    _review_dir = review_dir
    if not review_dir.exists():
        raise SystemExit("Run init_course_review.py first")

    questions = _load_questions(review_dir, course_path, source, limit)
    if not questions:
        raise SystemExit(
            "No questions available. Run generate_questions or check due_today."
        )

    subject = _resolve_subject(review_dir, course_path)
    total = len(questions)

    for index, question in enumerate(questions, start=1):
        print(f"\n第 {index}/{total} 题（建议 {question.time_limit_sec}s）")
        print("═" * 35)
        print(question.prompt)
        print("═" * 35)

        if non_interactive:
            user_answer = answer_text or ""
        else:
            user_answer = _read_user_answer()

        print("─" * 35)
        grade = grade_answer(
            user_answer,
            question.scoring_points,
            question.expected_answer,
            prompt=question.prompt,
        )
        _print_feedback(question, grade)
        print("─" * 35)

        card_id: str | None = None
        if grade["verdict"] in ("partial", "wrong"):
            card_id = _log_mistake(course_path, subject, question, user_answer, grade["verdict"])

        session_results.append(
            {
                "verdict": grade["verdict"],
                "topic": question.topic,
                "card_id": card_id,
                "question_id": question.id,
            }
        )

        if non_interactive:
            return 0

        try:
            choice = input("[Enter 下一题] [Q 退出] ").strip().lower()
        except EOFError:
            choice = ""
        if choice in {"q", "quit", "exit"}:
            break

    weakest = [
        result["topic"]
        for result in session_results
        if result["verdict"] in ("partial", "wrong")
    ]
    if weakest:
        next_action = f"复查 {len(weakest)} 条错题"
    else:
        next_action = "完成本轮复习"
    update_progress_next_action(review_dir, next_action, weakest_topics=weakest[:3])
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("course", help="Course directory path")
    parser.add_argument(
        "--source",
        choices=("generated", "due", "cards"),
        default="generated",
    )
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--non-interactive", action="store_true")
    parser.add_argument("--answer", default=None)
    args = parser.parse_args()

    signal.signal(signal.SIGINT, _handle_sigint)

    exit_code = run_session(
        Path(args.course),
        args.source,
        args.limit,
        args.non_interactive,
        args.answer,
    )
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
