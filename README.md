# Study Review Skill

CLI 本地课程复习工具：主动回忆 + 错题复查，基于本地课件与试卷 metadata 生成计划与变式题。

## 依赖

- Python 3.10+
- PyYAML

## 安装

```bash
git clone <repo-url>
cd study-review-skill
pip install pyyaml
```

## 完整 CLI 示例（6 步命令链）

```bash
python scripts/init_course_review.py "../计算机网络"
python scripts/analyze_exam.py "../计算机网络" --force
python scripts/generate_questions.py "../计算机网络" --count 5 --force
python scripts/plan_review.py "../计算机网络" --minutes 90 --goal pass --force
python scripts/review_session.py "../计算机网络" --source generated --limit 5
python scripts/due_today.py ..
```

## 当前限制

- 不解析 PDF/PPTX 内容，基于文件名和 `files.yaml` metadata 推断考点
- 规则判分（关键词子串匹配），准确率目标 ≥70%，MVP 不接 LLM
- 仅支持本地课程资料，不联网
- 交互模式在 Windows `cmd.exe` 下体验可能不佳，推荐 Windows Terminal

## 全栈启动（Phase 2 + 3）

```bash
# 终端 1 — API
cd Study_Review
set COURSES_ROOT=tests\fixtures
python -m uvicorn services.api.app:app --reload --port 8000

# 终端 2 — 前端
cd apps/web
npm run dev
# → http://localhost:5173 （通过 /api 代理到 8000）
```

## 开发状态

- **CLI MVP**：55/55 ✅
- **FastAPI 后端**（Phase 2）：`services/api/` ✅
- **React 前端**（Phase 3）：`apps/web/` Dashboard / 课程 / 答题 / 计划 / 分析 ✅
- **Phase 4**：`python tests/run_phase4_validation.py`（fixture 默认；真实目录设 `COURSE_PATH`）
- **测试**：33 条 Python + `npm run build` 通过

## 文档

- [docs/README.md](docs/README.md) — 文档体系总入口
- [docs/UPDATE_AND_ITERATION_PLAN.md](docs/UPDATE_AND_ITERATION_PLAN.md) — 当前更新与迭代计划
- [docs/DOCUMENTATION_SYSTEM.md](docs/DOCUMENTATION_SYSTEM.md) — 文档分层、维护规则和模板
- [tasks.md](tasks.md) — 任务清单与验收指标
- [PLAN.md](PLAN.md) — 历史实现路线图
- [DESIGN.md](DESIGN.md) — 设计原则
- [references/tech_stack.md](references/tech_stack.md) — 前端、后端、状态管理、PDF/OCR 与智能体技术选型
- [references/agent_framework_research.md](references/agent_framework_research.md) — 可复用复习智能体运行时、框架选型与模型 API 接入方向
- [scripts/ocr/README.md](scripts/ocr/README.md) — 本地 PDF 渲染、文本抽取与 macOS Vision OCR 脚本说明

## License

MIT
