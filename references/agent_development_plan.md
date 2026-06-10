# Agent Development Plan

This document explains how to build the agent layer for Study Review. It expands `references/orchestrator.md` into an engineering plan.

## Development Principle

The MVP should use:

```text
one total-control agent
  + deterministic Python tools
  + local YAML/Markdown state
  + strict source policy
```

Do not start with many autonomous agents. The first product problem is not agent collaboration. The first problem is making the review loop reliable:

```text
materials -> exam analysis -> priorities -> questions -> plan -> answer -> mistake -> due review
```

## Agent Goal

The agent should make the user feel:

```text
I uploaded messy review materials.
The system understood what exists.
It found the most test-relevant parts.
It told me what to do tonight.
It asked me questions one by one.
It remembered what I got wrong.
It brought those mistakes back before the exam.
```

The agent is valuable only when it moves the user from anxiety to action.

## Runtime Contract

The agent must always answer these internal questions before acting:

1. What course is the user working on?
2. What local materials exist?
3. Is there past exam or sample-paper evidence?
4. Does a review plan already exist?
5. Are there generated questions?
6. Are any mistakes due?
7. What is the next smallest useful action?

If the answer is unknown, inspect local state or ask the user for the missing input. Do not invent course facts.

## Agent Loop

Every agent turn should follow this loop:

```text
receive user request
  -> classify intent
  -> inspect course state
  -> choose next action
  -> call one tool or ask one clarifying question
  -> validate tool output
  -> respond with next concrete action
  -> persist state only through tools
```

The agent should avoid doing many hidden steps at once in early versions. A short, visible chain is easier to debug.

## Core Intents

The first version only needs these intents:

| Intent | User examples | Required state | Primary tool |
| --- | --- | --- | --- |
| `init_course` | 这门课开始复习 | course folder exists | `init_course_review.py` |
| `analyze_exam` | 根据试卷分析重点 | `files.yaml` has exam-like files | `analyze_exam.py` |
| `generate_questions` | 按往年题出题 | `exam-analysis.yaml` or patterns exist | `generate_questions.py` |
| `make_plan` | 今晚怎么不挂 | priorities or materials exist | `plan_review.py` |
| `start_review` | 开始刷题 | generated questions or due cards exist | `review_session.py` |
| `grade_answer` | user submitted answer | active question exists | `QuizGradingTool` |
| `log_mistake` | answer is wrong or partial | graded answer exists | `review_log.py` |
| `due_review` | 今天复习什么 | cards or mistake log exists | `due_today.py` |

Do not add broad chat intents until these are reliable.

## State Inspection

Before deciding, the orchestrator should read a compact course snapshot.

Minimum snapshot:

```yaml
course_id: string
course_path: string
review_dir_exists: boolean
files_yaml_exists: boolean
materials_count:
  slides: integer
  past_exam: integer
  mock_exam: integer
  homework_answer: integer
  teacher_focus: integer
  notes: integer
exam_analysis_exists: boolean
generated_questions_count: integer
plan_exists: boolean
due_items_count: integer
last_reviewed: string | null
next_action: string | null
```

The snapshot can first be assembled by scripts. Later it can become a backend service:

```text
GET /courses/{course}/state
```

## Tool Maturity Levels

Each tool should move through four levels.

| Level | Meaning | Requirement |
| --- | --- | --- |
| L0 | documented only | contract exists in `orchestrator.md` |
| L1 | CLI text | command runs and prints human-readable output |
| L2 | CLI JSON | supports `--json` for agent/API use |
| L3 | backend service | callable from FastAPI with tests |

MVP can ship when the P0 tools reach at least L1, with L2 for tools used by the frontend.

P0 maturity target:

| Tool | Script | MVP target |
| --- | --- | --- |
| Course initialization | `init_course_review.py` | L2 |
| Exam analysis | `analyze_exam.py` | L2 |
| Question generation | `generate_questions.py` | L2 |
| Emergency planning | `plan_review.py` | L2 |
| Review session | `review_session.py` | L1 first, L2 before frontend |
| Mistake logging | `review_log.py` | L2 |
| Due review | `due_today.py` | L2 |

