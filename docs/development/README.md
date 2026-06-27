# Development Docs

最后更新：2026-06-27

## 入口

| 文档 | 角色 |
| --- | --- |
| [../../tasks.md](../../tasks.md) | 工程任务和验收指标 |
| [../../PLAN.md](../../PLAN.md) | 历史路线图和版本背景 |
| [../UPDATE_AND_ITERATION_PLAN.md](../UPDATE_AND_ITERATION_PLAN.md) | 当前迭代计划 |
| [../../CURSOR_MASTER_PLAN.md](../../CURSOR_MASTER_PLAN.md) | Cursor 执行计划和阶段指令 |
| [../../apps/web/README.md](../../apps/web/README.md) | 前端开发说明 |
| [../../scripts/ocr/README.md](../../scripts/ocr/README.md) | macOS PDF/OCR 辅助脚本 |

## 本地开发命令

Python 测试：

```bash
python -m pytest tests
```

API 开发：

```bash
python -m uvicorn services.api.app:app --reload --port 8000
```

前端开发：

```bash
cd apps/web
npm run dev
```

前端构建：

```bash
cd apps/web
npm run build
```

Swift OCR 脚本在受限环境中运行时：

```bash
export CLANG_MODULE_CACHE_PATH=/tmp/study-review-clang-cache
swift scripts/ocr/render_pdf_pages.swift "input.pdf" "/tmp/pdf-pages" 2.0
```

## 开发规则

- 先更新或确认验收标准，再实现功能。
- 状态文件写入必须走统一 IO helper，保护用户长期数据。
- 新字段先更新 `references/data_formats.md` 和 examples。
- 新 API 先补测试或样例响应。
- 新前端流程必须覆盖 loading、empty、error、success 四类状态。
