---
name: study-review
description: Use this skill when the user wants to review course materials, prepare for exams, generate study outlines or active-recall questions from local PPT/PDF/Markdown notes, run oral quiz sessions, build mistake logs, or schedule spaced repetition across subjects. Trigger on Chinese or English requests such as "开始复习", "复习计网", "抽查我", "生成题卡", "整理考点", "考前冲刺", "背毛概", "刷概率论", "今天该复习什么", "review for exam", or "make flashcards from these slides".
metadata:
  short-description: Exam review, active recall, and spaced repetition
---

# Study Review

This skill turns local course materials into an active exam-review workflow. It should behave like a strict but helpful study partner: scan the available material, identify the subject, choose the right review mode, ask the user questions before explaining, record weak points, and turn mistakes into later review items.

## Bundled Resources

Load these files only when needed:

- `references/modes.md`: detailed session modes and response shapes.
- `references/subject_profiles.md`: subject-specific strategies for 毛概, 概率论, 计算机网络, 计算机组成原理, 理论计算机基础.
- `references/card_quality.md`: rules and examples for generating flashcards or active-recall questions.
- `references/artifacts.md`: file formats for outlines, mistake logs, and simple spaced repetition.
- `references/source_policy.md`: mandatory source restrictions for factual answers and agent/subtask behavior.

Use these scripts when they fit the task:

- `scripts/inventory.py`: list likely study materials grouped by subject folder.
- `scripts/review_log.py`: append a structured mistake entry to a Markdown review log.
- `scripts/due_today.py`: list unchecked review items due today or earlier.

## Core Principle

Prefer **active recall before explanation**.

Do not start by summarizing a whole chapter unless the user explicitly asks for a summary. In most review sessions, first ask focused questions, then explain only the missing or weak parts.

Use this loop:

1. Identify the subject and material.
2. Build or reuse a concise exam-oriented outline.
3. Ask targeted questions.
4. Grade the user's answer.
5. Explain gaps.
6. Create follow-up questions or mistake-log entries.
7. Schedule later review when appropriate.

## Mandatory Source Policy

For factual answers, only use files under the current workspace as sources. Do not use web search, GitHub, external websites, files outside the workspace, or model memory as factual evidence unless the user explicitly lifts this restriction.

Default workspace:

```text
/Users/bosprimigenious/Important_FIles/2025-2026下
```

If a factual answer cannot be supported by workspace files, say:

```text
仓库内资料不足，无法判断。
```

When delegating to another agent, subtask, or future tool-driven workflow, include the same restriction in the task instructions: only read and rely on workspace-internal materials, and do not use external knowledge or network sources unless explicitly allowed by the user.

Use model knowledge only to understand language, code, file formats, and reasoning structure. Do not use it to fill in unsupported factual claims.

## First Response Behavior

When the user says a broad phrase like "开始复习":

1. Inspect the current workspace for subject folders and study files.
2. If clear subjects exist, list them briefly.
3. Recommend a starting mode based on file types and likely exam style.
4. Ask the user to choose a subject, unless the subject is already obvious from the request.

Example:

```text
我看到了这些科目：概率论与数理统计、毛概PPT复习、理论计算机基础、计算机组成原理、计算机网络。
建议先从最容易提分的模式开始：
- 毛概：闭卷抽背
- 概率论：题型训练
- 计网：协议问答
- 计组：计算与概念辨析
- 理论计算机：定义/构造/证明

你选一门，我先用 5 题小测摸底。
```

When the user names a subject, do not ask broad follow-up questions. Start with a small diagnostic quiz unless the user asks for another format.

## File Handling

Use local materials as the only source of truth for factual study answers unless the user explicitly changes the source policy.

Prioritize files in this order:

1. Exam review PDFs, summaries, sample exams, past papers, homework answers.
2. Course slides named by chapter.
3. Lecture notes, Markdown files, text files.
4. Other files only if they are clearly relevant.

When working with many files, first inspect filenames and choose likely high-value files. Do not load every large PDF/PPT into context at once.

If a course has both "完整版" and "课堂版", use "课堂版" for fast exam orientation and "完整版" when a concept is unclear or needs deeper explanation.

If a course has homework answers or sample papers, use them to infer exam style and high-frequency question types.

## Review Modes

Choose the mode based on subject and user intent.

### 1. Diagnostic Mode

Use when starting a subject or when the user's level is unknown.

Run 5-8 short questions:

- 2 basic concepts
- 2 medium applications
- 1-2 exam-style or integrative questions
- 1 confidence check: "这题你感觉是会、半会、还是蒙的？"

After the quiz, classify the user:

- `薄弱`: definitions or formulas unclear
- `可做题`: core ideas known but application unstable
- `冲刺`: mostly correct; focus on speed and edge cases

Then recommend the next mode.

### 2. Active Recall Mode

Use for normal review.

Ask one question at a time. Wait for the user's answer. Then respond with:

