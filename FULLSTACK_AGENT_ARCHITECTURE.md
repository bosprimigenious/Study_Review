# React + TypeScript + Python 全栈智能体架构记录

记录时间：2026-06-09  
项目背景：`study-review` 当前是一个 Codex skill 仓库，目标是进一步演化为可交互、可记录、可调度的复习智能体系统。

## 技术路线结论

推荐路线：

```text
Frontend: React + TypeScript
Backend: Python
Agent Layer: Python-first，后续可选 OpenAI Agents SDK / LangGraph
Data: Markdown + YAML 起步，后续 SQLite
Skill: 继续保留 SKILL.md 作为行为规范和 agent 操作手册
```

一句话：

> React + TS 负责好用的界面，Python 负责资料处理、复习记录、调度和 agent 编排，Skill 负责沉淀复习方法论。

## 为什么选 React + TypeScript + Python

### React + TypeScript 适合做前端

适合承担：

- 复习仪表盘
- 今日待复习列表
- 题卡答题界面
- 错题回看
- 科目进度
- 复习模式切换
- 文件/课程选择
- 复习资料上传
- 往年题/试卷重点分析
- 按试卷题型生成变式题

选择原因：

- React 生态成熟。
- TypeScript 能约束题卡、进度、复习记录等数据结构。
- 以后做成 Next.js 或桌面 Web UI 都顺。
- 前端交互状态复杂，TS 比纯 JS 更安全。

### Python 适合做后端和 agent 逻辑

适合承担：

- 扫描本地课程资料
- 解析 Markdown / YAML
- 写入错题记录
- 计算 due 日期
- 管理 `review/` 目录
- 调用模型生成问题、判分、解释
- 后续处理 PDF/PPT 文本抽取

选择原因：

- 文件处理和数据处理舒服。
- AI/LLM 生态成熟。
- PDF、PPT、YAML、SQLite 工具多。
- 当前已有脚本是 Python，迁移成本低。

## 当前 Skill 与未来全栈系统的关系

当前仓库：

```text
study-review-skill/
├── SKILL.md
├── references/
├── scripts/
└── examples/
```

未来系统不是替代 skill，而是把 skill 变成智能体的“行为宪法”：

```text
用户
  ↓
React + TS 前端
  ↓
Python API / Agent Backend
  ↓
Agent 根据 SKILL.md 和 references 决策
  ↓
Python scripts / services 操作 review 数据
  ↓
返回问题、判分、错题、复查计划
```

Skill 继续负责：

- 主动回忆优先
- 不先大段总结
- 不同学科用不同复习策略
- 错题要进入复查
- 题卡要原子化
- 评分档位和复查节奏
- 只依据当前 workspace 内资料回答事实性问题，除非用户明确解除限制

全栈应用负责：

- 展示界面
- 管理状态
- 保存数据
- 提供交互入口
- 让复习过程更连续

## 推荐总体架构

```text
study-review/
├── apps/
│   └── web/                    # React + TypeScript 前端
├── services/
│   └── api/                    # Python 后端
├── skill/
│   └── study-review-skill/     # 当前 skill 仓库，可作为子模块或复制
├── data/
│   └── courses/                # 课程资料和 review 数据
└── docs/
    └── architecture.md
```

在当前仓库内，短期也可以先这样记：

```text
study-review-skill/
├── SKILL.md
├── references/
├── scripts/
├── examples/
└── FULLSTACK_AGENT_ARCHITECTURE.md
```

## 前端职责

React + TypeScript 前端不应该负责智能判断。它负责把复习流程做得顺手。

### 页面设计

建议页面：

1. **Dashboard**
   - 今日待复习数量
   - 各科进度
   - 最近错题
   - 快速开始按钮

2. **Course Review**
   - 当前科目资料列表
   - 章节进度
   - 推荐复习模式
   - 开始诊断 / 继续复习

3. **Quiz Session**
   - 当前问题
   - 用户答案输入
   - 判定结果
   - 更稳答法
   - 追问题
   - 评分按钮：忘了 / 困难 / 还行 / 很熟

4. **Mistake Log**
   - 按科目、章节、错因筛选
   - 展示原题、错误、正确理解、下次复查

