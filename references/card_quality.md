# Card Quality Rules

Cards should be atomic, checkable, and exam-oriented.

## Good Cards

- Ask one thing.
- Have a clear answer.
- Include formula conditions.
- Target scoring points.
- Include tags for subject, chapter, and topic.

## Bad Cards

- "总结第三章"
- "解释概率论"
- "TCP 所有内容是什么"
- Cards whose answer requires a full page.

## Basic Format

```markdown
Q: 条件概率公式是什么？适用条件是什么？
A: P(A|B)=P(AB)/P(B)，要求 P(B)>0。
Tags: 概率论/第一章/条件概率
Difficulty: basic
```

## Contrast Card

```markdown
Q: TCP 拥塞控制和流量控制的区别是什么？
A: 拥塞控制面向网络整体负载，流量控制面向接收端处理能力；前者常用拥塞窗口，后者常用接收窗口。
Tags: 计算机网络/传输层/TCP
Difficulty: medium
```

## Cloze Card

```markdown
Q: TCP 三次握手依次为：{{SYN}}、{{SYN+ACK}}、{{ACK}}。
A: SYN；SYN+ACK；ACK
Tags: 计算机网络/传输层/TCP
Difficulty: basic
```

## Final Check

Before delivering cards, verify:

- every question is answerable
- formulas include conditions
- definitions are precise
- long topics are split
- likely wrong-answer traps are represented
