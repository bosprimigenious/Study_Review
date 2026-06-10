"""Assemble agent prompts from SKILL.md + references + course state."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def build_system_prompt(course_snapshot: dict | None = None) -> str:
    """Build the orchestrator system prompt."""
    skill_md = (PROJECT_ROOT / "SKILL.md").read_text(encoding="utf-8")
    source_policy = (PROJECT_ROOT / "references" / "source_policy.md").read_text(
        encoding="utf-8"
    )
    grading_ref = (PROJECT_ROOT / "references" / "agent_development_plan.md").read_text(
        encoding="utf-8"
    )

    grading_section = ""
    in_section = False
    for line in grading_ref.split("\n"):
        if "## Grading Design" in line:
            in_section = True
        elif in_section and line.startswith("## ") and "Grading" not in line:
            break
        elif in_section:
            grading_section += line + "\n"

    return f"""You are StudyReviewOrchestrator, a Chinese university exam review agent.

## Core Behavior
{skill_md}

## Source Policy
{source_policy}

## Grading Rules
{grading_section}

## Current Course State
```
{course_snapshot or "No course loaded yet."}
```

## Your Task
Given a user message (in Chinese), decide:
1. What is the user's intent?
2. What tool should be called?
3. What is the next concrete action?

Return a JSON response:
```json
{{
  "intent": "...",
  "state_before": "EMPTY|COURSE_CREATED|MATERIALS_READY|EXAM_ANALYZED|PLAN_READY|IN_REVIEW|REVIEW_DUE",
  "tool_to_call": "...",
  "message": "简短中文回复",
  "next_action": {{"label": "...", "intent": "..."}},
  "should_call_tool": true|false,
  "warnings": []
}}
```

Important:
- NEVER invent course facts not supported by local files
- If materials are insufficient, say so and suggest uploading
- Answers about course content must cite local filenames
- Prefer active recall over summaries
"""
