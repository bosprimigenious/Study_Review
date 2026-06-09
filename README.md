# Study Review Skill

`study-review` is a Codex skill for exam review from local course materials. It is designed to ask active-recall questions, grade answers, record mistakes, and schedule later review.

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

## Repository Layout

```text
study-review-skill/
├── SKILL.md
├── references/
├── scripts/
├── examples/
└── agents/openai.yaml
```

## Current Focus

The first version focuses on this loop:

```text
scan materials -> ask questions -> grade answers -> record mistakes -> schedule review
```

More advanced features such as Anki export, FSRS scheduling, full PPT/PDF extraction, or a React interface should come after this review loop works reliably.
