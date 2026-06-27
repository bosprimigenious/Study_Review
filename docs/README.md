# Study Review Documentation

最后更新：2026-06-27

这个目录是 `study-review-skill` 的人类维护文档入口。`SKILL.md` 仍然是 Codex 运行时入口，`references/` 仍然保存运行时可按需加载的规则；`docs/` 负责项目规划、架构、开发、运维、产品和文档治理。

## 快速入口

| 你要做什么 | 先读 |
| --- | --- |
| 了解下一步怎么迭代 | [UPDATE_AND_ITERATION_PLAN.md](UPDATE_AND_ITERATION_PLAN.md) |
| 判断文档放哪里、怎么维护 | [DOCUMENTATION_SYSTEM.md](DOCUMENTATION_SYSTEM.md) |
| 看产品定位、商业化和用户路径 | [product/README.md](product/README.md) |
| 看前后端和 agent 架构 | [architecture/README.md](architecture/README.md) |
| 开发脚本、API、前端或测试 | [development/README.md](development/README.md) |
| 运行、发布、排障、真实课程验证 | [operations/README.md](operations/README.md) |
| 查运行时规则和数据契约 | [reference/README.md](reference/README.md) |

## 文档分层

```text
SKILL.md
  Codex 运行时最小契约。短、稳定、只放调度规则。

references/
  Codex 需要按任务加载的领域规则、数据格式、题型模板和 source policy。

docs/
  人类维护者使用的路线图、架构索引、开发流程、运维流程和文档制度。

tests/*_results.md
  测试或验收结果。只记录事实，不承担路线图职责。

examples/
  稳定样例数据。用于说明格式，不写产品规划。
```

## 当前主线

当前项目已经具备 CLI、agent、FastAPI 骨架和 React 前端雏形。下一阶段应收束到：

1. 真实课程端到端验证。
2. 前端从“能打开”变成“能无 CLI 完成复习闭环”。
3. OCR / PDF 摄取从辅助脚本变成清晰可调用流程。
4. 文档和测试跟随每个功能一起更新。

详细版本计划见 [UPDATE_AND_ITERATION_PLAN.md](UPDATE_AND_ITERATION_PLAN.md)。