## Prompt and Context Assembly

The agent prompt should be assembled from layers.

Stable instructions:

```text
SKILL.md
references/source_policy.md
references/orchestrator.md
```

Task-specific references:

```text
references/question_patterns.md
references/past_exam_analysis.md
references/product_mvp.md
references/data_formats.md
references/subject_profiles.md
```

Dynamic local state:

```text
COURSE/review/files.yaml
COURSE/review/progress.md
COURSE/review/exam-analysis.yaml
COURSE/review/past-exam-patterns.yaml
COURSE/review/generated-questions.yaml
COURSE/review/cards.yaml
COURSE/review/mistake-log.md
COURSE/review/plan.md
```

The agent should not load every raw PPT/PDF into context by default. It should first use metadata and analysis files, then inspect source files only when the next action requires evidence.

## Source Policy Enforcement

The source policy must be enforced in three places:

1. Prompt: tell the model not to use external facts for course content.
2. Tool layer: only expose files inside the workspace/course root.
3. Output validator: require source basis for priorities, generated questions, and plans.

For course-content claims, the output should include one of:

```yaml
source_basis:
  - file: string
    evidence: string
```

or:

```yaml
confidence: low
reason: "local materials are insufficient"
```

## Agent Output Shape

The orchestrator should return a compact structure.

```yaml
intent: analyze_exam | generate_questions | make_plan | start_review | grade_answer | due_review
state_before: EMPTY | COURSE_CREATED | MATERIALS_READY | EXAM_ANALYZED | PLAN_READY | IN_REVIEW | REVIEW_DUE
tool_called: string | null
state_after: string
message: string
next_action:
  label: string
  intent: string
  required_inputs:
    - string
artifacts:
  - path: string
    type: files | analysis | questions | plan | cards | mistakes
warnings:
  - string
```

The frontend can later map this into `nextView`.

## Review Session Design

The review session is the most important agent behavior because it turns a plan into action.

Session flow:

```text
load questions or due cards
  -> show one question
  -> receive answer
  -> grade answer
  -> show missing points
  -> ask follow-up or continue
  -> log mistake if needed
  -> update progress
```

Session state should be explicit:

```yaml
session:
  id: session-net-20260610-001
  course_id: computer-network
  source: generated
  started_at: "2026-06-10T20:00:00+08:00"
  current_index: 0
  question_ids:
    - q-net-001
    - q-net-002
  answered:
    - question_id: q-net-001
      verdict: partial
      logged_card_id: card-net-001
```

For MVP, session state can live in memory or a temporary YAML file. Before frontend work, it should become persistent.

## Grading Design

The grading agent should not just say right or wrong. It should classify the answer.

Verdicts:

```text
correct
partial
wrong
```

Feedback fields:

```yaml
verdict: partial
score_hint: "2/4 scoring points covered"
covered_points:
  - string
omissions:
  - string
better_answer: string
follow_up_question: string
should_log_mistake: true
```

For subjective courses, grading should focus on scoring points and missing keywords. For calculation-heavy courses, it should focus on conditions, formula choice, and steps.

## Planning Design

The planning agent must output tasks, not advice.

Bad:

```text
建议复习传输层和网络层。
```

Good:

```text
20 min: 背 TCP 拥塞控制四个阶段。
15 min: 做 2 道滑动窗口变式题。
10 min: 复查昨天错题 card-net-003。
5 min: 看最后 15 分钟清单。
现在开始：回答第 1 题。
```

Every plan must include:

- goal
- time budget
- evidence
- ordered tasks
- what to skip
- first action

## API Shape for Agent

The backend should eventually expose both direct endpoints and a flexible agent endpoint.

Direct endpoints:

```text
POST /courses/{course}/init-review
POST /courses/{course}/exam-analysis
POST /courses/{course}/questions
POST /courses/{course}/plan
POST /review-session/start
POST /review-session/answer
GET  /due-today
```

Flexible endpoint:

```text
POST /agent/run
```

Input:

```json
{
  "courseId": "computer-network",
  "message": "我今晚怎么不挂科",
  "goal": "pass",
  "availableMinutes": 90
}
```

