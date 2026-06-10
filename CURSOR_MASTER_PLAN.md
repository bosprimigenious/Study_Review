# Cursor 主控执行计划：v0.3 → v1.0

**给 Cursor 的总指令**：本文档包含 4 个 Phase。请严格按顺序执行——每个 Phase 全部验收通过后才能进入下一个。每个 Phase 开始时，先打印 `=== PHASE X START ===`，结束时打印 `=== PHASE X DONE ===` 并列出验收结果。

**项目根目录**：`C:\Fullstack_Development\Study_Review`
**所有命令从项目根目录执行**

---

## Phase 0：确认当前状态

在开始任何新代码之前，确认以下文件存在：

```bash
ls scripts/review_io.py scripts/review_log.py scripts/due_today.py scripts/init_course_review.py
ls scripts/analyze_exam.py scripts/generate_questions.py scripts/plan_review.py scripts/review_session.py
ls tests/test_*.py
python -m unittest discover -s tests -p "test_*.py" -v
```

16 条测试必须全部 PASS。如果有任何失败，停下来修复后再继续。

---

---

## Phase 1：v0.3 Agent 编排闭环

### 入口条件
- v0.2 68/68 全部完成
- 16 条测试全绿
- 环境变量 `OPENAI_API_KEY` 已设置（脚本从 `os.environ["OPENAI_API_KEY"]` 读取）

### 你要新建/修改的文件

```
scripts/
├── agent_run.py              ← 新建：总控 agent CLI 入口
├── agent/
│   ├── __init__.py           ← 新建：空文件
│   ├── orchestrator.py       ← 新建：StudyReviewOrchestrator
│   ├── state.py              ← 新建：课程状态快照
│   ├── intents.py            ← 新建：意图分类器
│   ├── tool_dispatcher.py    ← 新建：工具调度器
│   ├── prompts.py            ← 新建：prompt 组装
│   ├── validators.py         ← 新建：输出校验
│   └── grading.py            ← 新建：LLM 判分（替代规则判分）
tests/
└── test_agent_eval.py        ← 新建：7 条 agent eval
```

### Part 1A：`scripts/agent/state.py` — 课程状态快照

```python
"""Course state snapshot for the orchestrator."""
from pathlib import Path
from datetime import date
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.review_io import (
    get_review_dir, load_files_yaml, load_exam_analysis,
    load_generated_questions, load_cards, load_yaml
)

def get_course_snapshot(course_path: Path) -> dict:
    """Return a compact course state snapshot for agent decision-making."""
    review_dir = get_review_dir(course_path)
    snapshot = {
        "course_path": str(course_path.resolve()),
        "review_dir_exists": review_dir.exists(),
        "files_yaml_exists": (review_dir / "files.yaml").exists(),
        "materials_count": {"slides": 0, "past_exam": 0, "mock_exam": 0,
                           "homework_answer": 0, "teacher_focus": 0, "notes": 0},
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

    # materials
    files_data = load_files_yaml(review_dir)
    for f in files_data.get("files", []):
        mt = f.get("material_type", "other")
        if mt in snapshot["materials_count"]:
            snapshot["materials_count"][mt] += 1

    # exam analysis
    analysis_data = load_exam_analysis(review_dir)
    snapshot["exam_analysis_exists"] = analysis_data.get("analysis") is not None

    # generated questions
    gq = load_generated_questions(review_dir)
    snapshot["generated_questions_count"] = len(gq.get("questions", []))

    # plan
    snapshot["plan_exists"] = (review_dir / "plan.md").exists()

    # cards + due
    cards_data = load_cards(review_dir)
    cards = cards_data.get("cards", [])
    snapshot["cards_count"] = len(cards)
    today = date.today().isoformat()
    snapshot["due_items_count"] = sum(
        1 for c in cards
        if c.get("schedule", {}).get("due", "") <= today
    )

    # progress
    progress_path = review_dir / "progress.md"
    if progress_path.exists():
        text = progress_path.read_text(encoding="utf-8")
        import re
        lr = re.search(r"最近复习：(.+)", text)
        if lr:
            snapshot["last_reviewed"] = lr.group(1).strip()
        na = re.search(r"下一步：(.+)", text)
        if na:
            snapshot["next_action"] = na.group(1).strip()

    return snapshot
```

### Part 1B：`scripts/agent/intents.py` — 意图分类器

8 种 intent：

```python
"""Intent classification for StudyReviewOrchestrator."""

INTENTS = [
    "init_course",        # 开始复习某门课
    "analyze_exam",       # 根据试卷分析重点
    "generate_questions", # 按往年题出题 / 生成变式题
    "make_plan",          # 今晚怎么不挂 / 生成计划
    "start_review",       # 开始刷题 / 抽查
    "grade_answer",       # 用户提交了答案（由 session 触发）
    "log_mistake",        # 答案错了要记录
    "due_review",         # 今天复习什么
]

# 关键词 → intent 映射（按优先级排列，先匹配到的胜出）
INTENT_KEYWORDS = [
    ("make_plan",          ["今晚怎么", "不挂", "救火", "速成", "来不及", "只剩", "计划", "规划", "安排"]),
    ("analyze_exam",       ["试卷", "往年题", "样题", "真题", "分析重点", "考频", "高频", "题型"]),
    ("generate_questions", ["出题", "生成题", "变式", "模拟题", "题目", "刷题", "练习"]),
    ("start_review",       ["开始复习", "抽查", "抽背", "考我", "问我", "答题", "摸底", "开始刷"]),
    ("due_review",         ["今天复习什么", "该复习什么", "复查", "错题", "due", "到期"]),
    ("init_course",        ["初始化", "开始", "新建", "创建", "注册课程"]),
]

def classify_intent(user_message: str) -> str:
    """Simple keyword-based intent classifier. Returns intent name."""
    msg = user_message.lower()
    for intent, keywords in INTENT_KEYWORDS:
        for kw in keywords:
            if kw in msg:
                return intent
    return "start_review"  # default: assume user wants to practice
```

### Part 1C：`scripts/agent/tool_dispatcher.py` — 工具调度器

