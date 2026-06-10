"""Review session routes."""

from __future__ import annotations

import uuid
from datetime import date
from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException

from agent.grading import grade_answer  # noqa: E402
from review_io import due_dates_from_rating, load_yaml  # noqa: E402
from review_io import _atomic_write_text as atomic_write_text  # noqa: E402
from review_io import _dump_yaml as dump_yaml  # noqa: E402

from ..core.config import COURSES_ROOT
from ..core.runner import python_script, run_script
from ..core.storage import course_dir, load_course_cards, review_dir

router = APIRouter(tags=["sessions"])

SESSIONS: dict[str, dict] = {}
RATINGS = ("忘了", "困难", "还行", "很熟")


def _load_questions(course_id: str, source: str, limit: int) -> list[dict]:
    review = review_dir(course_id)
    if source == "generated":
        gq_path = review / "generated-questions.yaml"
        if not gq_path.exists():
            raise HTTPException(
                status_code=404,
                detail="No generated questions. Run generate_questions first.",
            )
        data = yaml.safe_load(gq_path.read_text(encoding="utf-8"))
        return (data or {}).get("questions", [])[:limit]

    if source == "cards":
        cards = load_course_cards(course_id).get("cards", [])
        return [
            {
                "id": card.get("id", ""),
                "prompt": card.get("prompt", ""),
                "topic": card.get("topic", ""),
                "expected_answer": card.get("answer", ""),
                "scoring_points": [],
                "time_limit_sec": 120,
                "course_id": course_id,
                "question_type": "short_answer",
                "difficulty": card.get("difficulty", "medium"),
                "label": "错题复查",
            }
            for card in cards[:limit]
        ]

    result = run_script(
        python_script(
            "due_today.py",
            str(COURSES_ROOT),
            "--subject",
            course_id,
            "--json",
        )
    )
    questions: list[dict] = []
    for course in result.get("courses", []):
        for item in course.get("items", []):
            questions.append(
                {
                    "id": item.get("id", ""),
                    "prompt": item.get("prompt", ""),
                    "topic": item.get("topic", ""),
                    "expected_answer": "",
                    "scoring_points": [],
                    "time_limit_sec": 120,
                    "course_id": course_id,
                    "question_type": "short_answer",
                    "difficulty": "medium",
                    "label": "到期复查",
                }
            )
    return questions[:limit]


def _update_card_rating(review: Path, card_id: str, rating: str, today: date) -> str:
    cards_path = review / "cards.yaml"
    data = load_yaml(cards_path) or {"schema_version": 1, "cards": []}
    due_dates = due_dates_from_rating(rating, today)
    found = False
    for card in data.get("cards", []):
        if card.get("id") == card_id:
            card["schedule"] = {
                "rating": rating,
                "last_reviewed": today.isoformat(),
                "due": due_dates[0].isoformat(),
            }
            found = True
            break
    if not found:
        raise HTTPException(status_code=404, detail=f"Card not found: {card_id}")
    atomic_write_text(cards_path, dump_yaml(data))
    return due_dates[0].isoformat()


def _create_card_for_rating(
    session: dict,
    question: dict,
    rating: str,
    user_answer: str,
) -> str:
    result = run_script(
        python_script(
            "review_log.py",
            "--course",
            session["course_dir"],
            "--subject",
            session["course_id"],
            "--topic",
            question.get("topic", ""),
            "--question",
            question.get("prompt", ""),
            "--mistake",
            user_answer or "(已掌握)",
            "--correction",
            question.get("expected_answer", ""),
            "--rating",
            rating,
            "--json",
        )
    )
    return str(result.get("card_id", ""))


