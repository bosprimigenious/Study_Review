# Study Review Skill Design

## Goal

`study-review` is a Codex skill for exam preparation from local course folders. It should make Codex behave less like a summarizer and more like a study partner: first test recall, then explain gaps, then preserve weak points for later review.

The main design choice is **active recall first**. A student often feels productive when reading summaries, but exam performance improves more from being forced to retrieve, compare, calculate, and explain.

## Target Use Cases

- Start a review session from a folder of PPT/PDF files.
- Generate exam-oriented outlines from slides or notes.
- Convert chapters into atomic flashcards.
- Run one-question-at-a-time oral quizzes.
- Maintain a mistake log.
- Suggest what to review today.
- Switch behavior by subject: 毛概, 概率论, 计网, 计组, 理论计算机.

## Repository Layout

```text
study-review-skill/
├── SKILL.md
├── DESIGN.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── artifacts.md
│   ├── card_quality.md
│   ├── modes.md
│   └── subject_profiles.md
├── scripts/
│   ├── due_today.py
│   ├── inventory.py
│   └── review_log.py
└── examples/
    └── sample_session.md
```

## Trigger Strategy

The skill should trigger on broad review phrases as well as concrete commands:

- "开始复习"
- "复习计网"
- "抽查我"
- "生成题卡"
- "整理考点"
- "考前冲刺"
- "今天该复习什么"

The description in `SKILL.md` intentionally includes Chinese and English triggers because the user's workflow is bilingual but mostly Chinese.

## Workflow

1. **Inventory**
   Scan subject folders and identify high-value materials: review PDFs, sample exams, homework answers, slides, and notes.

2. **Mode Choice**
   Pick the review mode based on subject and user wording. For example, 毛概 uses closed-book recitation, while 概率论 uses problem solving.

3. **Recall**
   Ask one question at a time. Avoid long explanations before the user attempts an answer.

4. **Feedback**
   Grade as correct, partially correct, or wrong. Give a better exam answer only after the attempt.

5. **Capture**
   Save weak points into a review log when useful.

6. **Reschedule**
   Use simple intervals: today, D+1, D+3, D+7.

## Why Not Make It Fully Automated

The first version should not try to parse every slide perfectly or implement a full FSRS clone. The useful core is behavioral: ask good questions, diagnose mistakes, and keep the student moving.

Scripts are intentionally small:

- `inventory.py` helps inspect folders.
- `review_log.py` appends structured mistake entries.
- `due_today.py` finds review-log items due today.

This keeps the skill robust even when PPT/PDF extraction quality varies.

## Future Improvements

- Add PPT/PDF text extraction helpers.
- Add Anki export.
- Add FSRS scheduling.
- Add subject-specific question generators.
- Add a small local web dashboard for review status.
- Add tests for the scripts once the log format stabilizes.