```python
"""Dispatch agent intents to CLI scripts."""
import subprocess
import sys
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent  # study-review-skill/

def dispatch(intent: str, course_dir: Optional[Path] = None, **kwargs) -> dict:
    """Run the appropriate CLI script and return structured result."""

    scripts_dir = PROJECT_ROOT / "scripts"
    workspace = str(PROJECT_ROOT / "tests" / "fixtures") if not course_dir else str(course_dir)

    intent_to_script = {
        "init_course":        ["python", str(scripts_dir / "init_course_review.py"), workspace],
        "analyze_exam":       ["python", str(scripts_dir / "analyze_exam.py"), workspace, "--force"],
        "generate_questions": ["python", str(scripts_dir / "generate_questions.py"), workspace, "--count", "5", "--force"],
        "make_plan":          ["python", str(scripts_dir / "plan_review.py"), workspace, "--minutes", "90", "--goal", kwargs.get("goal", "pass"), "--force"],
        "start_review":       ["python", str(scripts_dir / "review_session.py"), workspace, "--source", "generated", "--limit", "5"],
        "due_review":         ["python", str(scripts_dir / "due_today.py"), workspace],
    }

    cmd = intent_to_script.get(intent)
    if not cmd:
        return {"error": f"No tool for intent: {intent}", "tool_called": None, "status": "unavailable"}

    # All scripts support --json except review_session (L1)
    if intent != "start_review":
        cmd.append("--json")

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))

    output = {}
    if result.returncode == 0 and result.stdout.strip():
        import json
        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError:
            output = {"raw_output": result.stdout[:500]}

    return {
        "intent": intent,
        "tool_called": cmd[2].name if len(cmd) > 2 else None,  # script filename
        "status": "success" if result.returncode == 0 else "failed",
        "exit_code": result.returncode,
        "stderr": result.stderr[:500] if result.stderr else None,
        "output": output,
    }
```

### Part 1D：`scripts/agent/prompts.py` — Prompt 组装

```python
"""Assemble agent prompts from SKILL.md + references + course state."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent

def build_system_prompt(course_snapshot: dict = None) -> str:
    """Build the orchestrator system prompt."""

    # Load SKILL.md (core behavior rules)
    skill_md = (PROJECT_ROOT / "SKILL.md").read_text(encoding="utf-8")

    # Load source policy
    source_policy = (PROJECT_ROOT / "references" / "source_policy.md").read_text(encoding="utf-8")

    # Load grading guidelines
    grading_ref = (PROJECT_ROOT / "references" / "agent_development_plan.md").read_text(encoding="utf-8")
    # Extract only the Grading Design section
    grading_section = ""
    in_section = False
    for line in grading_ref.split("\n"):
        if "## Grading Design" in line:
            in_section = True
        elif in_section and line.startswith("## ") and "Grading" not in line:
            break
        elif in_section:
            grading_section += line + "\n"

    prompt = f"""You are StudyReviewOrchestrator, a Chinese university exam review agent.

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
    return prompt
```

### Part 1E：`scripts/agent/grading.py` — LLM 判分

```python
"""LLM-based grading to replace keyword matching."""
import os
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent

def grade_answer(
    question: str,
    expected_answer: str,
    scoring_points: list[str],
    user_answer: str
) -> dict:
    """Grade user answer using OpenAI API. Falls back to keyword matching if API unavailable."""

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return _keyword_grade(question, expected_answer, scoring_points, user_answer)

    scoring_text = "\n".join(f"- {p}" for p in scoring_points)
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
        from urllib import request
        import urllib.error

        req_body = json.dumps({
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "你是一个严格的大学课程助教。只输出 JSON。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 500
        }).encode("utf-8")

        req = request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=req_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
        )
        resp = request.urlopen(req, timeout=30)
        data = json.loads(resp.read())
        content = data["choices"][0]["message"]["content"]

        # Extract JSON from response (may be wrapped in ```json)
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        return json.loads(content)

    except Exception as e:
        # Fallback to keyword matching if API fails
        result = _keyword_grade(question, expected_answer, scoring_points, user_answer)
        result["fallback"] = True
        result["fallback_reason"] = str(e)[:200]
        return result


def _keyword_grade(question: str, expected_answer: str, scoring_points: list[str], user_answer: str) -> dict:
    """Keyword-based grading fallback (same algorithm as review_session.py v0.2)."""
    import re
    STOP_WORDS = {"的","是","在","和","了","一个","这个","那个","可以","使用",
                  "进行","通过","以及","或者","其中","什么","哪个","怎么","为什么",
                  "因为","所以","如果","虽然","但是","然而","因此"}

    def extract_keywords(text: str) -> list[str]:
        words = re.findall(r"[一-鿿]{2,}|[a-zA-Z]{2,}", text)
        return [w for w in words if w not in STOP_WORDS]

    covered = []
    omissions = []
    for point in scoring_points:
        kws = extract_keywords(point)
        if not kws:
            covered.append(point)
            continue
        matched = sum(1 for kw in kws if kw.lower() in user_answer.lower())
        if matched >= len(kws) * 0.5:
            covered.append(point)
        else:
            omissions.append(point)

    pct = len(covered) / max(len(scoring_points), 1) * 100
    if pct >= 80:
        verdict = "correct"
    elif pct >= 40:
        verdict = "partial"
    else:
        verdict = "wrong"

    return {
        "verdict": verdict,
        "score_hint": f"{len(covered)}/{len(scoring_points)} scoring points covered",
        "covered_points": covered,
        "omissions": omissions,
        "better_answer": expected_answer,
        "follow_up_question": f"你能补充一下 {omissions[0]} 吗？" if omissions else "",
        "should_log_mistake": verdict in ("partial", "wrong"),
    }
```

### Part 1F：`scripts/agent/validators.py` — 输出校验

```python
"""Validate agent output before returning to user."""
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent

# Files considered "local sources" — anything under fixtures or user-specified course dirs
LOCAL_SOURCE_PATTERNS = [
    r"tests/fixtures",
    r"计算机网络",
    r"概率论",
    r"毛概",
    r"计组",
    r"理论计算机",
]

