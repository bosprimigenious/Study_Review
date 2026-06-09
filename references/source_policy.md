# Source Policy

This policy is mandatory for `study-review` sessions and for any future agent built from this skill.

## Default Rule

Only use materials under the current workspace as factual sources:

```text
/Users/bosprimigenious/Important_FIles/2025-2026下
```

The agent may inspect, summarize, quiz from, and cite files inside this workspace. It must not use outside material as evidence unless the user explicitly lifts the restriction.

## Disallowed Sources

Do not use these as factual sources by default:

- web search
- GitHub
- external websites
- external documents
- files outside the workspace
- installed package docs outside the workspace
- model memory or general background knowledge

The existence of a tool does not imply permission to use it. Web, GitHub, browser, or connector tools are off-limits for factual study answers unless the user clearly authorizes them.

## Answer Gate

Before answering a factual question, check whether the answer can be supported by workspace files.

If yes:

- answer from the local material
- mention the source file when the claim matters
- distinguish direct file-based claims from inference

If no:

```text
仓库内资料不足，无法判断。
```

Do not guess. Do not say "一般来说", "我知道", "常识上", or "网上通常" to fill missing facts.

## Scope Of Model Knowledge

Model knowledge may be used for:

- understanding Chinese or English wording
- reading code and file formats
- deciding how to inspect files
- structuring explanations
- helping generate questions from verified local material

Model knowledge must not be used for:

- unsupported factual answers
- adding course content not present in the workspace
- correcting or replacing local course material with outside knowledge
- citing external concepts as if they came from the local files

## Subagents And Delegated Tasks

If a task is delegated to another agent, subtask, or future workflow, include this exact constraint in the task:

```text
Only read and rely on files inside /Users/bosprimigenious/Important_FIles/2025-2026下. Do not use web search, GitHub, external websites, repository-external files, or model memory as factual sources. If the answer is not supported by workspace files, say the workspace materials are insufficient.
```

## User Override

The user may explicitly lift or narrow this policy.

Examples:

- "这次可以联网查"
- "可以参考 GitHub"
- "只看毛概PPT复习里的文件"
- "这题可以用常识解释"

The override applies only to the current request unless the user clearly says it should persist.

## Citation Style

For important conclusions, cite workspace files with paths such as:

```text
毛概PPT复习/第一章.pptx
概率论与数理统计/概率统计期末真题-4学分-仅供教学使用.pdf
```

When exact extraction is not possible, say that the answer is inferred from the inspected local file names or available local text, not from external sources.
