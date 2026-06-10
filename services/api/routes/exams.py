"""Exam analysis + question generation routes."""

from __future__ import annotations

import yaml
from fastapi import APIRouter, HTTPException

from ..core.runner import python_script, run_script
from ..core.storage import course_dir, load_course_questions, review_dir

router = APIRouter(prefix="/courses", tags=["exams"])


@router.post("/{course_id}/exam-analysis")
def analyze_exam(course_id: str, goal: str = "pass") -> dict:
    path = course_dir(course_id)
    return run_script(
        python_script("analyze_exam.py", str(path), "--force", "--goal", goal, "--json")
    )


@router.get("/{course_id}/exam-analysis/latest")
def get_latest_analysis(course_id: str) -> dict:
    analysis_path = review_dir(course_id) / "exam-analysis.yaml"
    if not analysis_path.exists():
        raise HTTPException(status_code=404, detail="No analysis found")
    data = yaml.safe_load(analysis_path.read_text(encoding="utf-8"))
    analysis = data.get("analysis") or {}
    priorities = analysis.get("priorities", [])
    return {
        "analysis_id": analysis.get("id", ""),
        "course_id": course_id,
        "priorities_count": len(priorities),
        "confidence": analysis.get("confidence", "medium"),
        "priorities": priorities,
        "raw": data,
    }


@router.post("/{course_id}/questions")
def generate_questions(course_id: str, count: int = 5) -> dict:
    path = course_dir(course_id)
    result = run_script(
        python_script(
            "generate_questions.py",
            str(path),
            "--count",
            str(count),
            "--force",
            "--json",
        )
    )
    gq = load_course_questions(course_id)
    questions = gq.get("questions", [])
    ids = result.get("question_ids") or [q.get("id", "") for q in questions[-count:]]
    return {
        **result,
        "questions_count": len(questions),
        "question_ids": ids,
        "questions": questions[-count:] if count else questions,
    }


@router.post("/{course_id}/plan")
def make_plan(course_id: str, minutes: int = 90, goal: str = "pass") -> dict:
    path = course_dir(course_id)
    result = run_script(
        python_script(
            "plan_review.py",
            str(path),
            "--minutes",
            str(minutes),
            "--goal",
            goal,
            "--force",
            "--json",
        )
    )
    plan_path = review_dir(course_id) / "plan.md"
    plan_md = plan_path.read_text(encoding="utf-8") if plan_path.exists() else ""
    return {**result, "plan_md": plan_md, "minutes": minutes, "goal": goal}
