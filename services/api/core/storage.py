"""Storage helpers — thin wrapper over review_io."""

from __future__ import annotations

from pathlib import Path

from review_io import (  # noqa: E402
    get_review_dir,
    load_cards,
    load_exam_analysis,
    load_files_yaml,
    load_generated_questions,
)

from .config import COURSES_ROOT


def course_dir(course_id: str) -> Path:
    path = COURSES_ROOT / course_id
    if not path.exists():
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail=f"Course not found: {course_id}")
    return path


def review_dir(course_id: str) -> Path:
    return get_review_dir(course_dir(course_id))


def load_course_files(course_id: str) -> dict:
    return load_files_yaml(review_dir(course_id))


def load_course_analysis(course_id: str) -> dict:
    return load_exam_analysis(review_dir(course_id))


def load_course_questions(course_id: str) -> dict:
    return load_generated_questions(review_dir(course_id))


def load_course_cards(course_id: str) -> dict:
    return load_cards(review_dir(course_id))
