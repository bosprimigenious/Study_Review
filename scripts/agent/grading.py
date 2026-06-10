"""LLM-based grading to replace keyword matching."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

STOP_WORDS = {
    "的",
    "是",
    "在",
    "和",
    "了",
    "一个",
    "这个",
    "那个",
    "可以",
    "使用",
    "进行",
    "通过",
    "以及",
    "或者",
    "其中",
    "什么",
    "哪个",
    "怎么",
    "为什么",
    "因为",
    "所以",
    "如果",
    "虽然",
    "但是",
    "然而",
    "因此",
    "说明",
}


def grade_answer(
    question: str,
    expected_answer: str,
    scoring_points: list[str],
    user_answer: str,
) -> dict[str, Any]:
    """Grade user answer using OpenAI API. Falls back to keyword matching if API unavailable."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return _keyword_grade(question, expected_answer, scoring_points, user_answer)

    scoring_text = "\n".join(f"- {point}" for point in scoring_points)
    prompt = f"""你是中国大学课程助教，批改一道复习题。

题目：{question}

标准答案要点：
{scoring_text}

学生答案：{user_answer}

请按以下格式判分（只输出 JSON，不要其他文字）：
```json
{{
  "verdict": "correct|partial|wrong",
  "score_hint": "2/4 scoring points covered",
  "covered_points": ["已覆盖的要点"],
  "omissions": ["遗漏的要点"],
  "better_answer": "更完整的参考答案",
  "follow_up_question": "一个追问题",
  "should_log_mistake": true|false
}}
```

判分标准：
- correct：≥80% 评分点被覆盖
- partial：40-79% 评分点被覆盖
- wrong：<40% 评分点被覆盖

如果答案是错误的或部分正确的，should_log_mistake 应为 true。"""

    try:
        req_body = json.dumps(
            {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "你是一个严格的大学课程助教。只输出 JSON。"},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
                "max_tokens": 500,
            }
        ).encode("utf-8")

        req = urllib_request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=req_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
        )
        resp = urllib_request.urlopen(req, timeout=30)
        data = json.loads(resp.read())
        content = data["choices"][0]["message"]["content"]

        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        return json.loads(content)
    except (urllib_error.URLError, json.JSONDecodeError, KeyError, IndexError) as exc:
        result = _keyword_grade(question, expected_answer, scoring_points, user_answer)
        result["fallback"] = True
        result["fallback_reason"] = str(exc)[:200]
        return result


def _keyword_grade(
    question: str,
    expected_answer: str,
    scoring_points: list[str],
    user_answer: str,
) -> dict[str, Any]:
    """Keyword-based grading fallback (same algorithm as review_session.py v0.2)."""
    del question

    def extract_keywords(text: str) -> list[str]:
        normalized = re.sub(r"^说明", "", text.strip())
        words = re.findall(r"[\u4e00-\u9fff]{2,}|[a-zA-Z]{2,}", normalized)
        return [word for word in words if word not in STOP_WORDS]

    effective_points = scoring_points or (
        [part.strip() for part in re.split(r"[;；]", expected_answer) if part.strip()]
        if expected_answer
        else ["核心要点"]
    )

    covered: list[str] = []
    omissions: list[str] = []
    answer_lower = user_answer.lower()
    for point in effective_points:
        keywords = extract_keywords(point)
        if not keywords:
            covered.append(point)
            continue
        matched = sum(1 for keyword in keywords if keyword.lower() in answer_lower)
        if matched >= len(keywords) * 0.5:
            covered.append(point)
        else:
            omissions.append(point)

    total = max(len(effective_points), 1)
    pct = len(covered) / total * 100
    if pct >= 80:
        verdict = "correct"
    elif pct >= 40:
        verdict = "partial"
    else:
        verdict = "wrong"

    return {
        "verdict": verdict,
        "score_hint": f"{len(covered)}/{len(effective_points)} scoring points covered",
        "covered_points": covered,
        "omissions": omissions,
        "better_answer": expected_answer or "；".join(effective_points),
        "follow_up_question": f"你能补充一下 {omissions[0]} 吗？" if omissions else "",
        "should_log_mistake": verdict in ("partial", "wrong"),
    }
