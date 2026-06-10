"""Course routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..core.config import COURSES_ROOT
from ..core.runner import python_script, run_script
from ..core.storage import course_dir, review_dir

router = APIRouter(prefix="/courses", tags=["courses"])


def _infer_stage(course_path) -> str:
    review = course_path / "review"
    if not review.exists():
        return "未初始化"
    if (review / "generated-questions.yaml").exists():
        return "可练习"
    if (review / "exam-analysis.yaml").exists():
        return "已分析"
    if (review / "files.yaml").exists():
        return "已登记"
    return "诊断"


@router.get("")
def list_courses() -> dict:
    """List all course directories with review state."""
    from agent.state import get_course_snapshot  # noqa: E402

    courses = []
    if not COURSES_ROOT.exists():
        return {"courses": courses}

    for entry in sorted(COURSES_ROOT.iterdir()):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        snapshot = get_course_snapshot(entry)
        courses.append(
            {
                "course_id": entry.name,
                "name": entry.name,
                "materials_count": sum(snapshot["materials_count"].values()),
                "stage": _infer_stage(entry),
                "due_items_count": snapshot["due_items_count"],
                "last_reviewed": snapshot.get("last_reviewed"),
            }
        )
    return {"courses": courses}


@router.post("/{course_id}/init-review")
def init_course_review(course_id: str) -> dict:
    path = course_dir(course_id)
    return run_script(python_script("init_course_review.py", str(path), "--json"))


@router.get("/{course_id}/progress")
def get_progress(course_id: str) -> dict:
    progress_path = review_dir(course_id) / "progress.md"
    if not progress_path.exists():
        raise HTTPException(status_code=404, detail="No progress file")
    return {
        "course_id": course_id,
        "content": progress_path.read_text(encoding="utf-8"),
    }


@router.get("/{course_id}/plan")
def get_plan(course_id: str) -> dict:
    plan_path = review_dir(course_id) / "plan.md"
    if not plan_path.exists():
        raise HTTPException(status_code=404, detail="No plan found")
    return {
        "course_id": course_id,
        "plan_md": plan_path.read_text(encoding="utf-8"),
    }
