"""StudyReviewOrchestrator — single control agent entry point."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .intents import classify_intent
from .state import get_course_snapshot
from .tool_dispatcher import dispatch as dispatch_tool


def infer_state(snapshot: dict) -> str:
    if not snapshot["review_dir_exists"]:
        return "EMPTY"
    if snapshot["cards_count"] > 0 and snapshot["due_items_count"] > 0:
        return "REVIEW_DUE"
    if snapshot["generated_questions_count"] > 0:
        return "IN_REVIEW"
    if snapshot["plan_exists"]:
        return "PLAN_READY"
    if snapshot["exam_analysis_exists"]:
        return "EXAM_ANALYZED"
    if snapshot["materials_count"]["slides"] > 0 or snapshot["materials_count"]["past_exam"] > 0:
        return "MATERIALS_READY"
    if snapshot["review_dir_exists"]:
        return "COURSE_CREATED"
    return "EMPTY"


def run(course_path: Path, user_message: str, goal: str = "pass") -> dict[str, Any]:
    """Main orchestrator entry point."""
    snapshot = get_course_snapshot(course_path)
    state_before = infer_state(snapshot)
    intent = classify_intent(user_message)

    if intent == "grade_answer":
        return {
            "intent": intent,
            "state_before": state_before,
            "tool_called": "grading.py",
            "state_after": state_before,
            "message": "判分由 review_session 内部处理。",
            "next_action": {"label": "继续答题", "intent": "start_review"},
            "artifacts": [],
            "warnings": [],
        }

    if intent == "init_course" and not snapshot["review_dir_exists"]:
        result = dispatch_tool("init_course", course_path)
        warnings: list[str] = []
        if result.get("stderr"):
            warnings.append(result["stderr"])
        return {
            "intent": intent,
            "state_before": state_before,
            "tool_called": "init_course_review.py",
            "state_after": "COURSE_CREATED",
            "message": "已初始化课程复习工作区。下一步：上传资料或开始诊断。",
            "next_action": {"label": "上传资料", "intent": "init_course"},
            "artifacts": result.get("output", {}).get("created", []),
            "warnings": warnings,
        }

    if not snapshot["review_dir_exists"]:
        return {
            "intent": intent,
            "state_before": state_before,
            "tool_called": None,
            "state_after": state_before,
            "message": "还没有复习工作区。请先初始化课程：python scripts/init_course_review.py <课程目录>",
            "next_action": {"label": "初始化课程", "intent": "init_course"},
            "artifacts": [],
            "warnings": [],
        }

    if intent == "analyze_exam" and not snapshot["files_yaml_exists"]:
        return {
            "intent": intent,
            "state_before": state_before,
            "tool_called": None,
            "state_after": state_before,
            "message": "还没有登记资料。请先初始化课程并上传资料。",
            "next_action": {"label": "初始化课程", "intent": "init_course"},
            "artifacts": [],
            "warnings": ["files.yaml not found"],
        }

    result = dispatch_tool(intent, course_path, goal=goal)
    state_after = infer_state(get_course_snapshot(course_path))

    next_actions = {
        "init_course": {"label": "上传资料或分析试卷", "intent": "analyze_exam"},
        "analyze_exam": {"label": "生成变式题", "intent": "generate_questions"},
        "generate_questions": {"label": "生成复习计划", "intent": "make_plan"},
        "make_plan": {"label": "现在开始答题", "intent": "start_review"},
        "start_review": {"label": "继续答题或复查错题", "intent": "due_review"},
        "due_review": {"label": "开始复查", "intent": "start_review"},
    }

    response: dict[str, Any] = {
        "intent": intent,
        "state_before": state_before,
        "tool_called": result.get("tool_called"),
        "state_after": state_after,
        "message": _summarize_result(intent, result),
        "next_action": next_actions.get(intent, {"label": "查看结果", "intent": "due_review"}),
        "artifacts": result.get("output", {}).get("artifacts", []),
        "warnings": [],
    }

    if result.get("status") == "failed":
        response["warnings"].append(f"Tool failed: {result.get('stderr', 'unknown error')}")

    return response


def _summarize_result(intent: str, result: dict[str, Any]) -> str:
    """Generate a short Chinese summary based on tool output."""
    output = result.get("output", {})
    summaries = {
        "init_course": f"已初始化课程复习工作区（{output.get('materials_count', 0)} 份资料）。",
        "analyze_exam": f"已识别 {output.get('priorities_count', 0)} 个高频考点。",
        "generate_questions": f"已生成 {output.get('questions_count', 0)} 道变式题。",
        "make_plan": "已生成 90 分钟保底计划。「现在开始」环节已就绪。",
        "start_review": "复习会话已启动。",
        "due_review": "以下是今日待复习内容。",
    }
    fallback = result.get("stderr") or "操作完成。"
    return summaries.get(intent, fallback[:200])
