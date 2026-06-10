# Student Needs Research

This report translates exam-week student needs into product and agent requirements for `study-review`.

External research is used only for product design. Course-content answers must still follow `references/source_policy.md`.

## Research Caveat

Xiaohongshu content is difficult to cite reliably from search results because full posts are not always accessible or stable. Treat Xiaohongshu-style observations as qualitative signals, not a statistically valid dataset.

The consistent pattern across publicly visible exam-week posts, university study guides, and student-facing advice is:

```text
焦虑、来不及、资料很多、求重点、求不挂科、求速成、求有人带着做。
```

## Sources Consulted

- 中国大学生在线期末复习建议: emphasizes reviewing homework and PPT first, then teacher-marked scope, prioritizing major courses and high-GPA courses, and managing anxiety.
- Existing market products and learning systems: NotebookLM, Quizlet, Anki, FSRS, and AI-generated practice-test research.
- Internal project reports: `RESEARCH_REPORT.md`, `references/product_mvp.md`, `references/past_exam_analysis.md`.

## Demand Map

### 1. 救火规划

Student wording:

```text
我还有 2 天，怎么安排？
今晚怎么不挂？
五门课一起考，先复习哪门？
```

Required function:

- 30-minute plan
- 90-minute plan
- 3-day plan
- 7-day plan
- priority by exam date, credit/GPA value, weakness, and available materials

Agent behavior:

- do not start with a long summary
- produce a short plan
- immediately start the first task

### 2. 按资料找重点

Student materials are messy:

- PPT
- PDFs
- homework answers
- sample papers
- past exams
- teacher focus documents
- group-shared notes
- personal notes

Required function:

- identify high-value files
- classify files by type
- rank materials by exam usefulness
- answer "先看什么"
- answer "这个知识点在哪个资料里"

Priority:

```text
past exams -> sample papers -> homework answers -> teacher focus -> review PDFs -> slides -> notes
```

### 3. 往年题分析

Student wording:

```text
这几套卷子高频考什么？
能不能按这个风格出几道题？
哪些题型最容易拿分？
```

Required function:

- detect question types
- detect repeated topics
- map topics to local course materials
- generate safe variants
- produce scoring points
- build a review plan

Product implication:

```text
分析往年题
```

is the strongest paid-entry candidate.

### 4. 速成型笔记

Students do not need long notes during exam week. They need exam-ready notes:

- tonight's must-memorize items
- high-frequency question types
- confusing pairs
- calculation templates
- short-answer skeletons
- final 15-minute review list

Required function:

- `今晚保底笔记`
- `往年题题型笔记`
- `错题复盘笔记`

Do not build:

```text
完整课程笔记
```

until the review loop and data formats are stable.

### 5. 一题一答抽查

Student problem:

```text
看 PPT 时感觉会了，真答题时写不出来。
```

Required function:

- active recall first
- one question at a time
- grade after answer
- show missing scoring points
- ask a follow-up
- record mistakes

### 6. 错题复查

Student problem:

```text
今天错了，明天忘了。
```

Required function:

- mistake reason tags
- due dates
- same-type variants
- exam-eve recall

Use simple scheduling first:

```text
忘了 -> today + tomorrow
困难 -> D+1
还行 -> D+3
很熟 -> D+7
```

## Market Gap

NotebookLM is strong at source-based generation. Quizlet is strong at cards and learning modes. Anki is strong at memory scheduling.

The gap for this project:

```text
Chinese university finals
  + local PPT/PDF/past papers/homework answers
  + urgent planning
  + past-exam style variants
  + one-question-at-a-time review
```

## Recommended Product Statement

```text
期末复习总控 agent：
根据你的 PPT、往年题、作业答案和老师重点，
找出最该复习的内容，
生成今晚计划，
按往年题风格出变式题，
一题一题抽查你，
并把错题安排到考前复查。
```

## Feature Priority

### P0

- material upload / registration
- file type tagging
- material inventory
- past exam analysis
- tonight plan
- 5-question diagnostic
- generated variants
- mistake logging
- due review

### P1

- pass-oriented notes
- past-exam-type notes
- mistake review notes
- export to PDF / Word
- simple frontend

### P2

- full course notes
- school/course public question bank
- social sharing
- full Anki replacement
- heavy FSRS scheduling
- mobile mini app

## Implementation Implications

The next engineering work should not be another broad strategy document. It should create executable contracts:

1. `references/question_patterns.md`
2. `references/data_formats.md`
3. `examples/sample_files.yaml`
4. `examples/sample_exam_analysis.yaml`
5. `scripts/init_course_review.py`

Then validate on one real subject folder.
