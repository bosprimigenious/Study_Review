# Operations Docs

最后更新：2026-06-27

## 入口

| 文档 | 角色 |
| --- | --- |
| [../UPDATE_AND_ITERATION_PLAN.md](../UPDATE_AND_ITERATION_PLAN.md) | 当前版本验收重点 |
| [../../tests/e2e_results.md](../../tests/e2e_results.md) | CLI E2E 验收记录 |
| [../../tests/phase4_results.md](../../tests/phase4_results.md) | Phase 4 验证记录 |
| [../../scripts/ocr/README.md](../../scripts/ocr/README.md) | OCR 和 PDF 渲染运行说明 |

## 真实课程验收流程

对每门课程执行：

```bash
python scripts/init_course_review.py "../课程名"
python scripts/analyze_exam.py "../课程名" --force
python scripts/generate_questions.py "../课程名" --count 5 --force
python scripts/plan_review.py "../课程名" --minutes 90 --goal pass --force
python scripts/review_session.py "../课程名" --source generated --limit 1
python scripts/due_today.py ..
```

验收记录应包含：

- 课程名和日期。
- 输入资料概况。
- 成功命令和失败命令。
- 生成文件路径。
- 至少 1 道题的来源依据。
- 错题是否能被 due 查询查回。
- 需要人工核验的 OCR 或公式页面。

## 排障优先级

1. 数据文件损坏或覆盖风险。
2. 课程事实来源缺失。
3. API / CLI 输出 schema 不一致。
4. 前端主流程阻断。
5. OCR 识别质量问题。

## 运行边界

- 原始课程资料只读。
- 课程状态只写入对应 `review/`。
- 大型渲染缓存写入 `/tmp` 或课程内明确的 OCR 输出目录。
- 不把外部网页或模型记忆作为课程事实来源。
