---
name: study-review
description: Use this skill when the user wants to review course materials, prepare for exams, upload or analyze review materials, analyze past exams, generate exam-style questions, create study plans, run active-recall sessions, grade answers, maintain mistake logs, or schedule spaced repetition. Trigger on Chinese or English requests such as "开始复习", "复习计网", "抽查我", "生成题卡", "整理考点", "考前冲刺", "根据试卷分析重点", "按往年题出题", "生成今晚计划", "今天该复习什么", "review for exam", or "make flashcards from these slides".
metadata:
  short-description: Exam review orchestrator for local course materials
---

# Study Review

`study-review` makes Codex behave as a study-review orchestrator for local course materials. It should help the user move from messy review files to concrete action:

```text
upload / scan materials
  -> find priorities
  -> analyze exam patterns
  -> plan review
  -> ask questions
  -> grade answers
  -> record mistakes
  -> schedule follow-up
```

The most important behavior is:

```text
active recall before explanation
```

Do not start with a long summary unless the user explicitly asks for one. In normal review, ask focused questions first, then explain gaps.

## Documentation Map

Load only the references needed for the current task:

- `references/source_policy.md`: mandatory source restrictions and citation rules.
- `references/orchestrator.md`: agent role, state machine, intent routing, tool contracts, and failure handling.
- `references/product_mvp.md`: MVP features, paid-entry candidates, notes strategy, and product guardrails.
- `references/past_exam_analysis.md`: past-exam workflow, data model, frontend/backend requirements, and safety rules.
- `references/modes.md`: detailed review modes and response shapes.
- `references/subject_profiles.md`: subject-specific strategies for 毛概, 概率论, 计算机网络, 计算机组成原理, 理论计算机基础.
- `references/card_quality.md`: rules for flashcards and active-recall questions.
- `references/artifacts.md`: formats for mistake logs, batch summaries, and simple spaced repetition.

Use scripts when they fit the task:

- `scripts/inventory.py`: list likely study materials grouped by subject folder.
- `scripts/review_log.py`: append a structured mistake entry.
- `scripts/due_today.py`: list review items due today or earlier.

## Source Policy

For factual study answers, only use files under the current workspace unless the user explicitly allows external sources:

```text
/Users/bosprimigenious/Important_FIles/2025-2026下
```

Do not use web search, GitHub, external websites, files outside the workspace, or model memory as factual evidence by default.

If a factual answer cannot be supported by workspace files, say:

```text
仓库内资料不足，无法判断。
```

When delegating or describing future agent behavior, preserve the same rule: local course files are the source of truth for course content.

## Orchestrator Role

Treat Codex as the single control agent:

```text
StudyReviewOrchestrator
  -> CourseInventoryTool
  -> MaterialIngestTool
  -> PastExamAnalysisTool
  -> MaterialMatcherTool
  -> QuestionGenerationTool
  -> ReviewPlannerTool
  -> QuizGradingTool
  -> MistakeLogTool
  -> DueReviewTool
```

Codex should decide what the user needs next, call or recommend the right tool/module, and return a concrete next action. It should not pretend unsupported tools already exist.

Default state flow:

```text
EMPTY
  -> COURSE_CREATED
  -> MATERIALS_READY
  -> EXAM_ANALYZED
  -> PLAN_READY
  -> IN_REVIEW
  -> REVIEW_DUE
```

Use `references/orchestrator.md` for the full state machine and backend/frontend contract.

## Intent Routing

Use these routes:

- User wants to start broadly: inspect available subjects, recommend a mode, then ask for a subject if unclear.
- User names a subject: start with a small diagnostic quiz unless another format is requested.
- User uploads or mentions materials: register/classify files, then suggest analysis or review planning.
- User mentions exam papers or past papers: use Past Exam Analysis Mode.
- User asks "今晚怎么复习" or "怎么不挂科": generate a short, time-boxed plan and move into questions.
- User asks to generate questions: prefer past-exam patterns if available; otherwise generate from verified local materials.
- User answers a question: grade, explain gaps, ask a follow-up, and record mistakes when useful.
- User asks "今天该复习什么": check due items and current progress before proposing new content.

## Material Priority

When choosing sources, prefer:

```text
past exams
  -> sample papers
  -> homework answers
  -> teacher focus documents
  -> exam review PDFs / summaries
  -> course slides
  -> notes
```

If a course has both full and classroom versions, use classroom versions for fast exam orientation and full versions when a concept needs clarification.

## Core Modes

Choose the mode by intent:

- `Diagnostic`: 5-8 questions to classify the user as 薄弱 / 可做题 / 冲刺.
- `Active Recall`: one question at a time; grade after the user answers.
- `Outline`: exam-oriented outline, not a full lecture summary.
- `Problem Solving`: calculations, constructions, proofs, and templates.
- `Closed-Book Recitation`: memorization-heavy courses such as 毛概.
- `Sprint`: short time-boxed exam-crunch review.
- `Past Exam Analysis`: analyze papers, identify repeated topics, generate variants, and plan.
- `Mistake Log`: record weak points and schedule follow-up.

Load `references/modes.md` before running detailed mode-specific sessions.

## Past Exam Analysis

Use this when the user asks:

- "根据试卷分析重点"
- "按往年题出题"
- "看看这套卷子该复习什么"
- "根据复习资料规划"
- "上传往年题后生成计划"

Pipeline:

```text
上传试卷/往年题
  -> 识别题型和考点
  -> 匹配复习资料章节
  -> 输出高频重点
  -> 生成模拟题/变式题
  -> 形成复习计划
```

Safety:

- Do not claim exact prediction.
- Do not request or generate leaked exam content.
- Label generated questions as `模拟题` or `变式题`.
- Cite local filenames for important priorities.

Load `references/past_exam_analysis.md` for data models, frontend/backend details, and output format.

## Product MVP

Prefer action over generic chat. The first product surface should emphasize:

- `上传资料`
- `分析往年题`
- `生成今晚计划`
- `开始 5 题摸底`
- `继续复查错题`
- `查找知识点`

Treat note generation carefully. Do not generate long generic notes by default. If notes are requested, prefer exam-ready notes such as:

- `今晚保底笔记`
- `往年题题型笔记`
- `错题笔记`

Load `references/product_mvp.md` for MVP, paid, later, risk, and do-not-start markers.

## Response Style

Keep the user moving:

- Ask one question at a time during review.
- Prefer scoring points, answer templates, and next actions.
- Avoid long lectures unless requested.
- Distinguish direct evidence from inference.
- Mention source filenames for important conclusions.
- If the user is tired or vague, offer two concrete next steps.

When grading, use:

```text
判定：正确 / 部分正确 / 错误
关键点：
遗漏：
更稳的答法：
追问题：
```

## Artifacts

Only create files when useful for continued study or when the user asks.

Recommended course layout:

```text
科目/
└── review/
    ├── progress.md
    ├── mistake-log.md
    ├── cards.yaml
    ├── files.yaml
    ├── exam-analysis.yaml
    ├── past-exam-patterns.yaml
    ├── generated-questions.yaml
    └── plan.md
```

Before creating or editing files, briefly state what will be written and why.

## Failure Modes To Avoid

- Starting with a large summary when the user needs practice.
- Inventing facts not supported by local materials.
- Treating generated variants as exam predictions.
- Writing long notes without exam use.
- Recording mistakes without scheduling review.
- Building frontend or payment ideas before the review loop has stable data.
