# Product MVP

This document records the product-facing shape of `study-review`: what the user sees, what the system should do first, which features are paid candidates, and which features should be delayed because they are easy to implement poorly.

## Product Thesis

The product value is not "AI summarizes PPTs".

The product value is:

```text
用户丢进一堆复习资料后，系统能告诉用户现在该干什么，并陪用户把这件事做完。
```

Core promise:

```text
根据用户上传的复习资料，自动查找重点、识别题型、规划复习顺序，并带用户完成复习。
```

Exam-week positioning:

```text
不是“学习系统”，而是“期末救火总控”。
```

Default user question:

```text
我快来不及了，怎么不挂科？
```

Default product response:

```text
先分析资料和往年题，给出今晚计划，马上开始 5 题摸底。
```

## MVP Marker Legend

- `[MVP]`: required for the first useful version.
- `[MVP-CANDIDATE]`: likely to enter the first useful version, but should be validated after data formats and CLI flow work.
- `[PAID]`: strong paid-entry candidate.
- `[LATER]`: useful after the core loop works.
- `[RISK]`: valuable but easy to make low quality; implement with guardrails.
- `[DO NOT START]`: do not build before data formats and review loop stabilize.

## Core Workflow

```text
创建课程
  -> 上传资料
  -> 系统分类 / 用户确认
  -> 资料索引
  -> 生成复习优先级
  -> 生成今日计划
  -> 开始刷题 / 抽背
  -> 错题进入复查
```

First-version loop:

```text
资料接收 -> 资料查找 -> 重点识别 -> 复习规划 -> 执行复习 -> 错题复查
```

## Feature Blocks

### 1. 资料接收 `[MVP]`

The user uploads or selects local materials:

- PPT / PDF course slides
- past exams
- sample papers
- homework answers
- teacher focus documents
- class notes
- textbook / lecture notes

The frontend should let users tag every file. AI may prefill a guessed tag, but the user must be able to edit it.

File type tags:

- `课件`
- `往年题`
- `样题`
- `作业答案`
- `老师重点`
- `课堂笔记`
- `教材/讲义`
- `其他`

### 2. 资料查找 `[MVP]`

The system should not only do plain full-text search. It should search by review goal:

- Find which slides mention a knowledge point.
- Find repeated question types in past exams.
- Find which chapters appear in homework answers or sample papers.
- Find which chapters are covered by teacher focus documents.
- Find which course material explains a mistake.
- Find what should be reviewed tonight for a pass-oriented plan.

Default priority:

```text
往年题 > 样题 > 作业答案 > 老师重点 > PPT > 普通笔记
```

Example:

```text
User: 我今晚复习计网，先看什么？

System:
先看计算题：子网划分、CRC、滑动窗口。
再背简答：TCP 拥塞控制、DNS 解析、HTTP 流程。
最后扫 PPT 第 3、5、6 章。
```

### 3. 重点识别 `[MVP]`

Extract from materials:

- high-frequency chapters
- high-frequency question types
- high-frequency concepts
- confusing pairs
- calculation templates
- short-answer templates
- teacher-emphasized content
- repeated past-exam patterns

Output should not be a long summary. Use exam-oriented sections:

```text
必背
必会
常考题型
易混点
今晚优先级
可以暂时放弃
```

### 4. 复习规划 `[MVP]`

Plan from constraints:

User inputs:

- exam date
- available time per day
- goal: `保底` or `高分`
- current confidence
- whether past exams exist

Plan outputs:

- 30-minute plan
- 90-minute plan
- 3-day plan
- 7-day plan

Planning rules:

- If exam is near, prioritize past exams and sample papers.
- If goal is pass, prioritize high-frequency question types and basic concepts.
- If goal is high score, add integrated questions, proofs, and edge cases.
- If the user has weak points, prioritize mistakes and weak chapters.
- If materials are missing, prompt the user to upload teacher focus documents or past exams.

### 5. 执行复习 `[MVP]`

Planning must lead directly into action:

- active recall
- practice questions
- timed answers
- mistake logging
- next-day review
- follow-up questions on weak points

The agent should say things like:

```text
现在开始第 1 轮：5 道诊断题。
```

Do not stop at a plan when the user is ready to practice.

## Most Important Buttons

The first frontend should emphasize action buttons over a generic chat box:

- `上传资料` `[MVP]`
- `分析往年题` `[MVP] [PAID]`
- `生成今晚计划` `[MVP] [PAID]`
- `开始 5 题摸底` `[MVP]`
- `继续复查错题` `[MVP]`
- `查找知识点` `[MVP]`
- `生成今晚保底笔记` `[RISK] [PAID]`