5. **Cards**
   - 题卡列表
   - tags
   - due 日期
   - difficulty

6. **Materials Upload**
   - 拖拽上传 PPT、PDF、Word、Markdown、图片或压缩包
   - 用户确认文件类型：课件、往年题、样题、作业答案、老师重点、笔记、教材/讲义、其他
   - 显示每个文件的解析状态
   - 上传后提示是否进入试卷分析或生成今日计划

7. **Exam Analysis**
   - 选择一门课和若干试卷/往年题
   - 选择分析目标：重点分析、高频题型、变式题、复习计划
   - 展示高频章节、题型分布、对应复习资料、推荐优先级
   - 支持一键生成模拟题/变式题并加入复习会话

### TypeScript 数据类型

前端应围绕这些类型建模：

```ts
export type Rating = "忘了" | "困难" | "还行" | "很熟";

export type MaterialType =
  | "slides"
  | "past_exam"
  | "mock_exam"
  | "homework_answer"
  | "teacher_focus"
  | "notes"
  | "textbook"
  | "other";

export interface MaterialFile {
  id: string;
  courseId: string;
  name: string;
  type: MaterialType;
  size: number;
  ext: string;
  uploadedAt: string;
  status: "pending" | "uploaded" | "indexing" | "ready" | "failed";
  path?: string;
}

export interface StudyCard {
  id: string;
  subject: string;
  chapter?: string;
  topic: string;
  prompt: string;
  answer: string;
  tags: string[];
  difficulty: "basic" | "medium" | "hard";
  source?: string;
  schedule: {
    rating?: Rating;
    lastReviewed?: string;
    due?: string;
  };
}

export interface MistakeEntry {
  id: string;
  subject: string;
  chapter?: string;
  topic: string;
  question: string;
  mistake: string;
  correction: string;
  rating: Rating;
  due: string[];
  createdAt: string;
}

export interface CourseProgress {
  subject: string;
  stage: "诊断" | "补弱" | "冲刺";
  lastReviewed?: string;
  weakestTopics: string[];
  nextAction: string;
  chapters: {
    name: string;
    status: "未开始" | "复习中" | "已完成";
  }[];
}

export interface PastExamPattern {
  id: string;
  courseId: string;
  sourceFile: string;
  year?: string;
  questionType: string;
  topic: string;
  chapter?: string;
  difficulty: "basic" | "medium" | "hard";
  originalQuestion?: string;
  answerShape: string;
  scoringPoints: string[];
  reusableTemplate: string;
}

export interface ExamPriority {
  topic: string;
  chapter?: string;
  weight: number;
  evidence: {
    sourceFile: string;
    reason: string;
  }[];
  recommendedAction: string;
}

export interface GeneratedQuestion {
  id: string;
  courseId: string;
  basedOnPatternId?: string;
  sourceMaterialIds: string[];
  questionType: string;
  topic: string;
  prompt: string;
  expectedAnswer: string;
  scoringPoints: string[];
  difficulty: "basic" | "medium" | "hard";
  similarity: "same_type" | "same_topic" | "mixed";
  timeLimitSec?: number;
}

export interface ExamAnalysis {
  id: string;
  courseId: string;
  sourceFileIds: string[];
  generatedAt: string;
  patterns: PastExamPattern[];
  priorities: ExamPriority[];
  generatedQuestions: GeneratedQuestion[];
  plan: {
    thirtyMinutes?: string[];
    ninetyMinutes?: string[];
    threeDays?: string[];
    sevenDays?: string[];
  };
}
```

## 后端职责

Python 后端负责业务逻辑和本地文件操作。

### API 建议

```text
GET  /courses
GET  /courses/{course}/inventory
POST /courses/{course}/init-review
GET  /courses/{course}/progress
PATCH /courses/{course}/progress
GET  /due-today
GET  /cards
POST /cards
POST /courses/{course}/materials
GET  /courses/{course}/materials
POST /courses/{course}/exam-analysis
GET  /courses/{course}/exam-analysis/latest
POST /courses/{course}/exam-analysis/{analysis_id}/questions
POST /courses/{course}/exam-analysis/{analysis_id}/plan
POST /review-session/start
POST /review-session/answer
POST /mistakes
```