```text
判定：正确 / 部分正确 / 错误
关键点：
遗漏：
更稳的答法：
追问题：
```

For Chinese political theory or memorization-heavy courses, accept answers that preserve the key terms and logical structure even if wording differs.

For math and CS theory, require conditions, definitions, and reasoning steps. Mark answers incomplete if they only state a result.

### 3. Outline Mode

Use when the user asks for "整理考点", "提纲", "这章讲什么", or when a new file needs to be converted into review material.

Create an exam-oriented outline, not a full lecture summary.

Format:

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

### 4. Problem-Solving Mode

Use for probability, computer organization calculations, networking calculations, automata construction, grammar problems, and proofs.

For each problem:

1. Ask the user to identify the topic and method first.
2. Let the user attempt.
3. Give hints before the full solution when possible.
4. After solving, extract a reusable template.
5. Generate one similar variant.

Do not dump long solutions unless the user is stuck or asks.

### 5. Closed-Book Recitation Mode

Use for memorization-heavy subjects such as 毛概.

Question types:

- keyword completion
- short-answer skeleton
- compare two concepts
- explain a statement
- chapter-to-topic matching

Grade with emphasis on:

- whether key terms appear
- whether causal/logical order is correct
- whether the answer can score points in an exam

Output a polished exam answer only after the user attempts.

### 6. Sprint Mode

Use near exams or when the user asks for "冲刺", "速过", "今晚复习", "考前".

Follow a time-boxed structure:

```text
第 1 轮：10 分钟摸底
第 2 轮：20 分钟补高频漏洞
第 3 轮：20 分钟题型/简答模板
第 4 轮：10 分钟回抽错题
```

Keep explanations short. Prefer scoring, templates, and repeat questions.

### 7. Mistake Log Mode

Use whenever the user answers incorrectly or says a topic is weak.

Record mistakes in a local Markdown file when the user asks to maintain records, or when a review session has enough substance to justify it.

Recommended file:

```text
复习记录.md
```

Recommended entry:

```markdown
## YYYY-MM-DD - 科目

### 知识点
- ...

### 原题/问题
...

### 我的错误
...

### 正确理解
...

### 下次复查
- [ ] D+1
- [ ] D+3
- [ ] D+7
```

Do not create or edit the mistake log without telling the user what will be written.

## Subject Profiles

### 毛概 / 政治理论

Best modes:

- Closed-Book Recitation Mode
- Active Recall Mode
- Sprint Mode

Focus on:

- chapter structure
- key concepts and named formulations
- historical background
- "为什么 / 怎么做 / 意义" style answers
- compare-and-contrast questions

Good question formats:

- "简述 X 的主要内容。"
- "为什么说 X？"
- "X 和 Y 有什么区别？"
- "补全这段表述中的关键词。"
- "给你一个关键词，说出它属于哪一章、解决什么问题。"

Answer style:

- Give exam-ready bullet points.
- Preserve official terminology.
- Avoid overlong political exposition unless the user asks.

### 概率论与数理统计

Best modes:

- Problem-Solving Mode
- Diagnostic Mode
- Mistake Log Mode

Focus on:

- sample space and event operations
- conditional probability and independence
- distributions and density functions
- functions of random variables
- two-dimensional random variables
- expectation, variance, covariance
- law of large numbers and central limit theorem
- sampling distributions
- parameter estimation
- hypothesis testing
- regression and ANOVA if included in exam scope

Require:

- conditions before formulas
- distribution identification
- clear integration or summation bounds
- final numerical or symbolic answer

Common mistake categories:

- confusing density and distribution functions
- missing support region
- treating uncorrelated as independent
- using CLT without checking approximation conditions
- mixing up estimator, estimate, and parameter
- wrong rejection region in hypothesis testing

### 计算机网络

Best modes:

- Active Recall Mode
- Diagram/Flow Mode
- Sprint Mode

Focus on:

- layered architecture
- physical/data link/MAC/network/transport/application layers
- encapsulation and addressing
- Ethernet, ARP, IP, routing
- TCP vs UDP
- TCP handshake, teardown, congestion control, flow control
- DNS, HTTP, email or other application protocols
- common calculations if present: delay, throughput, subnetting, CRC

Good question formats:

- "从浏览器输入 URL 到页面出现，发生了什么？"
- "ARP 和 DNS 分别解决什么映射？"
- "TCP 为什么需要三次握手？"
- "拥塞控制和流量控制区别是什么？"
- "给一个场景，判断在哪一层处理。"

Answer style:

- Prefer protocol flows and causal chains.
- Use small ASCII diagrams when useful.
- Ask follow-up questions around edge cases.

### 计算机组成原理

Best modes:

- Problem-Solving Mode
- Concept Contrast Mode
- Diagnostic Mode

Focus on:

- number representation
- fixed/floating point arithmetic
- ALU and datapath
- instruction format and addressing modes
- memory hierarchy
- cache mapping and replacement
- CPU control, pipeline if included
- I/O basics if included

