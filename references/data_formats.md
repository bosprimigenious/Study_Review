# Data Formats

This file defines the stable data contracts for scripts, backend APIs, frontend views, and the StudyReviewOrchestrator.

Use Markdown for human-readable state and YAML for script-readable state.

## Course Review Directory

Each course should have:

```text
COURSE/
└── review/
    ├── files.yaml
    ├── progress.md
    ├── mistake-log.md
    ├── cards.yaml
    ├── exam-analysis.yaml
    ├── past-exam-patterns.yaml
    ├── generated-questions.yaml
    └── plan.md
```

Rules:

- Scripts must not overwrite existing review files unless explicitly requested.
- Every generated question must have a source or analysis basis.
- Every course fact must be traceable to local files.
- Dates use ISO format: `YYYY-MM-DD`.

## files.yaml

Purpose: material inventory and upload metadata.

```yaml
course:
  id: computer-network
  name: 计算机网络
  created_at: "2026-06-10"

files:
  - id: file-net-001
    path: 计算机网络/6-Transport(3).pptx
    name: 6-Transport(3).pptx
    material_type: slides
    ext: .pptx
    status: ready
    tags:
      - transport
    notes: ""
```

Allowed `material_type`:

```text
slides
past_exam
mock_exam
homework_answer
teacher_focus
notes
textbook
other
```

Allowed `status`:

```text
registered
indexing
ready
failed
```

## progress.md

Purpose: human-readable course state.

```markdown
# 计算机网络复习进度

## 当前状态
- 阶段：诊断
- 最近复习：2026-06-10
- 当前目标：保底
- 当前最弱：TCP 拥塞控制、子网划分
- 下一步：完成 5 题诊断后生成 90 分钟计划

## 资料状态
- 课件：7
- 往年题：1
- 样题：1
- 作业答案：0

## 章节进度
- [ ] Introduction
- [ ] Physical
- [ ] Data Link
- [ ] Network
- [ ] Transport
- [ ] Application

## 最近错因
- 暂无
```

## cards.yaml

Purpose: script-readable review cards and due items.

```yaml
cards:
  - id: card-net-tcp-001
    course_id: computer-network
    subject: 计算机网络
    chapter: Transport
    topic: TCP congestion control
    card_type: contrast
    prompt: TCP 拥塞控制和流量控制的区别是什么？
    answer: 拥塞控制面向网络整体负载；流量控制面向接收端处理能力。
    scoring_points:
      - 控制对象不同
      - 使用窗口不同
      - 触发原因不同
    source:
      file: 计算机网络/6-Transport(3).pptx
      evidence: local course material
    difficulty: medium
    tags:
      - 计算机网络
      - TCP
      - 易混
    schedule:
      rating: 困难
      last_reviewed: "2026-06-10"
      due: "2026-06-11"
```

Allowed `card_type`:

```text
definition
contrast
formula
flow
calculation
construction
proof
short_answer
variant
mistake_review
```

Allowed `difficulty`:

```text
basic
medium
hard
```

Allowed `rating`:

```text
忘了
困难
还行
很熟
```

## mistake-log.md

Purpose: human-readable mistakes.

```markdown
## 2026-06-10 - 计算机网络

### 知识点
- TCP 拥塞控制 vs 流量控制

### 原题/问题
拥塞控制和流量控制区别是什么？

### 我的错误
只说了“都是控制速度”，没有说清楚控制对象。

### 正确理解
拥塞控制防止网络过载，流量控制防止接收方被发送方压垮。

### 错因标签
- 概念混淆
- 表达不完整

### 下次复查
- [ ] 2026-06-11
- [ ] 2026-06-13
- [ ] 2026-06-17
```

## exam-analysis.yaml

Purpose: latest exam or past-paper analysis.

```yaml
analysis:
  id: exam-analysis-net-001
  course_id: computer-network
  generated_at: "2026-06-10"
  goal: pass
  source_files:
    - 计算机网络/计算机网络样题(5).pdf
  summary: 传输层和网络层题型优先级较高。
  priorities:
    - topic: TCP congestion control
      chapter: Transport
      weight: 5
      question_types:
        - short_answer
      evidence:
        - source_file: 计算机网络/计算机网络样题(5).pdf
          reason: appears in protocol explanation style
      recommended_action: closed-book protocol flow recall
  plan_refs:
    - plan.md
```

## past-exam-patterns.yaml

Purpose: reusable question patterns extracted from past papers.

```yaml
patterns:
  - id: pattern-net-001
    course_id: computer-network
    source_file: 计算机网络/计算机网络样题(5).pdf
    year: null
    question_type: short_answer
    topic: TCP congestion control
    chapter: Transport
    difficulty: medium
    answer_shape: 作用 -> 触发条件 -> 过程 -> 结果
    scoring_points:
      - 说明机制目的
      - 说明触发条件
      - 说明过程
      - 说明结果
    reusable_template: 解释协议机制时按作用、触发条件、过程、结果组织答案。
```

## generated-questions.yaml

Purpose: practice questions created from local materials or past-exam patterns.

```yaml
questions:
  - id: gen-net-001
    course_id: computer-network
    based_on_pattern_id: pattern-net-001
    source_materials:
      - 计算机网络/6-Transport(3).pptx
    question_type: short_answer
    topic: TCP fast retransmit and recovery
    difficulty: medium
    similarity: same_type
    label: 变式题
    prompt: 请说明 TCP 快速重传和快速恢复的作用、触发条件和基本过程。
    expected_answer: ""
    scoring_points:
      - 说明作用
      - 说明重复 ACK 触发
      - 说明快速重传
      - 说明快速恢复
    time_limit_sec: 180
```

Allowed `similarity`:

```text
same_type
same_topic
mixed
mistake_variant
```

Allowed `label`:

```text
模拟题
变式题
错题变式
```

## plan.md

Purpose: human-readable review plan.

```markdown
# 计算机网络复习计划

## 目标
- 保底

## 依据
- 计算机网络样题(5).pdf
- 6-Transport(3).pptx

## 90 分钟计划
1. 15 分钟：回忆 TCP/UDP、拥塞控制、流量控制。
2. 25 分钟：做 5 道传输层变式题。
3. 20 分钟：复盘错题并写入 cards.yaml。
4. 20 分钟：网络层高频题型快速过一遍。
5. 10 分钟：回抽本轮错题。

## 现在开始
- 先做 5 题诊断。
```

## ID Rules

IDs should be stable and readable:

```text
file-{course}-{number}
card-{course}-{topic}-{number}
pattern-{course}-{number}
gen-{course}-{number}
```

Use lowercase ASCII for IDs when possible. Chinese display names belong in `name`, `subject`, or `topic`, not IDs.