Output:

```json
{
  "intent": "make_plan",
  "nextView": "plan",
  "message": "已生成 90 分钟保底计划。",
  "artifacts": [
    { "path": "计算机网络/review/plan.md", "type": "plan" }
  ],
  "nextAction": {
    "label": "开始第 1 题",
    "intent": "start_review"
  }
}
```

## Evaluation Plan

The agent needs evaluation before it needs more framework.

Minimum eval cases:

1. User has no review directory.
   - Expected: initialize or ask to choose course.
2. User has materials but no exam analysis.
   - Expected: suggest analyzing past exams or generating diagnostic questions.
3. User asks "根据试卷分析重点".
   - Expected: route to exam analysis; no unsupported claims.
4. User asks "今晚怎么不挂".
   - Expected: generate a time-boxed plan ending with first action.
5. User asks "按往年题出题".
   - Expected: generate variants with source basis.
6. User answers partially.
   - Expected: grade partial, list omissions, log mistake.
7. User asks "今天复习什么".
   - Expected: due items before new content.

Each eval should check:

- selected intent
- tool called
- source policy respected
- next action exists
- no fake tool result

## Observability

Every agent run should eventually log:

```yaml
run_id: string
timestamp: string
course_id: string
user_message: string
detected_intent: string
state_before: string
tools_called:
  - name: string
    status: success | failed
state_after: string
artifacts_written:
  - string
warnings:
  - string
```

This can first be printed in debug mode, then stored in:

```text
COURSE/review/agent-runs.yaml
```

Do not log full private notes unnecessarily. Prefer paths, ids, and summaries.

## Error Handling

The agent should have standard fallbacks.

| Problem | Response |
| --- | --- |
| No course selected | ask user to choose course or run inventory |
| No materials | ask for PPT, past exam, teacher focus, or notes |
| No past exams | offer diagnostic questions and plan from slides |
| Bad YAML | identify file and suggest repair; do not continue silently |
| No generated questions | run question generation or due review first |
| Low confidence analysis | show weak evidence and ask for better material |
| Tool unavailable | say the tool is not implemented and name the next dev step |

## Multi-Agent Upgrade Criteria

Do not split agents until at least three conditions are true:

- The single orchestrator has completed the MVP loop on at least 3 courses.
- Tool contracts are stable and have JSON outputs.
- Evaluation shows repeated failures caused by overloaded responsibilities.
- There is a clear need for specialized prompts, not just code organization.

When splitting is justified, use this structure:

```text
StudyReviewOrchestrator
  -> ExamAnalystAgent
  -> QuestionWriterAgent
  -> PlannerAgent
  -> TutorAgent
```

Even then, only `StudyReviewOrchestrator` should talk to the frontend. Sub-agents should be internal workers.

## Implementation Milestones

### Milestone A: CLI Agent Harness

Build:

- `scripts/agent_run.py`
- course state snapshot
- intent classifier
- tool dispatcher
- structured response printer

Acceptance:

- Can route `今晚怎么不挂` to `plan_review.py`.
- Can route `按往年题出题` to `generate_questions.py`.
- Does not claim missing tools ran.

### Milestone B: Review Session Harness

Build:

- `scripts/review_session.py`
- one-question display
- answer capture
- grading handoff
- mistake logging handoff

Acceptance:

- User can answer 5 generated questions.
- Partial/wrong answers become due review cards.

### Milestone C: API Agent Endpoint

Build:

- `POST /agent/run`
- `GET /courses/{course}/state`
- typed request/response models

Acceptance:

- Frontend can call one endpoint for emergency planning.
- Direct endpoints still exist for predictable UI actions.

### Milestone D: Agent Evals

Build:

- fixture course with sample files
- eval cases for the 7 minimum scenarios
- regression check for source policy

Acceptance:

- New agent changes cannot break MVP routing silently.

## Current Recommendation

The next implementation step should not be a framework migration.

Do this first:

```text
analyze_exam.py
generate_questions.py
plan_review.py
review_session.py
review_log.py --json
due_today.py --json
```

Then build:

```text
agent_run.py
```

Only after those run locally should the project add FastAPI and React.