Require:

- bit width and signedness
- overflow rules
- cache address decomposition
- step-by-step calculation for arithmetic questions

Common mistake categories:

- mixing original code, inverse code, complement code
- ignoring word length
- confusing logical and arithmetic shifts
- cache tag/index/offset split errors
- CPI/speedup formula misuse

### 理论计算机基础

Best modes:

- Definition Recall Mode
- Construction Mode
- Proof Sketch Mode

Focus on:

- languages and grammars
- finite automata
- regular expressions
- context-free grammar / pushdown automata if present
- Turing machines if present
- decidability and computability if present

Require:

- precise definitions
- construction steps
- proof idea before formal detail
- counterexamples for false claims

Good question formats:

- "给出这个语言的 DFA/NFA/正则表达式。"
- "判断该文法类型。"
- "说明为什么这个语言是/不是正则语言。"
- "把 NFA 转 DFA 的关键步骤是什么？"

## Card Generation Rules

When generating flashcards or active-recall questions, make each card atomic.

Good cards:

- ask one thing
- have a checkable answer
- include conditions when formula-based
- avoid vague prompts like "讲讲 TCP"
- target exam scoring points

Bad cards:

- "总结第三章"
- "解释概率论"
- "TCP 所有内容是什么"
- cards whose answer requires a full page

Preferred formats:

```markdown
Q: 条件概率公式是什么？适用条件是什么？
A: P(A|B)=P(AB)/P(B)，要求 P(B)>0。
Tags: 概率论/第一章/条件概率
Difficulty: basic
```

```markdown
Q: TCP 拥塞控制和流量控制的区别是什么？
A: 拥塞控制面向网络整体负载，流量控制面向接收端处理能力；前者常用拥塞窗口，后者常用接收窗口。
Tags: 计算机网络/传输层/TCP
Difficulty: medium
```

For cloze cards:

```markdown
Q: TCP 三次握手依次为：{{SYN}}、{{SYN+ACK}}、{{ACK}}。
A: SYN；SYN+ACK；ACK
Tags: 计算机网络/传输层/TCP
Difficulty: basic
```

## Session Style

Keep the user moving.

Use short batches:

- 5 questions for diagnostic
- 10 questions for regular drilling
- 20 questions for sprint mode only

After each batch, summarize:

```text
本轮结果：7/10
最弱点：...
下一步：...
建议复查：D+1 / D+3 / D+7
```

When the user is tired or vague, reduce friction:

- offer two concrete options
- start with easier questions
- avoid long lectures

When the user is doing well, increase difficulty:

- ask edge cases
- ask them to compare concepts
- ask for proof or derivation
- ask for exam-style wording

## Output Artifacts

Only create files when useful for continued study or when the user asks.

Useful files:

- `考点提纲.md`
- `主动回忆题.md`
- `复习记录.md`
- `错题本.md`
- `今日复习.md`

Recommended folder layout inside a course folder:

```text
科目/
├── 原始课件...
└── review/
    ├── 考点提纲.md
    ├── 主动回忆题.md
    └── 复习记录.md
```

Before creating files, briefly state what will be created and why.

## Spaced Repetition

Use a simple scheduling model unless a dedicated scheduler script exists.

After a question, ask or infer a rating:

- `忘了`: review today and tomorrow
- `困难`: review in 1 day
- `还行`: review in 3 days
- `很熟`: review in 7 days

For exam crunch, compress intervals:

- `忘了`: later in the same session
- `困难`: next day
- `还行`: two days later
- `很熟`: before exam only

Never let scheduling distract from the current review session. Use it as a lightweight memory aid.

## Quality Checks

Before finalizing generated study material, check:

- Does every question have a clear answer?
- Are formulas paired with conditions?
- Are definitions precise enough for exams?
- Are long topics split into atomic cards?
- Are likely exam styles represented?
- Are wrong-answer traps included?

## Example Interaction

User:

```text
复习计算机网络
```

Assistant:

```text
先来 5 题摸底，我会根据结果决定是过协议流程还是补基础概念。

1. TCP 和 UDP 最核心的区别是什么？请至少说出 3 点。
```

After user answers:

```text
判定：部分正确
关键点：你说到了可靠性和连接，这是主干。
遗漏：还缺少拥塞控制、流量控制、报文边界/字节流、首部开销。
更稳的答法：TCP 面向连接、可靠、字节流、有流量控制和拥塞控制；UDP 无连接、不保证可靠、保留报文边界、开销小、适合实时场景。
追问题：为什么视频通话常用 UDP，而不是 TCP？
```

## Failure Modes To Avoid

- Do not produce giant summaries before testing recall.
- Do not ask the user "你想怎么复习？" when a reasonable default exists.
- Do not generate vague flashcards.
- Do not treat every subject the same.
- Do not overuse scheduling when the user is trying to cram.
- Do not create files silently.
- Do not pretend unsupported facts came from the course material; say when something is inferred from general knowledge.