@router.post("/review-session/start")
def start_session(course_id: str, source: str = "generated", limit: int = 5) -> dict:
    course_dir(course_id)
    questions = _load_questions(course_id, source, limit)
    if not questions:
        raise HTTPException(status_code=404, detail="No questions available")

    session_id = str(uuid.uuid4())[:8]
    SESSIONS[session_id] = {
        "course_id": course_id,
        "course_dir": str(course_dir(course_id)),
        "source": source,
        "questions": questions,
        "current_index": 0,
        "results": [],
        "awaiting_rating": False,
        "pending_result": None,
        "pending_card_id": None,
        "pending_answer": None,
        "pending_question": None,
    }
    return {
        "session_id": session_id,
        "question_index": 1,
        "total_questions": len(questions),
        "question": questions[0],
    }


@router.post("/review-session/answer")
def submit_answer(session_id: str, answer: str) -> dict:
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    if session.get("awaiting_rating"):
        raise HTTPException(status_code=400, detail="Rate current question before continuing")

    idx = session["current_index"]
    questions = session["questions"]
    if idx >= len(questions):
        raise HTTPException(status_code=400, detail="All questions answered")

    question = questions[idx]
    result = grade_answer(
        question.get("prompt", ""),
        question.get("expected_answer", ""),
        question.get("scoring_points", []),
        answer,
    )

    card_id: str | None = None
    if result.get("should_log_mistake"):
        auto_rating = "困难" if result["verdict"] == "partial" else "忘了"
        log_result = run_script(
            python_script(
                "review_log.py",
                "--course",
                session["course_dir"],
                "--subject",
                session["course_id"],
                "--topic",
                question.get("topic", ""),
                "--question",
                question.get("prompt", ""),
                "--mistake",
                answer,
                "--correction",
                result.get("better_answer", "; ".join(result.get("omissions", []))),
                "--rating",
                auto_rating,
                "--json",
            )
        )
        card_id = log_result.get("card_id")

    session["awaiting_rating"] = True
    session["pending_result"] = result
    session["pending_card_id"] = card_id
    session["pending_answer"] = answer
    session["pending_question"] = question

    result["card_id"] = card_id
    result["awaiting_rating"] = True
    result["has_next"] = idx + 1 < len(questions)
    result["next_question"] = None
    return result


@router.post("/review-session/rate")
def rate_answer(
    session_id: str,
    rating: str,
    card_id: str | None = None,
) -> dict:
    if rating not in RATINGS:
        raise HTTPException(status_code=400, detail=f"Invalid rating. Choose from: {RATINGS}")

    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    if not session.get("awaiting_rating"):
        raise HTTPException(status_code=400, detail="No question awaiting rating")

    today = date.today()
    review = review_dir(session["course_id"])
    resolved_card_id = card_id or session.get("pending_card_id")
    question = session.get("pending_question") or {}

    if resolved_card_id:
        due = _update_card_rating(review, resolved_card_id, rating, today)
    else:
        resolved_card_id = _create_card_for_rating(
            session,
            question,
            rating,
            session.get("pending_answer", ""),
        )
        due = due_dates_from_rating(rating, today)[0].isoformat()

    pending = session.get("pending_result") or {}
    session["results"].append(
        {
            **pending,
            "question_id": question.get("id"),
            "rating": rating,
            "card_id": resolved_card_id,
        }
    )
    session["current_index"] = session["current_index"] + 1
    session["awaiting_rating"] = False
    session["pending_result"] = None
    session["pending_card_id"] = None
    session["pending_answer"] = None
    session["pending_question"] = None

    idx = session["current_index"]
    questions = session["questions"]
    has_next = idx < len(questions)
    return {
        "card_id": resolved_card_id,
        "rating": rating,
        "due": due,
        "has_next": has_next,
        "question_index": idx + 1 if has_next else idx,
        "total_questions": len(questions),
        "next_question": questions[idx] if has_next else None,
    }


@router.get("/review-session/{session_id}")
def get_session(session_id: str) -> dict:
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    idx = session["current_index"]
    questions = session["questions"]
    return {
        "session_id": session_id,
        "course_id": session["course_id"],
        "current_index": idx,
        "total_questions": len(questions),
        "completed": idx >= len(questions) and not session.get("awaiting_rating"),
        "awaiting_rating": session.get("awaiting_rating", False),
        "current_question": questions[idx] if idx < len(questions) else None,
    }
