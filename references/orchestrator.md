# Study Review Orchestrator

This document defines the agent layer. The first version should use one control agent plus deterministic tools, not multiple autonomous agents.

## Architecture

```text
Frontend / User
  -> API Layer
  -> StudyReviewOrchestrator
  -> Tool Layer
       - CourseInventoryTool
       - MaterialIngestTool
       - PastExamAnalysisTool
       - MaterialMatcherTool
       - QuestionGenerationTool
       - ReviewPlannerTool
       - QuizGradingTool
       - MistakeLogTool
       - DueReviewTool
  -> Storage Layer
       - files.yaml
       - progress.md
       - exam-analysis.yaml
       - past-exam-patterns.yaml
       - generated-questions.yaml
       - cards.yaml
       - mistake-log.md
```

## Why Single Orchestrator First

The product flow is mostly linear:

```text
upload materials
  -> analyze materials / exams
  -> find priorities
  -> plan review
  -> generate questions
  -> grade answers
  -> record mistakes
  -> review due items
```

This does not require multiple agents in the first version. Multiple agents would add debugging cost before the data formats and tool contracts are stable.

Use one orchestrator to decide, and tools to execute.

## Responsibilities

`StudyReviewOrchestrator` is the only entry agent.

It should:

1. Understand the user's goal: pass, high score, tonight review, exam analysis, question generation, mistake review.
2. Detect the current state of the course.
3. Choose the next mode: upload intake, past exam analysis, planning, active recall, problem solving, or due review.
4. Call the right tool or backend service.
5. Merge tool results into a concrete next action.
6. Preserve the source policy.
7. Ask for missing information only when needed.
8. Never fabricate course facts or pretend unavailable tools exist.

## State Machine

```text
EMPTY
  No course or materials.

COURSE_CREATED
  Course exists, but review materials are missing or insufficient.

MATERIALS_READY
  Materials are uploaded or visible locally, but not analyzed.

EXAM_ANALYZED
  Past exams or sample papers have been analyzed.

PLAN_READY
  A time-boxed review plan exists.

IN_REVIEW
  The user is answering questions or drilling.

REVIEW_DUE
  Mistakes or cards are due for review.
```

State transitions:

```text
EMPTY -> COURSE_CREATED
COURSE_CREATED -> MATERIALS_READY
MATERIALS_READY -> EXAM_ANALYZED
EXAM_ANALYZED -> PLAN_READY
PLAN_READY -> IN_REVIEW
IN_REVIEW -> REVIEW_DUE
REVIEW_DUE -> IN_REVIEW
```

The orchestrator can skip states when enough local data already exists.

## Intent Routing

### upload_materials

Use when the user uploads files or asks where to submit materials.

Actions:

1. Create or select course.
2. Register files and file types.
3. Save file metadata to `files.yaml`.
4. Suggest next action: analyze past exams, generate plan, or start diagnostic.

### analyze_exam

Use when the user mentions papers, past exams, sample papers, or "根据试卷分析重点".

Actions:

1. Locate exam-like files.
2. Locate supporting course materials.
3. Call `PastExamAnalysisTool`.
4. Call `MaterialMatcherTool`.
5. Return priorities, patterns, variants, and a plan.

### find_key_points

Use when the user asks what to review or where a knowledge point appears.

Actions:

1. Search indexed materials or inspect filenames if no index exists.
2. Rank sources by material priority.
3. Return concise priorities with filenames.

### generate_questions

Use when the user asks for practice, quiz, variants, or a mock paper.

Actions:

1. Prefer `past-exam-patterns.yaml`.
2. Fall back to local slides, notes, and homework answers.
3. Generate questions with expected answers and scoring points.
4. Mark generated items as `模拟题` or `变式题`.

### make_plan

Use when the user asks "今晚怎么复习", "怎么不挂科", or gives exam date/time budget.

Actions:

1. Read priorities, mistakes, and due items.
2. Generate 30-minute, 90-minute, 3-day, or 7-day plan.
3. End with the first concrete review action.

### start_review

Use when the user is ready to practice.

Actions:

1. Start with diagnostic or due items.
2. Ask one question at a time.
3. Wait for the user's answer.

### grade_answer

Use after the user answers.

Actions:

1. Grade as correct, partially correct, or wrong.
2. Show key points and omissions.
3. Ask a follow-up question.
4. Record mistakes when useful.

### due_review

Use when the user asks "今天该复习什么" or when due items exist.

Actions:

1. Call `DueReviewTool`.
2. Group by course and priority.
3. Start with overdue mistakes before new content.

## Tool Contracts

### CourseInventoryTool

Input:

```yaml
workspace_path: string
```

Output:

```yaml
courses:
  - course_id: string
    name: string
    files:
      - path: string
        guessed_type: string
```

### MaterialIngestTool

Input:

```yaml
course_id: string
files:
  - path: string
    material_type: slides | past_exam | mock_exam | homework_answer | teacher_focus | notes | textbook | other
```

Output:

```yaml
files_yaml_path: string
registered_files:
  - id: string
    path: string
    material_type: string
```

### PastExamAnalysisTool

Input:

```yaml
course_id: string
exam_file_ids:
  - string
material_file_ids:
  - string
goal: pass | score_high
time_budget_minutes: integer
```

Output:

```yaml
patterns: []
priorities: []
generated_questions: []
plan: {}
```

### ReviewPlannerTool

Input:

```yaml
course_id: string
exam_date: string
available_minutes: integer
priorities: []
mistakes: []
```

Output:

```yaml
tasks:
  - title: string
    source: string
    duration_minutes: integer
    mode: recall | practice | read | review_mistake
fallback_plan:
  - string
```

### QuizGradingTool

Input:

```yaml
question: string
expected_answer: string
scoring_points:
  - string
user_answer: string
```

Output:

```yaml
verdict: correct | partial | wrong
key_points:
  - string
omissions:
  - string
better_answer: string
follow_up_question: string
```

## Frontend Event Contract

The frontend should send user actions as explicit intents:

```json
{
  "intent": "analyze_exam",
  "courseId": "computer-network",
  "fileIds": ["exam-2024-a", "summary-ppt"],
  "goal": "pass",
  "availableMinutes": 90
}
```

The orchestrator returns structured results:

```json
{
  "nextView": "exam_analysis",
  "message": "已识别 4 类高频题型。",
  "priorities": [],
  "questions": [],
  "plan": []
}
```

## Source Policy

The orchestrator must preserve the default source policy:

```text
Only read and rely on files inside /Users/bosprimigenious/Important_FIles/2025-2026下.
Do not use web search, GitHub, external websites, repository-external files, or model memory as factual sources.
If the answer is not supported by workspace files, say the workspace materials are insufficient.
```

External research may inform product design only when the user explicitly allows it. It must not be used to answer course-content questions.

## Failure Handling

If materials are missing:

- say what is missing
- ask for the most useful next upload
- offer a fallback based on available files

If file extraction fails:

- keep the file registered
- mark status as failed
- ask the user to upload a clearer file or use another source

If analysis confidence is low:

- say why
- show source coverage
- avoid strong claims
- recommend diagnostic questions instead

If a tool does not exist yet:

- do not pretend it ran
- describe the intended next implementation step
- use manual inspection only if it is reliable from available files

## Future Multi-Agent Split

Only split into multiple agents after the single orchestrator and tools are stable.

Possible future agents:

- `ExamAnalystAgent`
- `QuestionWriterAgent`
- `TutorAgent`
- `PlannerAgent`

Do not introduce them in the first version unless tool complexity forces the split.