### 后端模块

```text
services/api/
├── app.py
├── routes/
│   ├── courses.py
│   ├── cards.py
│   ├── materials.py
│   ├── exams.py
│   ├── sessions.py
│   └── mistakes.py
├── core/
│   ├── scheduler.py
│   ├── inventory.py
│   ├── storage.py
│   ├── material_matcher.py
│   ├── exam_analyzer.py
│   ├── question_generator.py
│   ├── planner.py
│   └── agent.py
└── tests/
```

### 后端初期存储

第一阶段继续用文件：

```text
course/review/
├── progress.md
├── mistake-log.md
├── cards.yaml
├── files.yaml
├── exam-analysis.yaml
├── past-exam-patterns.yaml
├── generated-questions.yaml
└── plan.md
```

以后再迁移到 SQLite：

```text
study_review.db
├── courses
├── material_files
├── exam_analyses
├── past_exam_patterns
├── generated_questions
├── cards
├── mistakes
├── review_sessions
└── review_events
```

不要太早上数据库。当前最重要的是把复习闭环跑通。

## Agent 层

Agent 层的详细规范放在 `references/orchestrator.md`。本节只保留全栈架构视角：后端如何调用总控 agent，以及何时升级框架。

### Source Policy

所有后续 agent 实现都必须继承 `references/source_policy.md`：

```text
Only read and rely on files inside /Users/bosprimigenious/Important_FIles/2025-2026下.
Do not use web search, GitHub, external websites, repository-external files, or model memory as factual sources.
If the answer is not supported by workspace files, say the workspace materials are insufficient.
```

这条规则应同时写入：

- agent system/developer instructions
- Python backend agent prompt
- subtask/delegation prompt
- tool routing logic
- README or product help text

### 第一阶段：Skill-guided Agent

不急着上重框架。

方式：

- 后端读 `SKILL.md` 和必要 reference。
- 对总控行为读取 `references/orchestrator.md`。
- 把当前课程、进度、错题、用户请求组合成 prompt。
- 调用模型生成问题、判分、解释、追问。
- 用 Python 脚本保存结果。

优点：

- 简单。
- 贴合当前仓库。
- 容易调试。

### 第二阶段：OpenAI Agents SDK

适合当功能变多后引入。

Agent 可以定义：

- instructions：来自 `SKILL.md`
- tools：inventory、review_log、due_today、init_course_review
- structured output：题卡、判分结果、复习计划

适合场景：

- 想保持轻量。
- 想使用官方 agent 抽象。
- 想让工具调用和 structured output 更规范。

### 第三阶段：LangGraph

适合当复习流程变成清晰状态机。

例如：

```text
Start
  ↓
Load Course Context
  ↓
Choose Mode
  ↓
Ask Question
  ↓
Wait For Answer
  ↓
Grade Answer
  ↓
Record Mistake?
  ↓
Schedule Review
  ↓
Next Question / End Session
```

适合场景：

- 需要可恢复 session。
- 需要明确状态转移。
- 需要多步骤流程可观察、可测试。

## 数据流

### 开始复习

```text
用户点击“开始复习”
  ↓
前端 POST /review-session/start
  ↓
后端读取 course/review/progress.md 和 cards.yaml
  ↓
Agent 选择模式并生成第一题
  ↓
前端展示题目
```

### 提交答案

```text
用户提交答案
  ↓
前端 POST /review-session/answer
  ↓
Agent 判分并生成反馈
  ↓
后端根据 rating 写 mistake-log / cards.yaml
  ↓
前端展示判定、遗漏、更稳答法、追问题
```

### 今日复习

```text
前端 GET /due-today
  ↓
后端扫描所有 course/review/cards.yaml
  ↓
返回按科目分组的 due cards
  ↓
前端展示今日待复习列表
```

### 上传资料并分析试卷

