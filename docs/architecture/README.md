# Architecture Docs

最后更新：2026-06-27

## 入口

| 文档 | 角色 |
| --- | --- |
| [../../FULLSTACK_AGENT_ARCHITECTURE.md](../../FULLSTACK_AGENT_ARCHITECTURE.md) | 全栈 + agent 架构全景 |
| [../../PRODUCT_ARCHITECTURE.md](../../PRODUCT_ARCHITECTURE.md) | 产品结构和商业化架构 |
| [../../DESIGN.md](../../DESIGN.md) | 设计原则和交互方向 |
| [../../references/tech_stack.md](../../references/tech_stack.md) | 技术选型、PDF/OCR、前后端建议 |
| [../../references/orchestrator.md](../../references/orchestrator.md) | StudyReviewOrchestrator 状态机和工具契约 |
| [../../references/agent_development_plan.md](../../references/agent_development_plan.md) | agent 开发路线 |

## 系统边界

```text
React SPA
  -> FastAPI services/api
  -> Python CLI/tool layer
  -> course review/ files
  -> local course materials

Codex / StudyReviewOrchestrator
  -> reads SKILL.md
  -> loads references as needed
  -> calls scripts or API
```

## 架构原则

- CLI 是可信执行层，API 和前端先包装稳定 CLI 行为。
- LLM / Codex 做判断、解释、出题和评分，不直接写长期状态文件。
- 课程事实只来自本地 workspace、review 文件和用户输入。
- PDF/OCR 证据必须标明来源类型：native text、Vision OCR、rendered page。
- 架构升级必须服务核心复习闭环，不为抽象而抽象。
