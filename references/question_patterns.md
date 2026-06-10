# Question Patterns

This file defines reusable question patterns for exam review. The goal is to make Codex ask useful questions instead of drifting into summaries.

## Pattern Rules

Good review questions should:

- test one main point at a time
- be answerable from local course materials
- match likely exam scoring
- include conditions for formulas
- force retrieval before explanation
- support follow-up when the answer is weak

Avoid:

- "讲讲这一章"
- "总结全部 PPT"
- questions with no checkable answer
- variants that look like leaked exam predictions

## Diagnostic Patterns

Use 5-8 questions to classify the user as `薄弱`, `可做题`, or `冲刺`.

Templates:

```text
基础概念：请用一句话定义 {concept}，并说出它解决什么问题。
易混判断：{A} 和 {B} 的核心区别是什么？
应用识别：看到题目关键词 {clue}，你会想到哪个知识点/公式/协议？
步骤回忆：完成 {task} 的第一步、第二步、第三步分别是什么？
考试表达：如果这题是简答题，你会写哪 3 个得分点？
信心检查：这题你感觉是会、半会、还是蒙的？
```

## Active Recall Patterns

Templates:

```text
闭卷回忆：不看资料，说出 {concept} 的定义和适用条件。
关键点列举：{topic} 至少要答出哪 {n} 个得分点？
因果链：为什么 {mechanism} 会导致 {result}？
流程题：从 {start} 到 {end}，中间发生哪些步骤？
反问检查：如果少了 {condition}，结论还成立吗？为什么？
```

## Concept Contrast Patterns

Templates:

```text
比较 {A} 和 {B}：控制对象、使用场景、常见考法分别是什么？
判断题："{claim}" 对不对？错在哪里？
表格回忆：按定义、作用、条件、例子比较 {A} / {B}。
易错边界：什么时候容易把 {A} 误认为 {B}？
```

## Formula And Condition Patterns

Useful for probability, statistics, and computer organization.

Templates:

```text
公式回忆：{formula_name} 的公式是什么？每个符号代表什么？
条件检查：使用 {formula_name} 前必须满足哪些条件？
题型识别：看到 {problem_clue}，为什么要用 {formula_or_method}？
错误诊断：这一步用了 {formula_name}，你觉得是否合法？为什么？
变式：把参数从 {old_value} 换成 {new_value}，解题步骤哪里会变？
```

## Protocol Flow Patterns

Useful for computer networks.

Templates:

```text
流程回忆：从 {start_event} 到 {end_event}，按顺序说出协议交互。
层次定位：这个问题发生在 OSI/TCP-IP 哪一层？为什么？
字段作用：{field_or_header} 的作用是什么？如果没有它会怎样？
机制解释：{mechanism} 的触发条件、过程、结果是什么？
对比：{protocol_A} 和 {protocol_B} 分别解决什么问题？
```

## Calculation Patterns

Templates:

```text
先判题型：这道题属于哪类计算？第一步应该找什么量？
列步骤：不用算最终答案，先写出解题模板。
单位检查：这个结果的单位/量纲对吗？
边界检查：答案是否落在合理范围？为什么？
同型变式：保持题型不变，换一组参数再做一题。
```

## Construction And Proof Patterns

Useful for theoretical computer science.

Templates:

```text
构造题：给语言 {language}，构造 DFA/NFA/CFG 的关键状态或产生式。
证明思路：先说证明策略，再写形式化细节。
反例：如果命题 "{claim}" 是假的，给一个反例。
泵引理：选择字符串、分解条件、矛盾点分别是什么？
等价转换：把 {object_A} 转换成 {object_B} 的步骤是什么？
```

## Closed-Book Recitation Patterns

Useful for memorization-heavy subjects.

Templates:

```text
关键词补全：{statement} 中缺的关键词是什么？
简答骨架：回答 "{question}" 至少写哪三层？
章节定位：{keyword} 属于哪一章？解决什么问题？
意义题：为什么说 {claim}？按背景、内容、意义回答。
比较题：{concept_A} 和 {concept_B} 在历史背景和理论内容上有什么区别？
```

## Past Exam Variant Patterns

Use only safe variants. Do not imply exact exam prediction.

Templates:

```text
同题型变式：保留 {question_type} 和考点 {topic}，更换场景或参数。
同考点变式：保留考点 {topic}，换成另一种问法。
高频混合卷：从最高频 {n} 个 topic 各出 1-2 题。
保底卷：只覆盖最基础、最容易拿分的题型。
错题变式：围绕用户错因 {mistake_type} 生成相似题。
```

Every generated variant should include:

```text
题目：
依据：
标准答案：
评分点：
建议限时：
```

## Mistake Follow-Up Patterns

When the user is wrong or partially correct:

```text
错因定位：你这题主要错在概念、条件、步骤、表达，还是计算？
最小补题：我只追问一个点：{missing_point} 是什么？
同类再练：换一个同类型题，看看是不是稳定会了。
反向解释：你能解释为什么错误答案不成立吗？
复查卡片：这题下次复查时应该问成什么问题？
```

## Subject Quick Templates

### 毛概

- 简述 {concept} 的主要内容。
- 为什么说 {claim}？
- {concept_A} 和 {concept_B} 有什么区别？
- 给关键词 {keyword}，说出它属于哪一章、解决什么问题。
- 把答案压成考试能得分的 3 点。

### 概率论与数理统计

- 这题先判断随机变量类型还是分布类型？
- 这个公式的适用条件是什么？
- 支持域/积分区域怎么确定？
- 拒绝域怎么写？显著性水平在哪里用？
- 换一组参数，步骤是否一样？

### 计算机网络

- 从浏览器输入 URL 到页面出现，发生了什么？
- ARP 和 DNS 分别解决什么映射？
- 拥塞控制和流量控制区别是什么？
- 这个字段在哪一层？解决什么问题？
- 按往年题风格出一道同类型协议流程题。

### 计算机组成原理

- 这题的位宽和符号位是什么？
- 溢出怎么判断？
- cache 地址如何拆成 tag/index/offset？
- 指令格式中每个字段的作用是什么？
- 先写模板，再代数计算。

### 理论计算机基础

- 给出这个语言的 DFA/NFA/正则表达式。
- 判断该文法类型并说明理由。
- 这个语言为什么是/不是正则语言？
- NFA 转 DFA 的关键步骤是什么？
- 证明前先说证明策略。
