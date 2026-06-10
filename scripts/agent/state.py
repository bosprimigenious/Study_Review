"""Course state snapshot for the orchestrator."""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from review_io import (  # noqa: E402
    get_review_dir,
    load_cards,
    load_exam_analysis,
    load_files_yaml,
    load_generated_questions,
)


def get_course_snapshot(course_path: Path) -> dict:
    """Return a compact course state snapshot for agent decision-making."""
    review_dir = get_review_dir(course_path)
    snapshot: dict = {
        "course_path": str(course_path.resolve()),
        "review_dir_exists": review_dir.exists(),
        "files_yaml_exists": (review_dir / "files.yaml").exists(),
        "materials_count": {
            "slides": 0,
            "past_exam": 0,
            "mock_exam": 0,
            "homework_answer": 0,
            "teacher_focus": 0,
            "notes": 0,
        },
        "exam_analysis_exists": False,
        "generated_questions_count": 0,
        "plan_exists": False,
        "cards_count": 0,
        "due_items_count": 0,
        "last_reviewed": None,
        "next_action": None,
    }

    if not review_dir.exists():
        return snapshot

    files_data = load_files_yaml(review_dir)
    for file_entry in files_data.get("files", []):
        material_type = file_entry.get("material_type", "other")
        if material_type in snapshot["materials_count"]:
            snapshot["materials_count"][material_type] += 1

    analysis_data = load_exam_analysis(review_dir)
    snapshot["exam_analysis_exists"] = analysis_data.get("analysis") is not None

    generated = load_generated_questions(review_dir)
    snapshot["generated_questions_count"] = len(generated.get("questions", []))

    snapshot["plan_exists"] = (review_dir / "plan.md").exists()

    cards_data = load_cards(review_dir)
    cards = cards_data.get("cards", [])
    snapshot["cards_count"] = len(cards)
    today = date.today().isoformat()
    snapshot["due_items_count"] = sum(
        1
        for card in cards
        if str(card.get("schedule", {}).get("due", "")) <= today
    )

    progress_path = review_dir / "progress.md"
    if progress_path.exists():
        text = progress_path.read_text(encoding="utf-8")
        last_reviewed = re.search(r"最近复习：(.+)", text)
        if last_reviewed:
            snapshot["last_reviewed"] = last_reviewed.group(1).strip()
        next_action = re.search(r"下一步：(.+)", text)
        if next_action:
            snapshot["next_action"] = next_action.group(1).strip()

    return snapshot
