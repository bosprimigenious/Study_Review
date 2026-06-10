# Study Review Skill

`study-review` is a Codex skill for exam review from local course materials. It is designed to ask active-recall questions, grade answers, record mistakes, and schedule later review.

It is also being extended toward a full exam-prep workflow:

```text
upload review materials / past exams
  -> analyze question types and key topics
  -> match topics to local course materials
  -> generate variant practice questions
  -> build a concrete review plan
```

## Source Policy

By default, this skill only uses files under:

```text
/Users/bosprimigenious/Important_FIles/2025-2026下
```

It does not use web search, GitHub, external websites, repository-external files, or model memory as factual evidence unless the user explicitly allows it.

If a factual answer cannot be supported by local workspace files, the expected answer is:

```text
仓库内资料不足，无法判断。
```

See `references/source_policy.md` for the full policy.

## Product MVP

See `references/product_mvp.md` for the product-facing feature map. It marks first-version features, paid-entry candidates, later features, and risky features such as long-form note generation.

## How To Use

Example prompts:

```text
开始复习计算机网络，先摸底
```

```text
毛概抽背我，先来 5 题
```

```text
今天该复习什么
```

```text
根据这份试卷和复习资料分析重点，并出 10 道变式题
```

## Repository Layout

```text
study-review-skill/
├── SKILL.md
├── references/
├── scripts/
├── examples/
└── agents/openai.yaml
```

## Documentation Map

- `SKILL.md`: distilled runtime instructions for Codex as the study-review orchestrator.
- `DESIGN.md`: high-level design principles.
- `PLAN.md`: implementation roadmap and phase order.
- `FULLSTACK_AGENT_ARCHITECTURE.md`: React + TypeScript + Python architecture.
- `RESEARCH_REPORT.md`: background research and external comparisons.
- `references/orchestrator.md`: single-agent orchestration, state machine, intent routing, and tool contracts.
- `references/student_needs_research.md`: student demand research for exam-week workflows.
- `references/product_mvp.md`: MVP scope, paid-entry candidates, and note-generation strategy.
- `references/past_exam_analysis.md`: past-exam analysis workflow and data model.
- `references/question_patterns.md`: reusable question templates.
- `references/data_formats.md`: stable review data contracts and examples.
- `references/source_policy.md`: mandatory local-source policy.
- `references/modes.md`: detailed review modes.
- `references/subject_profiles.md`: subject-specific strategies.
- `references/card_quality.md`: flashcard and question quality rules.
- `references/artifacts.md`: review artifact formats.

## Current Focus

The first version focuses on this loop:

```text
scan materials -> ask questions -> grade answers -> record mistakes -> schedule review
```

The next product-facing loop is:

```text
upload exams/materials -> find priorities -> generate variants -> plan review -> drill weak points
```

More advanced features such as Anki export, FSRS scheduling, full PPT/PDF extraction, or a polished React interface should come after these review and exam-analysis loops work reliably.

## First CLI Step

Initialize a course review workspace:

```bash
python scripts/init_course_review.py "../计算机网络"
```