```text
用户上传 PPT / PDF / 往年题
  ↓
前端 POST /courses/{course}/materials
  ↓
后端保存文件并写入 files.yaml
  ↓
用户点击“分析试卷”
  ↓
前端 POST /courses/{course}/exam-analysis
  ↓
后端识别题型、考点、答案结构
  ↓
后端匹配本地课件/复习资料
  ↓
Agent 生成重点、变式题和计划
  ↓
前端展示 Exam Analysis 页面
```

### 按试卷生成练习

```text
用户选择“高频混合卷”或“同题型变式”
  ↓
前端 POST /courses/{course}/exam-analysis/{analysis_id}/questions
  ↓
后端从 past-exam-patterns.yaml 和本地资料生成题目
  ↓
写入 generated-questions.yaml / cards.yaml
  ↓
前端进入 Quiz Session
```

## 开发阶段

### Phase 0：继续强化 Skill 仓库

目标：

- 完成 `PLAN.md` 中 P0。
- 保持 `SKILL.md` 精简，并把产品、试卷分析、总控细节分别放在 `product_mvp.md`、`past_exam_analysis.md`、`orchestrator.md`。
- 补 `question_patterns.md`。
- 补 `data_formats.md`。
- 做 `init_course_review.py`。
- 升级 `review_log.py` 和 `due_today.py`。

这是前置条件。

### Phase 1：Python CLI 闭环

目标：

- 不做 UI。
- 用命令行跑通完整流程。

完成定义：

```text
inventory -> init review -> record mistake -> due today
```

### Phase 2：Python API

目标：

- 把 CLI 能力封装成 API。
- 暂时不做复杂 agent 框架。

建议框架：

```text
FastAPI
```

原因：

- Python 生态成熟。
- API schema 清楚。
- 和 TS 前端对接舒服。

### Phase 3：React + TS Web

目标：

- 做最小可用前端。

页面优先级：

1. 今日复习
2. 复习会话
3. 错题本
4. 资料上传
5. 试卷分析
6. 科目进度

不要先做漂亮 dashboard。先让答题体验顺。

### Phase 4：Agent 框架化

目标：

- 根据实际复杂度决定 OpenAI Agents SDK 或 LangGraph。

选择标准：

- 如果只是工具调用和 structured output：OpenAI Agents SDK。
- 如果会话状态复杂，需要流程恢复：LangGraph。

## 技术栈建议

### 前端

```text
React
TypeScript
Vite 或 Next.js
TanStack Query
Zod
```

选择：

- 纯本地工具：Vite 更轻。
- 想做完整 Web 产品：Next.js 更顺。

### 后端

```text
Python
FastAPI
Pydantic
PyYAML
pytest
```

### Agent

```text
OpenAI Agents SDK 或 LangGraph
```

暂时不选定，等 CLI 和 API 稳定后再判断。

### 存储

第一阶段：

```text
Markdown + YAML
```

第二阶段：

```text
SQLite
```

不要一开始上 PostgreSQL。

## 暂不做

- 不先做移动 App。
- 不先做复杂多人系统。
- 不先做 OAuth/账号系统。
- 不先做 Web 面板统计图。
- 不先做 FSRS。
- 不先强制迁移数据库。

## 与当前计划的衔接

当前 `PLAN.md` 的 P0 是全栈系统的地基：

```text
提问模板库
课程 review 目录
进度文件
错题到复查闭环
真实课程端到端测试
```

只有这些稳定了，React + TS + Python 才有东西可展示、可调用、可保存。

## 当前推荐下一步

继续先做 skill 仓库，不急着开前端工程。

顺序：

1. 保持 `SKILL.md` 精简，只做总控入口和行为规则。
2. 补 `references/question_patterns.md`。
3. 补 `references/data_formats.md`。
4. 补 `examples/sample_progress.md` 和 `examples/sample_cards.yaml`。
5. 写 `scripts/init_course_review.py`。
6. 写 `scripts/analyze_exam.py`。
7. 升级 `review_log.py` 和 `due_today.py`。
8. 用 `计算机网络` 跑通 CLI 闭环。
9. 再开 FastAPI。
10. 最后开 React + TS。

原因：

- 前端太早做，会被不断变化的数据格式拖着改。
- 先把复习闭环做硬，UI 才不会只是壳。
