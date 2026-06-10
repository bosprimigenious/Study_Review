# Past Exam Analysis

This module turns uploaded exams, sample papers, homework answers, and course materials into exam-focused priorities and practice questions.

It should not promise leaked questions or exact predictions. It should identify patterns from user-provided materials, connect them to local review sources, and generate safe variants for practice.

## Core Flow

```text
upload exams / past papers
  -> detect question types and topics
  -> match topics to course materials
  -> rank high-frequency priorities
  -> generate variant questions
  -> build a review plan
```

## Inputs

Use workspace-local files only unless the user explicitly allows external sources.

High-value inputs:

- past exams
- sample papers
- homework answers
- teacher focus documents
- slides and review PDFs
- notes

Priority order for exam analysis:

```text
past exams -> sample papers -> homework answers -> teacher focus -> slides -> notes
```

## Output: Exam Analysis

An exam analysis should answer:

- What topics appear repeatedly?
- What question types are common?
- Which chapters should be reviewed first?
- Which items are good for scoring quickly?
- Which items need full reasoning or proof practice?
- What simulated questions should be practiced next?

Suggested format:

```markdown
# 试卷重点分析

## 高频章节
- ...

## 高频题型
- 题型：考点 / 常见问法 / 复习资料位置

## 先复习
1. ...

## 可以后置
- ...

## 变式练习
1. ...

## 复习计划
- 30 分钟：
- 90 分钟：
- 3 天：
```

## Data Model

### PastExamPattern

```yaml
id: pattern-cn-network-001
course_id: computer-network
source_file: 计算机网络/计算机网络样题(5).pdf
year: null
question_type: short_answer
topic: TCP congestion control
chapter: transport
difficulty: medium
original_question: ""
answer_shape: "作用 -> 触发条件 -> 过程 -> 结果"
scoring_points:
  - ""
reusable_template: "解释某协议机制时，按作用、触发条件、流程、结果组织答案。"
```

### ExamPriority

```yaml
course_id: computer-network
generated_at: "2026-06-10"
sources:
  - 计算机网络/计算机网络样题(5).pdf
priorities:
  - topic: TCP congestion control
    chapter: transport
    weight: 5
    evidence:
      - source_file: 计算机网络/计算机网络样题(5).pdf
        reason: "appears as a short-answer style topic"
    recommended_action: "closed-book protocol flow recall"
```

### GeneratedQuestion

```yaml
id: generated-cn-network-001
course_id: computer-network
based_on_pattern_id: pattern-cn-network-001
source_materials:
  - 计算机网络/6-Transport(3).pptx
question_type: short_answer
topic: TCP fast retransmit and recovery
difficulty: medium
similarity: same_type
prompt: ""
expected_answer: ""
scoring_points:
  - ""
time_limit_sec: 180
```

## Frontend Requirements

Add a dedicated exam analysis surface.

### Upload / Intake

The upload page must let users tag files:

- `课件`
- `往年题`
- `样题`
- `作业答案`
- `老师重点`
- `笔记`
- `教材/讲义`
- `其他`

The system may infer a tag from the filename, but the user must be able to correct it.

### Exam Analysis Page

Route:

```text
/courses/:courseId/exams
```

Main controls:

- select source files
- start analysis
- choose output: `重点分析`, `高频题型`, `变式题`, `复习计划`
- choose goal: `保底`, `冲高分`
- choose available time: `30 分钟`, `90 分钟`, `3 天`, `7 天`

Main sections:

- source coverage
- high-frequency topics
- question type distribution
- matched course materials
- generated practice set
- recommended review plan

Important actions:

- `分析试卷`
- `生成高频重点`
- `生成变式题`
- `加入今日计划`
- `开始练习`

## Backend Requirements

Suggested API:

```text
POST /courses/{courseId}/materials
GET  /courses/{courseId}/materials
POST /courses/{courseId}/exam-analysis
GET  /courses/{courseId}/exam-analysis/latest
POST /courses/{courseId}/exam-analysis/{analysisId}/questions
POST /courses/{courseId}/exam-analysis/{analysisId}/plan
```

Backend modules:

```text
services/api/routes/materials.py
services/api/routes/exams.py
services/api/core/exam_analyzer.py
services/api/core/material_matcher.py
services/api/core/question_generator.py
services/api/core/planner.py
```

Storage:

```text
course/review/
├── exam-analysis.yaml
├── past-exam-patterns.yaml
├── generated-questions.yaml
└── plan.md
```

## Agent Behavior

When the user asks:

- "根据试卷分析重点"
- "按往年题出题"
- "看看这套卷子该复习什么"
- "根据复习资料规划"

The agent should:

1. Identify exam-like files and study materials.
2. Ask for the course only if it is unclear.
3. Prefer existing past exam / sample paper files over slides.
4. Extract question types, topics, and answer shapes.
5. Match each topic back to local course materials.
6. Rank priorities with evidence.
7. Generate safe variant questions, not predicted original questions.
8. Build a short plan that starts with practice, not a long summary.

Every recommendation should distinguish:

- direct evidence from uploaded exams
- inference from repeated topics
- source material used to support the answer

## Safety And Quality Rules

- Do not claim a topic will definitely appear on the exam.
- Do not generate or request leaked exam content.
- Do not copy whole past-exam papers into the response.
- Mark generated items as `模拟题` or `变式题`.
- Keep source links or filenames for every priority item.
- Prefer scoring points and answer templates over long explanations.
