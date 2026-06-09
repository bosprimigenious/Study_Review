# Review Modes

Use these modes to decide how to run a study session.

## Diagnostic

Use when the user starts a subject or their level is unknown.

- Ask 5-8 questions.
- Mix concepts, applications, and one exam-style question.
- Classify the user as `薄弱`, `可做题`, or `冲刺`.
- Recommend the next mode.

## Active Recall

Use for ordinary review.

- Ask one question at a time.
- Wait for the user's answer.
- Judge the answer before explaining.
- End each answer with a follow-up question unless the user wants to stop.

Response shape:

```text
判定：正确 / 部分正确 / 错误
关键点：
遗漏：
更稳的答法：
追问题：
```

## Outline

Use when asked for outlines, chapter summaries, or exam points.

Output:

```markdown
# 科目/章节

## 必背
- ...

## 必会
- ...

## 易混
- A vs B: ...

## 常考题型
- 题型：解法模板 / 注意事项

## 5分钟自测
1. ...
```

## Problem Solving

Use for probability, computer organization, network calculations, automata construction, grammar problems, and proofs.

Process:

1. Ask the user to identify topic and method.
2. Let the user attempt.
3. Give hints before the full solution.
4. Extract a reusable template.
5. Generate one similar variant.

## Closed-Book Recitation

Use for memorization-heavy subjects.

Question types:

- keyword completion
- short-answer skeleton
- compare two concepts
- explain a statement
- chapter-to-topic matching

Grade by key terms, logical order, and exam scoring value.

## Sprint

Use near exams.

```text
第 1 轮：10 分钟摸底
第 2 轮：20 分钟补高频漏洞
第 3 轮：20 分钟题型/简答模板
第 4 轮：10 分钟回抽错题
```

Keep explanations short. Prefer scoring, templates, and repeated recall.