Emergency-mode buttons:

- `今晚怎么不挂` `[MVP] [PAID]`
- `只剩 90 分钟` `[MVP]`
- `最后 15 分钟看什么` `[MVP-CANDIDATE]`
- `哪些先放弃` `[MVP-CANDIDATE]`

The most valuable paid entry is likely:

```text
分析往年题
```

Reason: it directly answers the exam-week question "what will be tested and what should I practice first?" without promising leaked or exact questions.

## MVP Feature Checklist

First version:

- course management `[MVP]`
- material upload `[MVP]`
- file type tagging `[MVP]`
- material list `[MVP]`
- search by knowledge point `[MVP]`
- past-exam question type analysis `[MVP] [PAID]`
- today's review plan `[MVP]`
- one-question-at-a-time review `[MVP]`
- mistake logging `[MVP]`
- due review `[MVP]`
- emergency pass plan `[MVP]`
- first-task handoff after planning `[MVP]`

Later:

- paid unlocks `[LATER]`
- material sharing `[LATER]`
- Anki export `[LATER]`
- precise PDF/PPT extraction `[LATER]`; local scanned-PDF OCR workflow is documented in `references/pdf_ocr_workflow.md`
- school/course question banks `[LATER]`
- mobile mini app `[LATER]`

## Notes Output Strategy

Generating notes is valuable, but it is harder than search, planning, and drilling.

Why:

```text
笔记不是摘要。
```

Students need exam-ready notes:

- what the chapter tests
- what must be memorized
- what becomes calculation questions
- how to apply templates
- how to distinguish confusing concepts
- what the student personally missed
- what to read in the final 30 minutes

### Supported Note Types

Implement in this order:

1. `今晚保底笔记` `[MVP-CANDIDATE] [PAID]`
2. `往年题题型笔记` `[PAID]`
3. `错题笔记` `[MVP-CANDIDATE]`
4. `章节笔记` `[LATER] [RISK]`
5. `完整课程笔记` `[DO NOT START]`

### Exam-Ready Note Template

```markdown
# 计算机网络 第 5 章 网络层

## 先背这个
- ...

## 会这样考
- 题型：
- 问法：
- 答题模板：

## 易混
- A vs B：

## 计算题模板
1. 先判断：
2. 再套公式：
3. 最后检查：

## 往年题关联
- 2023 A 卷第 3 题：...
- 2024 样题第 5 题：...

## 5 分钟自测
1. ...
```

### Notes Generation Pipeline

Do not ask the model to read all materials and directly write a long note. Use a staged pipeline:

```text
资料索引
  -> 章节 / 题型切片
  -> 抽取候选考点
  -> 按往年题 / 样题 / 作业答案加权
  -> 生成笔记大纲
  -> 生成固定格式笔记
  -> 附来源引用
  -> 用户确认 / 编辑
```

### Notes Frontend

Route:

```text
/courses/:courseId/notes
```

Controls:

- course selector
- note goal: `保底`, `冲刺`, `错题`, `章节`, `往年题`
- source scope: `全部`, `只看往年题`, `只看老师重点`, `选择文件`
- generate button

Layout:

```text
Left: note body
Right: source evidence / related questions / add to active recall
```

Each note block should support:

- `加入题卡`
- `标记重点`
- `我不会`
- `生成相似题`

### Paid Notes

Do not sell generic summaries. Sell concrete exam outcomes:

- `生成今晚保底笔记`
- `生成往年题高频笔记`
- `生成错题复盘笔记`
- `生成可打印冲刺清单`
- `导出 PDF / Word`

Free version:

- chapter mini-outline
- first 3 key points
- small number of self-test questions

Paid version:

- full pass-oriented note
- past-exam links
- mistake review note
- export
- continue into active recall

## Payment Model

Recommended first monetization:

```text
Freemium + exam-season packages
```

Do not start with a heavy monthly subscription. Exam review demand is seasonal.

Better candidates:

- single-course sprint pack
- finals all-course pack
- paid past-exam analysis
- paid high-frequency notes
- paid export

Suggested unlock path:

```text
upload materials for free
  -> show material inventory for free
  -> give 5 diagnostic questions for free
  -> show partial weakness report
  -> paid unlock for full plan / past-exam analysis / high-frequency variants
```

## Product Guardrails

- Do not promise exact exam prediction.
- Do not request or generate leaked exam content.
- Mark generated questions as `模拟题` or `变式题`.
- Every recommendation should cite local files or clearly state it is an inference.
- Avoid long generic notes.
- Prefer "what to do next" over "what this chapter says".