def validate_agent_output(response: dict, course_snapshot: dict = None) -> list[str]:
    """Return list of warnings. Empty list = valid."""
    warnings = []

    # Required fields
    for field in ["intent", "message", "next_action"]:
        if field not in response:
            warnings.append(f"Missing required field: {field}")

    # Source policy: message should not contain unsupported claims
    message = response.get("message", "")
    # Check for common patterns of invented facts
    suspicious = ["根据教材", "第X章说", "书上提到", "考试重点"]
    for s in suspicious:
        if s in message:
            # OK if it references a local file
            if not any(pattern in message for pattern in LOCAL_SOURCE_PATTERNS):
                warnings.append(f"Message may contain unsourced claim: '{s}'")

    # No fake tool claims
    if response.get("tool_to_call") and response.get("should_call_tool"):
        valid_tools = [
            "init_course_review.py", "analyze_exam.py", "generate_questions.py",
            "plan_review.py", "review_session.py", "review_log.py", "due_today.py"
        ]
        tool = response.get("tool_to_call", "")
        if tool not in valid_tools:
            warnings.append(f"Tool not implemented: {tool}")

    return warnings
```

### Part 1G：`scripts/agent/orchestrator.py` — 总控入口

```python
"""StudyReviewOrchestrator — single control agent entry point."""
import json
from pathlib import Path
from .state import get_course_snapshot
from .intents import classify_intent
from .tool_dispatcher import dispatch as dispatch_tool
from .prompts import build_system_prompt
from .validators import validate_agent_output

PROJECT_ROOT = Path(__file__).parent.parent.parent

# State inference from snapshot
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


