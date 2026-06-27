# Reference Docs

最后更新：2026-06-27

`references/` 是 Codex 运行时按需加载的知识库。这个索引给人类维护者看，帮助判断应该改哪一篇。

| 文件 | 何时修改 |
| --- | --- |
| [../../references/source_policy.md](../../references/source_policy.md) | 本地资料来源规则变化时 |
| [../../references/orchestrator.md](../../references/orchestrator.md) | agent 状态机、工具路由、失败处理变化时 |
| [../../references/data_formats.md](../../references/data_formats.md) | YAML / Markdown 状态文件字段变化时 |
| [../../references/past_exam_analysis.md](../../references/past_exam_analysis.md) | 往年题分析流程、证据模型变化时 |
| [../../references/pdf_ocr_workflow.md](../../references/pdf_ocr_workflow.md) | PDF/OCR 摄取流程变化时 |
| [../../references/question_patterns.md](../../references/question_patterns.md) | 题型模板或出题规则变化时 |
| [../../references/card_quality.md](../../references/card_quality.md) | 卡片质量标准变化时 |
| [../../references/modes.md](../../references/modes.md) | 复习模式和回复结构变化时 |
| [../../references/subject_profiles.md](../../references/subject_profiles.md) | 课程策略变化时 |
| [../../references/artifacts.md](../../references/artifacts.md) | 错题、总结、复习记录格式变化时 |
| [../../references/tech_stack.md](../../references/tech_stack.md) | 技术栈建议变化时 |
| [../../references/product_mvp.md](../../references/product_mvp.md) | MVP 边界变化时 |
| [../../references/student_needs_research.md](../../references/student_needs_research.md) | 用户需求研究更新时 |

## 修改原则

- `references/` 写给 Codex 运行时，保持可执行、可检索、少叙事。
- 长期计划放 `docs/UPDATE_AND_ITERATION_PLAN.md`。
- 产品背景放 `docs/product/` 或根部产品文档。
- 数据字段变化必须同时更新 examples 和测试。