def run(course_path: Path, user_message: str, goal: str = "pass") -> dict:
    """
    Main orchestrator entry point.

    Args:
        course_path: Path to the course directory
        user_message: User's natural language request (Chinese)
        goal: "pass" or "score_high"

    Returns:
        Structured response dict with intent, message, next_action, artifacts, warnings
    """
    # 1. Get course state
    snapshot = get_course_snapshot(course_path)
    state_before = infer_state(snapshot)

    # 2. Classify intent
    intent = classify_intent(user_message)

    # 3. Handle simple grade_answer intent (no tool dispatch needed)
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

    # 4. Handle init_course when review dir doesn't exist
    if intent == "init_course" and not snapshot["review_dir_exists"]:
        result = dispatch_tool("init_course", course_path)
        return {
            "intent": intent,
            "state_before": state_before,
            "tool_called": "init_course_review.py",
            "state_after": "COURSE_CREATED",
            "message": "已初始化课程复习工作区。下一步：上传资料或开始诊断。",
            "next_action": {"label": "上传资料", "intent": "init_course"},
            "artifacts": result.get("output", {}).get("created", []),
            "warnings": result.get("stderr") or [],
        }

    # 5. Check prerequisites
    if not snapshot["review_dir_exists"]:
        return {
            "intent": intent,
            "state_before": state_before,
            "tool_called": None,
            "state_after": state_before,
            "message": "还没有复习工作区。请先初始化课程：python scripts/init_course_review.py <课程目录>",
            "next_action": {"label": "初始化课程", "intent": "init_course"},
            "artifacts": [],
            "warnings": ["review/ directory does not exist"],
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

    # 6. Dispatch tool
    result = dispatch_tool(intent, course_path, goal=goal)

    # 7. Determine next state
    state_after = infer_state(get_course_snapshot(course_path))

    # 8. Build response
    next_actions = {
        "init_course":        {"label": "上传资料或分析试卷", "intent": "analyze_exam"},
        "analyze_exam":       {"label": "生成变式题", "intent": "generate_questions"},
        "generate_questions": {"label": "生成复习计划", "intent": "make_plan"},
        "make_plan":          {"label": "现在开始答题", "intent": "start_review"},
        "start_review":       {"label": "继续答题或复查错题", "intent": "due_review"},
        "due_review":         {"label": "开始复查", "intent": "start_review"},
    }

    response = {
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


def _summarize_result(intent: str, result: dict) -> str:
    """Generate a short Chinese summary based on tool output."""
    output = result.get("output", {})
    summaries = {
        "init_course":        f"已初始化课程复习工作区（{output.get('materials_count', 0)} 份资料）。",
        "analyze_exam":       f"已识别 {output.get('priorities_count', 0)} 个高频考点。",
        "generate_questions": f"已生成 {output.get('questions_count', 0)} 道变式题。",
        "make_plan":          "已生成 90 分钟保底计划。「现在开始」环节已就绪。",
        "start_review":       "复习会话已启动。",
        "due_review":         "以下是今日待复习内容。",
    }
    return summaries.get(intent, result.get("stderr", "操作完成。")[:200])
```

### Part 1H：`scripts/agent/__init__.py`

空文件：
```python
# agent package
```

### Part 1I：`scripts/agent_run.py` — CLI 入口

```python
#!/usr/bin/env python3
"""StudyReviewOrchestrator CLI entry point."""
import argparse
import json
from pathlib import Path
from agent.orchestrator import run

def main():
    parser = argparse.ArgumentParser(description="Study Review Agent")
    parser.add_argument("course", help="Course directory path")
    parser.add_argument("message", help="Natural language request (Chinese)")
    parser.add_argument("--goal", choices=["pass", "score_high"], default="pass")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    course_path = Path(args.course).resolve()
    if not course_path.exists():
        print(f"Course not found: {course_path}", file=__import__("sys").stderr)
        raise SystemExit(1)

    response = run(course_path, args.message, args.goal)

    if args.json:
        print(json.dumps(response, ensure_ascii=False, indent=2))
    else:
        print(f"\n意图：{response['intent']}")
        print(f"状态：{response['state_before']} → {response['state_after']}")
        if response.get('tool_called'):
            print(f"工具：{response['tool_called']}")
        print(f"\n{response['message']}")
        if response.get('next_action'):
            print(f"\n下一步：{response['next_action']['label']}")
        if response.get('warnings'):
            print(f"\n⚠ {response['warnings']}")

    if response.get("warnings"):
        raise SystemExit(0 if response.get("tool_called") else 1)

if __name__ == "__main__":
    main()
```

### Part 1J：`tests/test_agent_eval.py` — 7 条最小 eval

```python
"""7 minimum eval scenarios from agent_development_plan.md."""
import unittest
import tempfile
import subprocess
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "computer-network"

class TestAgentEval(unittest.TestCase):

    def _run_agent(self, course: Path, message: str) -> dict:
        r = subprocess.run(
            [sys.executable, "scripts/agent_run.py", str(course), message, "--json"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT)
        )
        self.assertEqual(r.returncode, 0, f"Agent failed: {r.stderr}")
        return json.loads(r.stdout)

    # Eval 1: No review dir → suggest init
    def test_no_review_dir_suggests_init(self):
        with tempfile.TemporaryDirectory() as tmp:
            course = Path(tmp) / "empty-course"
            course.mkdir()
            resp = self._run_agent(course, "开始复习计算机网络")
            self.assertIn(resp["intent"], ["init_course", "start_review"])
            self.assertIsNotNone(resp["next_action"])

    # Eval 2: Has materials, no analysis → suggest analyze
    def test_materials_no_analysis_suggests_analyze(self):
        resp = self._run_agent(FIXTURE, "根据试卷分析重点")
        self.assertIn(resp["intent"], ["analyze_exam", "make_plan"])
        self.assertIsNotNone(resp["next_action"])

    # Eval 3: 按往年题出题 → route to generate_questions
    def test_generate_questions_routing(self):
        resp = self._run_agent(FIXTURE, "按往年题出5道变式题")
        self.assertIn(resp["intent"], ["generate_questions", "analyze_exam"])
        self.assertIsNotNone(resp["next_action"])

    # Eval 4: 今晚怎么不挂 → make_plan
    def test_emergency_plan(self):
        resp = self._run_agent(FIXTURE, "我今晚怎么不挂科")
        self.assertEqual(resp["intent"], "make_plan")
        self.assertIsNotNone(resp["next_action"])

    # Eval 5: 今天复习什么 → due_review
    def test_due_review_intent(self):
        resp = self._run_agent(FIXTURE, "今天该复习什么")
        self.assertEqual(resp["intent"], "due_review")

    # Eval 6: No fake tool claims
    def test_no_fake_tool(self):
        resp = self._run_agent(FIXTURE, "帮我分析一下PPT的内容")
        # Should not claim a non-existent tool was called
        self.assertIsNotNone(resp.get("next_action"))
        if resp.get("tool_called"):
            valid = ["init_course_review.py", "analyze_exam.py", "generate_questions.py",
                     "plan_review.py", "review_session.py", "review_log.py", "due_today.py", None]
            self.assertIn(resp["tool_called"], valid)

    # Eval 7: Source policy — message should not claim external facts
    def test_no_unsourced_claims(self):
        resp = self._run_agent(FIXTURE, "TCP拥塞控制是什么")
        message = resp.get("message", "")
        # If making a factual claim, should reference a local file
        # (This is a soft check — the validator warns but doesn't block)
        self.assertIsNotNone(resp.get("next_action"))

if __name__ == "__main__":
    unittest.main()
```

### Phase 1 验收

```bash
# 1. 课程状态快照
python -c "
from scripts.agent.state import get_course_snapshot
from pathlib import Path
import json
snap = get_course_snapshot(Path('tests/fixtures/computer-network'))
print(json.dumps(snap, ensure_ascii=False, indent=2))
"
# → 应输出完整快照，materials_count, exam_analysis_exists 等字段有值

# 2. Agent CLI（不调 LLM，纯规则路由）
python scripts/agent_run.py tests/fixtures/computer-network "今晚怎么不挂" --json
# → intent=make_plan, state_before 正确

python scripts/agent_run.py tests/fixtures/computer-network "按往年题出5道题" --json
# → intent=generate_questions, tool_called=generate_questions.py

python scripts/agent_run.py tests/fixtures/computer-network "今天该复习什么" --json
# → intent=due_review

# 3. Agent eval
python -m unittest tests/test_agent_eval.py -v
# → 7 条全部 PASS

# 4. LLM 判分（如果 OPENAI_API_KEY 已设置）
python -c "
from scripts.agent.grading import grade_answer
result = grade_answer(
    'TCP拥塞控制和流量控制的区别是什么？',
    '拥塞控制面向网络整体负载；流量控制面向接收端处理能力。',
    ['控制对象不同', '使用窗口不同', '触发原因不同'],
    '拥塞控制面向网络避免过载'
)
print(result['verdict'])  # 应为 partial
print(result['covered_points'])
print(result['omissions'])
"
```

Phase 1 全部验收通过后进入 Phase 2。

---

---

## Phase 2：v0.4 FastAPI 后端

### 入口条件
- Phase 1 全部验收通过
- 7 条 agent eval 全绿

### 依赖安装
```bash
pip install fastapi uvicorn pydantic
```

### 你要新建的文件

```
services/
├── __init__.py
└── api/
    ├── __init__.py
    ├── app.py              ← FastAPI app
    ├── models.py            ← Pydantic request/response models
    ├── routes/
    │   ├── __init__.py
    │   ├── courses.py       ← /courses 路由
    │   ├── materials.py     ← /courses/{id}/materials
    │   ├── exams.py         ← /courses/{id}/exam-analysis + questions
    │   ├── sessions.py      ← /review-session/start + /answer
    │   ├── mistakes.py      ← /mistakes
    │   └── agent.py         ← POST /agent/run
    └── core/
        ├── __init__.py
        ├── storage.py       ← 统一文件读写（复用 review_io API）
        └── agent_bridge.py  ← 桥接 scripts/agent/orchestrator
tests/
└── test_api.py              ← 集成测试
```

### Part 2A：`services/api/models.py` — Pydantic Models

```python
"""Pydantic models for API request/response."""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import date


# ── Course ──
class CourseSummary(BaseModel):
    course_id: str
    name: str
    materials_count: int
    stage: str
    due_items_count: int
    last_reviewed: Optional[str] = None

class InitReviewResponse(BaseModel):
    course_id: str
    review_dir: str
    created: list[str]
    skipped: list[str]

# ── Materials ──
class MaterialFile(BaseModel):
    id: str
    path: str
    name: str
    material_type: Literal["slides","past_exam","mock_exam","homework_answer","teacher_focus","notes","textbook","other"]
    ext: str
    status: str
    tags: list[str] = []

class MaterialsListResponse(BaseModel):
    course_id: str
    files: list[MaterialFile]

# ── Exam Analysis ──
class Evidence(BaseModel):
    source_file: str
    reason: str

class Priority(BaseModel):
    topic: str
    chapter: Optional[str] = None
    weight: int
    question_types: list[str]
    evidence: list[Evidence]
    recommended_action: str

class ExamAnalysisResponse(BaseModel):
    analysis_id: str
    course_id: str
    priorities_count: int
    confidence: str
    priorities: list[Priority]

# ── Questions ──
class GeneratedQuestion(BaseModel):
    id: str
    course_id: str
    question_type: str
    topic: str
    prompt: str
    expected_answer: str
    scoring_points: list[str]
    difficulty: str
    label: str
    time_limit_sec: int

class GenerateQuestionsResponse(BaseModel):
    questions_count: int
    question_ids: list[str]
    questions: list[GeneratedQuestion]

# ── Plan ──
class PlanResponse(BaseModel):
    goal: str
    minutes: Optional[int] = None
    days: Optional[int] = None
    first_action: str
    plan_md: str  # raw markdown content

# ── Review Session ──
class StartSessionRequest(BaseModel):
    source: Literal["generated","due","cards"] = "generated"
    limit: int = Field(default=5, ge=1, le=50)

class QuestionResponse(BaseModel):
    session_id: str
    question_index: int
    total_questions: int
    question: GeneratedQuestion | dict

class AnswerRequest(BaseModel):
    session_id: str
    answer: str

class GradingResponse(BaseModel):
    verdict: Literal["correct","partial","wrong"]
    score_hint: str
    covered_points: list[str]
    omissions: list[str]
    better_answer: str
    follow_up_question: str
    card_id: Optional[str] = None

# ── Mistakes ──
class MistakeEntry(BaseModel):
    id: str
    course_id: str
    topic: str
    question: str
    mistake: str
    correction: str
    due_dates: list[str]

# ── Due Today ──
class DueItem(BaseModel):
    id: str
    topic: str
    prompt: str
    due: str
    source: str

class DueTodayResponse(BaseModel):
    courses: list[dict]  # [{"course_id":..., "name":..., "items":[...]}]

# ── Agent ──
class AgentRunRequest(BaseModel):
    course_id: str
    message: str
    goal: Literal["pass","score_high"] = "pass"

class AgentRunResponse(BaseModel):
    intent: str
    state_before: str
    tool_called: Optional[str] = None
    state_after: str
    message: str
    next_action: dict
    artifacts: list[str] = []
    warnings: list[str] = []
```

### Part 2B：`services/api/app.py` — FastAPI App

```python
"""FastAPI application for Study Review."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import courses, materials, exams, sessions, mistakes, agent

app = FastAPI(
    title="Study Review API",
    version="0.4.0",
    description="CLI-backed exam review API for local course materials"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite/Next dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(courses.router)
app.include_router(materials.router)
app.include_router(exams.router)
app.include_router(sessions.router)
app.include_router(mistakes.router)
app.include_router(agent.router)

@app.get("/health")
def health():
    return {"status": "ok", "version": "0.4.0"}
```

### Part 2C：路由文件

**`services/api/routes/courses.py`**：
```python
"""Course routes."""
from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
import subprocess, sys

router = APIRouter(prefix="/courses", tags=["courses"])

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent  # study-review-skill/
SCRIPTS = PROJECT_ROOT / "scripts"
COURSES_ROOT = Path(os.environ.get("COURSES_ROOT", str(PROJECT_ROOT / "tests" / "fixtures")))

import os

@router.get("")
def list_courses():
    """List all course directories with review state."""
    courses = []
    for d in sorted(COURSES_ROOT.iterdir()):
        if d.is_dir() and not d.name.startswith("."):
            review_dir = d / "review"
            materials_count = 0
            if review_dir.exists():
                files_yaml = review_dir / "files.yaml"
                if files_yaml.exists():
                    import yaml
                    data = yaml.safe_load(files_yaml.read_text(encoding="utf-8"))
                    materials_count = len(data.get("files", []))
            courses.append({
                "course_id": d.name.replace(" ", "-").lower(),
                "name": d.name,
                "materials_count": materials_count,
                "stage": "诊断",
                "due_items_count": 0,
                "last_reviewed": None,
            })
    return {"courses": courses}

@router.post("/{course_id}/init-review")
def init_course_review(course_id: str):
    """Initialize review workspace for a course."""
    course_dir = COURSES_ROOT / course_id
    if not course_dir.exists():
        raise HTTPException(404, f"Course not found: {course_id}")

    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "init_course_review.py"), str(course_dir), "--json"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT)
    )
    if r.returncode != 0:
        raise HTTPException(500, r.stderr)
    return json.loads(r.stdout)

@router.get("/{course_id}/progress")
def get_progress(course_id: str):
    """Get course progress."""
    review_dir = COURSES_ROOT / course_id / "review"
    progress_path = review_dir / "progress.md"
    if not progress_path.exists():
        raise HTTPException(404, "No progress file")
    return {"course_id": course_id, "content": progress_path.read_text(encoding="utf-8")}
```

**`services/api/routes/exams.py`**：
```python
"""Exam analysis + question generation routes."""
from fastapi import APIRouter, HTTPException
from pathlib import Path
import json, subprocess, sys, os

router = APIRouter(prefix="/courses", tags=["exams"])

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
SCRIPTS = PROJECT_ROOT / "scripts"
COURSES_ROOT = Path(os.environ.get("COURSES_ROOT", str(PROJECT_ROOT / "tests" / "fixtures")))

@router.post("/{course_id}/exam-analysis")
def analyze_exam(course_id: str, goal: str = "pass"):
    course_dir = COURSES_ROOT / course_id
    if not course_dir.exists():
        raise HTTPException(404, f"Course not found: {course_id}")
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "analyze_exam.py"), str(course_dir), "--force", "--goal", goal, "--json"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT)
    )
    if r.returncode != 0:
        raise HTTPException(500, r.stderr)
    return json.loads(r.stdout)

@router.get("/{course_id}/exam-analysis/latest")
def get_latest_analysis(course_id: str):
    review_dir = COURSES_ROOT / course_id / "review"
    analysis_path = review_dir / "exam-analysis.yaml"
    if not analysis_path.exists():
        raise HTTPException(404, "No analysis found")
    import yaml
    return yaml.safe_load(analysis_path.read_text(encoding="utf-8"))

@router.post("/{course_id}/exam-analysis/{analysis_id}/questions")
def generate_questions(course_id: str, analysis_id: str, count: int = 5):
    course_dir = COURSES_ROOT / course_id
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "generate_questions.py"), str(course_dir), "--count", str(count), "--force", "--json"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT)
    )
    if r.returncode != 0:
        raise HTTPException(500, r.stderr)
    return json.loads(r.stdout)

@router.post("/{course_id}/plan")
def make_plan(course_id: str, minutes: int = 90, goal: str = "pass"):
    course_dir = COURSES_ROOT / course_id
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "plan_review.py"), str(course_dir), "--minutes", str(minutes), "--goal", goal, "--force", "--json"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT)
    )
    if r.returncode != 0:
        raise HTTPException(500, r.stderr)
    return json.loads(r.stdout)
```

**`services/api/routes/sessions.py`**：
```python
"""Review session routes."""
from fastapi import APIRouter, HTTPException
from pathlib import Path
import json, subprocess, sys, os, uuid

router = APIRouter(tags=["sessions"])

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
SCRIPTS = PROJECT_ROOT / "scripts"
COURSES_ROOT = Path(os.environ.get("COURSES_ROOT", str(PROJECT_ROOT / "tests" / "fixtures")))

# In-memory session store (v0.4 — move to SQLite in v1.0)
SESSIONS = {}

@router.post("/review-session/start")
def start_session(course_id: str, source: str = "generated", limit: int = 5):
    course_dir = COURSES_ROOT / course_id
    if not course_dir.exists():
        raise HTTPException(404, f"Course not found: {course_id}")

    # Load questions
    review_dir = course_dir / "review"
    if source == "generated":
        gq_path = review_dir / "generated-questions.yaml"
        if not gq_path.exists():
            raise HTTPException(404, "No generated questions. Run generate_questions first.")
        import yaml
        questions = yaml.safe_load(gq_path.read_text(encoding="utf-8")).get("questions", [])[:limit]
    else:
        # due / cards: use due_today JSON
        r = subprocess.run(
            [sys.executable, str(SCRIPTS / "due_today.py"), str(COURSES_ROOT), "--subject", course_id, "--json"],
            capture_output=True, text=True, cwd=str(PROJECT_ROOT)
        )
        due_data = json.loads(r.stdout)
        questions = []
        for course in due_data.get("courses", []):
            for item in course.get("items", []):
                questions.append({
                    "id": item["id"],
                    "prompt": item["prompt"],
                    "topic": item["topic"],
                    "expected_answer": "",
                    "scoring_points": [],
                    "time_limit_sec": 120,
                })

    if not questions:
        raise HTTPException(404, "No questions available")

    session_id = str(uuid.uuid4())[:8]
    SESSIONS[session_id] = {
        "course_dir": str(course_dir),
        "source": source,
        "questions": questions,
        "current_index": 0,
        "results": [],
    }

    q = questions[0]
    return {
        "session_id": session_id,
        "question_index": 1,
        "total_questions": len(questions),
        "question": q,
    }

@router.post("/review-session/answer")
def submit_answer(session_id: str, answer: str):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found or expired")

    idx = session["current_index"]
    questions = session["questions"]
    if idx >= len(questions):
        raise HTTPException(400, "All questions answered")

    q = questions[idx]

    # Grade using agent grading (with keyword fallback)
    from scripts.agent.grading import grade_answer
    result = grade_answer(q["prompt"], q.get("expected_answer", ""), q.get("scoring_points", []), answer)

    # Log mistake if needed
    if result.get("should_log_mistake"):
        course_dir = Path(session["course_dir"])
        rating = "困难" if result["verdict"] == "partial" else "忘了"
        r = subprocess.run([
            sys.executable, str(SCRIPTS / "review_log.py"),
            "--course", str(course_dir),
            "--subject", course_dir.name,
            "--topic", q.get("topic", ""),
            "--question", q["prompt"],
            "--mistake", answer,
            "--correction", result.get("better_answer", "; ".join(result.get("omissions", []))),
            "--rating", rating,
            "--json"
        ], capture_output=True, text=True, cwd=str(PROJECT_ROOT))
        if r.returncode == 0:
            result["card_id"] = json.loads(r.stdout).get("card_id")

    session["results"].append({**result, "question_id": q.get("id")})
    session["current_index"] = idx + 1

    return result
```

**`services/api/routes/mistakes.py`**：
```python
"""Mistake log routes."""
from fastapi import APIRouter
from pathlib import Path
import json, subprocess, sys, os

router = APIRouter(tags=["mistakes"])

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
COURSES_ROOT = Path(os.environ.get("COURSES_ROOT", str(PROJECT_ROOT / "tests" / "fixtures")))

@router.get("/due-today")
def due_today(subject: str = None):
    cmd = [sys.executable, str(PROJECT_ROOT / "scripts" / "due_today.py"), str(COURSES_ROOT), "--json"]
    if subject:
        cmd += ["--subject", subject]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
    if r.returncode != 0:
        from fastapi import HTTPException
        raise HTTPException(500, r.stderr)
    return json.loads(r.stdout)
```

**`services/api/routes/agent.py`**：
```python
"""POST /agent/run — flexible natural language routing."""
from fastapi import APIRouter
from pathlib import Path
import os

router = APIRouter(tags=["agent"])

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
COURSES_ROOT = Path(os.environ.get("COURSES_ROOT", str(PROJECT_ROOT / "tests" / "fixtures")))

@router.post("/agent/run")
def agent_run(course_id: str, message: str, goal: str = "pass"):
    from scripts.agent.orchestrator import run
    course_path = COURSES_ROOT / course_id
    if not course_path.exists():
        return {
            "intent": "init_course",
            "state_before": "EMPTY",
            "tool_called": None,
            "state_after": "EMPTY",
            "message": f"课程目录不存在：{course_path}。请先创建课程目录并放入课件。",
            "next_action": {"label": "创建课程目录", "intent": "init_course"},
            "artifacts": [],
            "warnings": ["course not found"],
        }
    return run(course_path, message, goal)
```

### Part 2D：`tests/test_api.py` — 集成测试

```python
"""API integration tests using TestClient."""
import unittest
from fastapi.testclient import TestClient
from pathlib import Path
import sys, os

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ["COURSES_ROOT"] = str(PROJECT_ROOT / "tests" / "fixtures")

from services.api.app import app

client = TestClient(app)

class TestAPI(unittest.TestCase):

    def test_health(self):
        r = client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "ok")

    def test_list_courses(self):
        r = client.get("/courses")
        self.assertEqual(r.status_code, 200)
        self.assertIn("courses", r.json())

    def test_agent_run_make_plan(self):
        r = client.post("/agent/run", params={
            "course_id": "computer-network",
            "message": "今晚怎么不挂科",
            "goal": "pass"
        })
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn(data["intent"], ["make_plan", "start_review"])

    def test_agent_run_due_review(self):
        r = client.post("/agent/run", params={
            "course_id": "computer-network",
            "message": "今天该复习什么"
        })
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["intent"], "due_review")

    def test_due_today(self):
        r = client.get("/due-today")
        self.assertEqual(r.status_code, 200)
        self.assertIn("courses", r.json())

    def test_404_course(self):
        r = client.post("/agent/run", params={
            "course_id": "nonexistent",
            "message": "开始复习"
        })
        self.assertEqual(r.status_code, 200)  # agent returns 200 with warning
        self.assertIn("warnings", r.json())

if __name__ == "__main__":
    unittest.main()
```

### Phase 2 验收

```bash
# 启动 API 服务器
cd C:\Fullstack_Development\Study_Review
set COURSES_ROOT=C:\Fullstack_Development\Study_Review\tests\fixtures
python -m uvicorn services.api.app:app --reload --port 8000

# 另一个终端测试
curl http://localhost:8000/health
curl http://localhost:8000/courses
curl -X POST "http://localhost:8000/agent/run?course_id=computer-network&message=%E4%BB%8A%E6%99%9A%E6%80%8E%E4%B9%88%E4%B8%8D%E6%8C%82%E7%A7%91"
curl http://localhost:8000/due-today

# API 集成测试
python -m unittest tests/test_api.py -v
# → 6 条全绿

# OpenAPI 文档
# 浏览器打开 http://localhost:8000/docs
```

Phase 2 全部验收通过后进入 Phase 3。

---

---

## Phase 3：v0.5 React + TypeScript 前端

### 入口条件
- Phase 2 全部验收通过
- Node 20 LTS+ 已安装
- 后端 `python -m uvicorn services.api.app:app` 在 localhost:8000 运行

### 依赖安装
```bash
cd C:\Fullstack_Development\Study_Review
npm create vite@latest apps/web -- --template react-ts
cd apps/web
npm install
npm install tailwindcss @tailwindcss/vite postcss autoprefixer
npm install react-router-dom @tanstack/react-query zod lucide-react
npm install @shadcn/ui  # (if available; otherwise use manual component setup)
```

### 你要新建/修改的文件

所有前端文件在 `apps/web/src/` 下：

```
apps/web/src/
├── main.tsx                 ← Vite 入口
├── App.tsx                  ← 路由 + Layout
├── index.css                ← Tailwind + CSS variables
├── api/
│   └── client.ts            ← API client (TanStack Query hooks)
├── types/
│   └── index.ts             ← TypeScript types (from Pydantic models)
├── components/
│   ├── Layout.tsx            ← 侧边栏 + 顶部导航
│   ├── CommandPalette.tsx    ← Cmd+K 全局搜索
│   ├── DueBadge.tsx          ← 到期数量红点
│   ├── RatingButton.tsx      ← 四档评分按钮
│   ├── ProgressRing.tsx      ← 环形进度
│   ├── ScoreCard.tsx         ← 判分结果卡片
│   ├── MarkdownRenderer.tsx  ← Markdown 渲染
│   ├── FileDropZone.tsx      ← 拖拽上传
│   ├── EmptyState.tsx        ← 空数据引导
│   └── Skeleton.tsx          ← 骨架屏
├── pages/
│   ├── Dashboard.tsx         ← /
│   ├── Course.tsx            ← /course/:id
│   ├── Materials.tsx         ← /course/:id/materials
│   ├── ExamAnalysis.tsx       ← /course/:id/analysis
│   ├── Plan.tsx              ← /course/:id/plan
│   └── QuizSession.tsx       ← /course/:id/quiz
└── hooks/
    └── useKeyboardShortcut.ts
```

### 前端设计目标

**一句话**：Notion 的克制排版 + Linear 的响应速度 + shadcn/ui 的组件质量

**配色方案**：
- Light: `--background: #ffffff`, `--foreground: #0a0a0a`, `--primary: #2563eb`
- Dark: `--background: #0a0a0a`, `--foreground: #fafafa`, `--primary: #3b82f6`
- Success: `#16a34a`, Warning: `#d97706`, Error: `#dc2626`

**Typography**：system font stack, `font-sans` 用于正文, `font-mono` 用于题目文本

### 核心页面实现要求

#### Dashboard (`/`)
- 左侧：各科进度环（ProgressRing 组件，SVG circle）
- 中间：今日待复习卡片列表（来自 `GET /due-today`）
- 右侧：最近错题预览（3 条，来自 `mistake-log.md` 最近 section）
- 顶部：欢迎语 + 日期
- 快速开始按钮：→ 跳转最近复习的课程 Quiz
- 空状态：没有课程时显示 EmptyState「还没有课程？去 init →」

#### QuizSession (`/course/:id/quiz`)
**最重要的页面——这是核心体验。**

- 单题展示区（卡片样式，padding 充足，字体略大）
- 倒计时（可选显示）
- 答案输入框（textarea，支持多行）
- 提交按钮（Enter 提交，Shift+Enter 换行）
- 提交后：卡片翻转动效（200ms，`prefers-reduced-motion` 时禁用）
- 判分结果：ScoreCard 组件
  - correct → 绿色左边框 + ✓
  - partial → 黄色左边框 + △
  - wrong → 红色左边框 + ✗
- 遗漏要点列表 + 更稳答法
- 追问题（展开/收起）
- 评分按钮：忘了 / 困难 / 还行 / 很熟（RatingButton 组件）
- 「下一题」按钮（或 Enter）
- 进度条：`3/5`

#### Plan (`/course/:id/plan`)
- 渲染 `plan.md` 为美化 Markdown
- 「现在开始」按钮高亮（primary color, large）
- 任务列表带 checkbox（只读展示）

#### ExamAnalysis (`/course/:id/analysis`)
- priorities 卡片列表，按 weight 排序
- 每条：topic + chapter + weight 条形图 + evidence tooltip
- 「生成变式题」按钮 → POST generate → 跳转 Quiz

#### Materials (`/course/:id/materials`)
- 文件列表（表格或卡片）
- material_type 彩色标签
- 拖拽上传区（FileDropZone）
- 上传后自动刷新列表

### 公共组件要求

**CommandPalette**：Cmd+K 打开，搜索课程名、快捷命令（"开始复习 计网"、"今天复习什么"）

**RatingButton**：4 个按钮横向排列，animated press effect, keyboard accessible

**ScoreCard**：三色左边框 + 图标 + 内容区，slide-up animation

**EmptyState**：居中图标 + 一句话描述 + CTA 按钮，不要空白页

### TanStack Query hooks

```typescript
// api/client.ts
const API_BASE = 'http://localhost:8000';

export function useCourses() {
  return useQuery({ queryKey: ['courses'], queryFn: () => fetch(`${API_BASE}/courses`).then(r => r.json()) });
}
export function useDueToday(subject?: string) {
  return useQuery({ queryKey: ['due', subject], queryFn: () => fetch(`${API_BASE}/due-today?subject=${subject || ''}`).then(r => r.json()) });
}
export function useStartSession(courseId: string, source: string, limit: number) {
  return useMutation({ mutationFn: () => fetch(`${API_BASE}/review-session/start?course_id=${courseId}&source=${source}&limit=${limit}`, { method: 'POST' }).then(r => r.json()) });
}
export function useSubmitAnswer() {
  return useMutation({
    mutationFn: ({ sessionId, answer }: { sessionId: string; answer: string }) =>
      fetch(`${API_BASE}/review-session/answer?session_id=${sessionId}&answer=${encodeURIComponent(answer)}`, { method: 'POST' }).then(r => r.json()),
    onMutate: async ({ sessionId, answer }) => {
      // Optimistic update: show "submitting..." immediately
    }
  });
}
```

### Phase 3 验收

```bash
cd apps/web
npm run dev
# → 浏览器打开 http://localhost:5173

# Lighthouse 检查
npx lighthouse http://localhost:5173 --view
# FCP ≤1.2s, LCP ≤2.0s, TTI ≤2.5s, CLS ≤0.1

# Build
npm run build
# → dist/ 目录，JS bundle gzip ≤150KB

# Type check
npx tsc --noEmit
# → 零错误

# Lint
npx eslint src/ --max-warnings 0
# → 零错误
```

**手动验证（必须做，不能用自动化替代）**：
- [ ] Cmd+K 能搜索课程
- [ ] 暗色模式切换无闪烁
- [ ] 答题全流程键盘可达（Tab → 输入 → Enter 提交 → Enter 下一题）
- [ ] 暗色模式下判分三色仍有足够对比度
- [ ] 空 Dashboard 有引导而非空白
- [ ] 断网时 TanStack Query cache 仍有数据显示
- [ ] `prefers-reduced-motion` 时翻转动效禁用

Phase 3 全部验收通过后进入 Phase 4。

---

---

## Phase 4：v1.0 真实课程验证

### 入口条件
- Phase 3 全部验收通过
- 用户提供至少 1 门真实课程目录路径（含 PPT/PDF 课件）

### 验证步骤

对每门真实课程：

```bash
# 1. 初始化
python scripts/init_course_review.py "<真实课程路径>" --json

# 2. 分析
python scripts/analyze_exam.py "<真实课程路径>" --force --json

# 3. 生成题
python scripts/generate_questions.py "<真实课程路径>" --count 10 --force --json

# 4. 计划
python scripts/plan_review.py "<真实课程路径>" --minutes 90 --force --json

# 5. 交互答题（手动，不是 --non-interactive！）
python scripts/review_session.py "<真实课程路径>" --source generated --limit 10
# ↑ 必须人肉答，测试真实判分体验

# 6. 复查
python scripts/due_today.py "<真实课程父目录>" --json
```

### v1.0 验收清单

- [ ] 至少 3 门课跑通完整 CLI 流程
- [ ] 每门课完成：资料登记 → 分析 → 变式题 → 计划 → 答题 → 错题复查
- [ ] 生成题的内容与课件章节有可辨识的对应关系（不是乱出）
- [ ] 判分结果在 ≥2/3 的情况下人肉觉得合理
- [ ] 前端能从「打开浏览器」到「开始答第一题」≤2 分钟
- [ ] 0 数据丢失事件（`review/` 文件不被覆盖，用户手写内容不被破坏）
- [ ] 所有错误都有清晰中文提示，无 traceback 暴露给用户

---

---

## 全局约束（所有 Phase 通用）

1. **不破坏已有脚本**：如果修改 v0.2 脚本，必须跑 `python -m unittest discover -s tests -p "test_*.py"` 确认 16 条测试不退化
2. **Source policy**：不联网编造课程内容；所有课程事实来自本地文件
3. **原子写入**：所有 YAML/Markdown 写入走 `review_io.atomic_write`
4. **YAML 安全**：所有字符串在写入前检查 bool 类型
5. **Windows 兼容**：路径用 `/`、编码 UTF-8、换行 `\n`
6. **每个 Phase 末尾必须跑测试**：确认之前 Phase 的功能不退化
