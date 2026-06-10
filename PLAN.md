# Study Review Skill 开发计划

制定时间：2026-06-09  
最近更新：2026-06-10  
版本：v3.1，新增商业化路线图索引；产品全景见 `PRODUCT_ARCHITECTURE.md`  
依据：当前仓库、`DESIGN.md`、`PRODUCT_ARCHITECTURE.md`、`RESEARCH_REPORT.md`、`references/student_needs_research.md`、`references/product_mvp.md`、对标项目（含 NovaOrbit），以及当前 workspace 里的实际课程资料。

## 一句话判断

这个项目最有价值的部分不是“自动总结课件”，而是让 Codex 变成一个能长期陪你复习的考试搭子：

> 先问问题，发现薄弱点，记录错因，隔天再抽查。

因此第一版必须优先开发“资料到行动”的复习闭环，而不是先做复杂导出、FSRS、Web 面板或完美 PPT/PDF 解析。

用户最强需求可以压成一句话：

> 我有一堆 PPT、往年题、作业答案和老师重点，但快考试了，请告诉我先复习什么，按考法出题，一题一题带我做，并把错题安排到考前复查。

## 当前仓库状态

已有结构：

```text
study-review-skill/
├── SKILL.md
├── DESIGN.md
├── RESEARCH_REPORT.md
├── agents/openai.yaml
├── references/
│   ├── artifacts.md
│   ├── card_quality.md
│   ├── modes.md
│   └── subject_profiles.md
├── scripts/
│   ├── due_today.py
│   ├── inventory.py
│   └── review_log.py
└── examples/sample_session.md
```

当前已经不错的部分：

- skill 的行为方向清楚：主动回忆优先。
- `SKILL.md` 已蒸馏成总控智能体入口，细节拆到 `references/`。
- `references/orchestrator.md` 已定义单总控 agent、状态机、意图路由和工具契约。
- `references/agent_development_plan.md` 已扩展智能体开发路线、状态快照、工具成熟度、API 形状和评测方案。
- `references/student_needs_research.md` 已沉淀大学生期末需求和功能优先级。
- `references/product_mvp.md` 已统一标记 MVP、付费入口、后续功能和笔记风险。
- `references/past_exam_analysis.md` 已定义试卷/往年题分析模块。
- `references/question_patterns.md` 和 `references/data_formats.md` 已补齐第一版问题模板与数据契约。
- `examples/sample_files.yaml`、`sample_progress.md`、`sample_cards.yaml`、`sample_exam_analysis.yaml` 已提供样例数据。
- `scripts/init_course_review.py` 已实现课程 `review/` 工作区初始化，并验证不会覆盖已有文件。
- 五门课的复习策略已经分开。
- 文件夹扫描、错题记录、到期查看都有最小脚本。
- 对标分析已经说明：成熟复习系统都绕不开题卡、日志、调度。

当前真正急缺的部分：

- `scripts/analyze_exam.py` 还没有实现。
- `scripts/generate_questions.py` 还没有实现。
- `scripts/plan_review.py` 还没有实现。
- `scripts/review_session.py` 还没有实现，一题一答还没有正式入口。
- 错题记录和到期复习还没有形成闭环。
- 没有用真实科目跑过端到端验证。

## MVP 闭环审查结论

结论：

- **产品闭环成立**：已经明确从资料、往年题、计划、练题、错题到复查的完整路径。
- **文档闭环基本成立**：`SKILL.md`、`references/orchestrator.md`、`references/product_mvp.md`、`references/data_formats.md` 已经能约束 agent 和脚本行为。
- **执行闭环尚未完成**：目前只有初始化脚本可运行；试卷分析、变式题、计划、一题一答、错题复查还需要补齐。

MVP 必须收束成这一条可运行链路：

```text
init_course_review
  -> analyze_exam
  -> generate_questions
  -> plan_review
  -> review_session
  -> review_log
  -> due_today
```

如果缺少 `review_session`，MVP 会停在“生成题和计划”，但不能证明用户真的被带着完成复习。因此一题一答会话必须进入 v0.2，而不是放到后面的前端阶段。

MVP 可验收标准：

- 一门真实课程能生成 `review/` 工作区。
- 至少 1 份往年题/样题/老师重点能进入分析结果。
- 至少生成 5 道带标准答案、评分点和来源依据的题。
- 至少生成 1 份 90 分钟保底计划。
- 用户能回答至少 1 道题，并得到 `correct | partial | wrong` 判定。
- 至少 1 条错题能写入 `mistake-log.md` 和 `cards.yaml`。
- `due_today.py` 能在当天或次日查回该错题。
- 所有课程事实必须来自本地课程资料、分析文件或用户刚输入的答案。

## 版本路线图

### v0.1：文档和契约地基 `基本完成`

目标：让项目方向、智能体行为、数据格式、问题模板稳定下来。

产物：

- `SKILL.md` 总控入口。
- `references/orchestrator.md`。
- `references/agent_development_plan.md`。
- `references/student_needs_research.md`。
- `references/product_mvp.md`。
- `references/past_exam_analysis.md`。
- `references/question_patterns.md`。
- `references/data_formats.md`。
- `examples/*.yaml` / `examples/*.md`。

完成标准：

- agent 知道什么时候救火规划、什么时候分析往年题、什么时候一题一答。
- 数据文件有稳定字段，不再边写脚本边猜格式。
- 文档中不再把已完成项当作待办。

### v0.2：CLI 最小闭环 `当前目标`

目标：不用前端，先让一门真实课程跑通。

链路：

```text
inventory
  -> init_course_review
  -> analyze_exam
  -> generate_questions
  -> plan_review
  -> review_session
  -> review_log
  -> due_today
```

完成标准：

- `计算机网络/review/` 可生成并重复运行安全。
- 能从样题/课件生成非空 `exam-analysis.yaml`。
- 能生成 5 道变式题。
- 能生成 90 分钟保底计划。
- 能启动一题一答会话并判定用户答案。
- 能记录 1 条错题并在 due 查询中出现。

### v0.3：Agent 编排闭环

目标：把 CLI 能力接到 `StudyReviewOrchestrator` 的意图路由里。

完成标准：

- 用户说“今晚怎么不挂”，agent 能选择计划流程。
- 用户说“按往年题出题”，agent 能选择试卷分析和出题流程。
- 用户回答题目后，agent 能判分、记录错题、安排复查。
- agent 不假装未实现工具已经运行。

开发顺序：

1. **Prompt-orchestrated agent**：先让 `SKILL.md` 规定总控行为，由 Codex 调用 CLI，不引入复杂框架。
2. **Tool-backed orchestrator**：每个脚本稳定后包装成工具契约，输入输出都对齐 `references/data_formats.md`。
3. **Structured outputs**：agent 返回固定 JSON/Markdown 结构，方便 API 和前端消费。
4. **API-backed orchestrator**：FastAPI 提供 `POST /agent/run`，由后端统一路由到工具。
5. **Optional framework**：只有当状态分支和异步任务明显复杂后，才考虑 OpenAI Agents SDK 或 LangGraph；MVP 阶段不先上多 agent。

详细开发计划见：

```text
references/agent_development_plan.md
```

v0.3 的原则：

- 一个总控智能体负责决策。
- Python 工具负责确定性读写和文件状态。
- LLM 只做判断、解释、出题、评分，不直接改状态文件。
- 所有落盘动作都通过脚本或后端服务完成。

### v0.4：FastAPI 后端

目标：把 CLI 能力封装成 API，为前端做准备。

核心接口：

```text
GET  /courses
POST /courses/{course}/init-review
GET  /courses/{course}/materials
POST /courses/{course}/exam-analysis
POST /courses/{course}/questions
POST /courses/{course}/plan
POST /mistakes
GET  /due-today
```

完成标准：

- API 返回结构和 `references/data_formats.md` 一致。
- 后端不直接编造课程内容，只调工具/agent。
- 每个接口有最小测试或样例请求。

### v0.5：React 前端 MVP

目标：做工具型界面，不做精美 dashboard。

页面：

- 课程页
- 上传/登记资料页
- 试卷分析页
- 今晚计划页
- 一题一答练习页
- 错题复查页

完成标准：

- 用户能从“上传资料”一路走到“开始 5 题摸底”。
- `分析往年题` 是明确主按钮。
- 计划页必须有“现在开始”动作。

### v1.0：可用期末复习产品

目标：面向真实期末周使用。

完成标准：

- 至少 3 门课真实跑通。
- 每门课至少完成一次：资料登记、试卷分析、变式题、计划、错题复查。
- 输出内容可追溯到本地资料。
- 用户不需要理解仓库结构也能完成复习流程。

## 需求到功能映射

调研后，功能必须围绕期末周高压场景排序。

| 学生需求 | 产品功能 | 工程落点 | 优先级 |
| --- | --- | --- | --- |
| 来不及了，不知道先看什么 | 今晚/三天救火计划 | `plan_review.py`, `plan.md` | P0 |
| 资料太多，不知道重点 | 资料分类和重点查找 | `files.yaml`, `data_formats.md`, later material index | P0 |
| 有往年题，想知道高频题型 | 试卷/往年题分析 | `analyze_exam.py`, `exam-analysis.yaml` | P0 |
| 想按考法练题 | 变式题生成 | `generate_questions.py`, `generated-questions.yaml` | P0 |
| 看 PPT 感觉会，答题写不出 | 一题一答抽查 | `question_patterns.md`, future review session | P0 |
| 错了容易忘 | 错题记录和到期复查 | `review_log.py`, `due_today.py`, `cards.yaml` | P0 |
| 想要速成笔记 | 今晚保底笔记/错题笔记 | after analysis and plan are stable | P1 |
| 想导出/分享 | PDF/Word/Anki/分享 | later | P2 |

第一版不追求“全科完整笔记”，只追求：

```text
资料 -> 重点 -> 题 -> 计划 -> 答题 -> 错题 -> 复查
```

## 功能模块边界

### 总控 Agent

负责：

- 理解用户目标。
- 判断课程状态。
- 选择下一步工具。
- 保持 source policy。
- 把工具结果变成行动。

不负责：

- 直接解析所有文件。
- 自己维护数据库。
- 凭空补课程知识。
- 替代确定性脚本。

### CLI Scripts

负责：

- 初始化目录。
- 读取/写入 YAML 和 Markdown。
- 查找 due 项。
- 生成确定性框架结果。

不负责：

- 做复杂教学判断。
- 长篇解释课程内容。
- 绕过 source policy。

### Future API

负责：

- 将脚本能力暴露给前端。
- 做输入校验。
- 返回结构化结果。

不负责：

- 把业务规则藏在前端。
- 直接写不符合数据契约的临时格式。

### Future Frontend

负责：

- 让上传、分析、计划、练习变得低摩擦。
- 展示来源、计划、题目、错题。

不负责：

- 判断课程事实。
- 生成题目。
- 管理复习调度算法。

## 功能优先级

### P0：必须先做

这些功能直接决定它是不是一个好用的复习 skill。

1. **提问模板库** `已完成文档，待接入工具`
   没有好问题，复习就会退化成总结。已沉淀诊断题、概念辨析题、公式条件题、协议流程题、计算题、简答题、追问题；下一步要让出题脚本实际使用它。

2. **课程 review 目录** `脚本已完成，待真实课程落地`
   每门课必须有自己的复习状态区，例如 `计算机网络/review/`。`init_course_review.py` 已可生成标准目录和文件；下一步是对真实课程运行并检查产物。

3. **进度文件** `格式已定义，待自动更新`
   需要知道“上次复习到哪、最弱点是什么、下一步问什么”。`progress.md` 格式已定义；后续脚本需要自动更新它。

4. **错题到复查闭环** `待实现`
   答错后要能写入错题，再由 `due_today.py` 在未来某天抽回来。

5. **真实课程端到端测试** `待执行`
   必须用 `计算机网络` 或 `概率论与数理统计` 跑一次完整流程。纸面计划不等于好用。

6. **试卷重点分析模块** `文档已完成，脚本待实现`
   用户上传试卷、往年题、样题或作业答案后，系统要能识别题型和考点，匹配本地复习资料章节，输出高频重点，生成模拟题/变式题，并形成短期复习计划。

7. **总控智能体契约** `已完成文档，待接入后端`
   `SKILL.md` 保持精简，`references/orchestrator.md` 承接状态机、意图路由、工具输入输出和失败处理。

### P1：必要但不抢第一批

这些功能有价值，但要建立在 P0 稳定之后。

1. **结构化题卡 `cards.yaml`**
   很有必要，因为 Markdown 适合人看，YAML 适合脚本查到期和导出。但第一步可以先只支持核心字段。

2. **数据格式文档**
   需要写清 `progress.md`、`mistake-log.md`、`cards.yaml`。这会让后续脚本少很多歧义。

3. **README**
   作为 GitHub 仓库需要，但它不提升复习质量。放在 P1。

4. **脚本测试**
   `review_log.py` 和 `due_today.py` 一旦开始改 YAML，就需要最小测试，避免日期和路径逻辑坏掉。

5. **题卡校验**
   对 `cards.yaml` 检查必填字段、日期、id 唯一性。等题卡格式定下来再做。

### P2：以后再做

这些功能听起来酷，但现在不是急缺。

1. **Anki 导出**
   有价值，但当前目标是让 Codex 内部复习闭环跑起来。Anki 导出可以等题卡格式稳定后做。

2. **FSRS 调度**
   对长期大规模题卡有用，但期末冲刺阶段 D+1/D+3/D+7 已经够用。先保留字段，别先上依赖。

3. **PPT/PDF 自动解析**
   资料抽取很诱人，但容易陷入格式泥潭。当前 Codex 可以先按需读取材料，脚本不急着承担抽取质量。

4. **本地 Web 面板**
   适合展示统计，但不是复习质量核心。CLI 和数据结构稳定后再考虑。

5. **完整 study pack 生成器**
   `outline + glossary + quiz + flashcards + exercises` 很完整，但第一版先别追求一键生成所有材料。

## 第一阶段：把“问得好”做出来 `已完成文档`

目标：Codex 触发 skill 后，能稳定用高质量问题带你复习。

已新增：

```text
references/question_patterns.md
```

内容必须覆盖：

- 诊断题：快速判断基础、应用、综合能力。
- 主动回忆题：逼用户从记忆里取答案。
- 概念辨析题：处理易混概念。
- 公式条件题：尤其适合概率论。
- 协议流程题：尤其适合计算机网络。
- 计算步骤题：尤其适合计组和概率论。
- 构造/证明题：尤其适合理论计算机。
- 闭卷简答题：尤其适合毛概。
- 错题追问题：答错后继续追问相邻薄弱点。

验收标准：

- 每类至少 3 个模板。`已完成`
- 每门当前课程至少有 5 个可直接套用的模板。`已完成`
- `SKILL.md` 的 Bundled Resources 引用它。`已完成`
- 用 `计算机网络` 能生成一组 5 题诊断题。`待工具化验证`

为什么急：

- 这是整个 skill 的“教学质量核心”。
- 没它，Codex 容易回到普通总结模式。

## 第二阶段：定义课程 review 工作区 `基础已完成，待真实课程运行`

目标：每门课有稳定的复习状态，不再每次从零开始。

已新增：

```text
references/data_formats.md
examples/sample_progress.md
examples/sample_cards.yaml
examples/sample_files.yaml
examples/sample_exam_analysis.yaml
scripts/init_course_review.py
```

课程目录目标结构：

```text
计算机网络/
├── 原始课件...
└── review/
    ├── progress.md
    ├── mistake-log.md
    ├── cards.yaml
    ├── files.yaml
    ├── exam-analysis.yaml
    ├── past-exam-patterns.yaml
    ├── generated-questions.yaml
    └── plan.md
```

`progress.md` 保存：

- 当前阶段：诊断 / 补弱 / 冲刺
- 最近复习日期
- 当前最弱知识点
- 下一轮建议
- 章节进度

`mistake-log.md` 保存：

- 问题
- 用户错误
- 正确理解
- 错因标签
- 复查日期

`cards.yaml` 保存：

- 题干
- 答案
- 学科/章节/知识点
- tags
- difficulty
- schedule

`init_course_review.py` 必须做到：

- 创建 `review/`。
- 不覆盖已有文件。
- 根据课程文件名生成初始章节列表。
- 对重复运行安全。
- 不碰原始课件。

验收标准：

- `--dry-run` 对 `计算机网络` 能识别资料并显示将创建的文件。`已完成`
- 对临时课程目录实际运行，生成完整 `review/`。`已完成`
- 重复运行不覆盖已有文件。`已完成`
- 对真实 `计算机网络` 目录实际初始化并人工检查产物。`待执行`
- 生成的 `progress.md` 人能直接看懂下一步。`已完成样例，待真实课程确认`

为什么急：

- 没有 review 工作区，就没有长期记忆。
- 这是从“一次聊天”变成“复习系统”的边界。

## 第三阶段：打通错题到复查 `下一批实现`

目标：用户答错一次，未来能被系统重新抽回来。

升级：

```text
scripts/review_log.py
scripts/due_today.py
```

### review_log.py 必做

新增参数：

```text
--course
--chapter
--difficulty
--tags
--source
```

行为：

- 写入 `COURSE/review/mistake-log.md`。
- 同步追加到 `COURSE/review/cards.yaml`。
- 根据 rating 生成 due。
- 自动生成稳定且不冲突的 card id。

评分映射：

```text
忘了 -> 今天 + 明天
困难 -> D+1
还行 -> D+3
很熟 -> D+7
```

### due_today.py 必做

行为：

- 扫描 workspace 下所有 `*/review/cards.yaml`。
- 扫描所有 `*/review/mistake-log.md` 中未勾选 due。
- 按课程分组输出。
- 支持 `--subject` 过滤。
- 支持 `--json`，方便以后接 UI。

验收标准：

- 记录一条 `计算机网络` 错题后，今天或明天能查到。
- 修改 rating 后 due 日期符合预期。
- 没有到期项时输出清楚提示。
- 不因为某门课的 YAML 坏掉而整个崩溃，要提示具体文件。

为什么急：

- 复习最容易失败的地方不是第一次学，而是错过复查。
- 这是 active recall 和 spaced repetition 的最小闭环。

## 第四阶段：试卷/往年题分析重点

目标：把“上传试卷/往年题 -> 找重点 -> 出变式题 -> 给计划”做成正式功能，而不是靠临时提示词。

已新增文档，待新增脚本：

```text
references/past_exam_analysis.md
references/product_mvp.md
scripts/analyze_exam.py
```

流程：

```text
上传试卷/往年题
  ↓
识别题型和考点
  ↓
匹配复习资料章节
  ↓
输出高频重点
  ↓
生成模拟题/变式题
  ↓
形成复习计划
```

前端必须支持：

- 资料上传页：PPT、PDF、Word、Markdown、图片、压缩包。
- 文件类型标记：课件、往年题、样题、作业答案、老师重点、笔记、教材/讲义、其他。
- 试卷分析页：展示高频章节、题型分布、对应资料、推荐复习优先级。
- 出题页：支持同题型变式、同考点变式、高频混合卷、保底卷、错题变式卷。
- 一键进入复习会话：生成题后直接开始作答、判分、记录错题。

后端必须支持：

```text
POST /courses/{course}/materials
GET  /courses/{course}/materials
POST /courses/{course}/exam-analysis
GET  /courses/{course}/exam-analysis/latest
POST /courses/{course}/exam-analysis/{analysis_id}/questions
POST /courses/{course}/exam-analysis/{analysis_id}/plan
```

数据文件：

```text
course/review/
├── files.yaml
├── exam-analysis.yaml
├── past-exam-patterns.yaml
├── generated-questions.yaml
└── plan.md
```

验收标准：

- 能对一门课识别至少 3 类题型或考点。`待实现`
- 每个高频重点都能回到本地资料或试卷文件。`待实现`
- 能生成至少 5 道标注为 `模拟题` 或 `变式题` 的练习题。`待实现`
- 每题包含标准答案、评分点、来源依据和建议限时。`待实现`
- 输出 30 分钟、90 分钟、3 天三种复习计划。`待实现`
- 不承诺押题，不生成或索要泄题内容。

为什么急：

- 这是用户最直接的期末需求：我有试卷和资料，想知道先复习什么、会怎么考、该练什么。
- 这个模块比普通笔记更有付费价值，也能把上传资料、规划、出题、错题复查串起来。

## 第五阶段：真实复习验证

目标：用当前资料验证 skill 不是“文档好看”。

先选 `计算机网络`，因为它材料结构清晰、有样题，且适合问答。

验证流程：

1. 运行 `inventory.py`，确认能识别课程资料。
2. 运行 `init_course_review.py "../计算机网络"`。
3. Codex 使用 `question_patterns.md` 生成 5 题诊断。
4. 用户模拟答错 1 题。
5. 运行 `review_log.py` 记录错题。
6. 运行 `due_today.py ..` 查到复查项。
7. 更新 `progress.md`，写明下一步。

验收标准：

- 没有大段无目的总结。
- 提问符合计网考试风格。
- 错题能进入 `mistake-log.md` 和 `cards.yaml`。
- 到期项能被查到。
- 生成文件不污染原始课件目录，只写 `review/`。

通过后再验证：

- `概率论与数理统计`：测试公式条件、计算题、错题变式。
- `毛概PPT复习`：测试闭卷简答、关键词抽背。

## 第六阶段：文档和稳定性

目标：让这个仓库可以给未来的自己或别人使用。

新增或完善：

```text
README.md
tests/
```

README 只写：

- 这个 skill 解决什么问题。
- 怎么安装。
- 常用命令。
- 当前限制。

测试优先覆盖：

- `init_course_review.py` 不覆盖文件。
- `review_log.py` due 日期正确。
- `due_today.py` 能扫描多个课程。
- 坏 YAML 有清楚报错。

验收标准：

- README 不超过 150 行。
- `python -m unittest` 或同等命令能跑完脚本测试。

## 不建议现在开发的功能

### Anki 导出

原因：

- 只有题卡数据稳定后才值得导出。
- 现在更急的是在 Codex 里形成复习闭环。

进入条件：

- `cards.yaml` 已经在至少 3 门课中真实使用。

### FSRS

原因：

- 复杂度高，引入依赖。
- 当前期末复习周期短，简单间隔已经能解决主要问题。

进入条件：

- 题卡数量达到数百张，且用户确实每天复习。

### PPT/PDF 自动全文抽取

原因：

- 文件格式复杂，容易把时间花在脏数据处理上。
- Codex 已能按需读取材料，第一版不用把抽取脚本做成核心依赖。

进入条件：

- 已有稳定 review 闭环，但人工挑材料太慢。

### Web 面板

原因：

- 漂亮但不急。
- 数据结构没稳定前做 UI 会反复改。

进入条件：

- `due_today.py --json` 输出稳定。

## 修订后的执行顺序

1. 写 `references/question_patterns.md`。
2. 在 `SKILL.md` 中引用 question patterns。
3. 写 `references/data_formats.md`。
4. 写 `examples/sample_progress.md` 和 `examples/sample_cards.yaml`。
5. 写 `scripts/init_course_review.py`。
6. 写 `scripts/analyze_exam.py`。
7. 升级 `review_log.py`，支持课程 review 目录和 cards.yaml。
8. 升级 `due_today.py`，支持 workspace 扫描。
9. 用 `计算机网络` 跑端到端。
10. 补最小测试。

## 第一版完成定义

第一版完成不是“功能很多”，而是下面这条链路稳定：

```text
扫描资料 -> 初始化 review -> 分析试卷 -> 生成变式题 -> 生成计划 -> 一题一答 -> 记录错题 -> 今日复查
```

必须满足：

- `开始复习` 后 Codex 能先问问题，而不是先总结。
- 至少一门真实课程跑通完整闭环。
- 试卷/往年题能进入分析结果，而不是只停留在文件列表。
- 变式题能被一题一答会话直接使用。
- 计划能以“现在开始”进入第一道题或第一项任务。
- 错题能落盘。
- 到期项能查回。
- 进度能恢复。
- 对试卷/往年题能输出重点、题型、变式题和计划。
- 数据格式简单、可读、可脚本处理。

最小演示脚本序列：

```text
python3 scripts/init_course_review.py "../计算机网络"
python3 scripts/analyze_exam.py "../计算机网络"
python3 scripts/generate_questions.py "../计算机网络" --count 5
python3 scripts/plan_review.py "../计算机网络" --minutes 90 --goal pass
python3 scripts/review_session.py "../计算机网络" --source generated
python3 scripts/due_today.py ..
```

这组命令能跑通，才算 MVP 可以进入前端开发。

## 当前最该做的下一步

马上做：

```text
scripts/init_course_review.py
scripts/analyze_exam.py
scripts/generate_questions.py
scripts/plan_review.py
scripts/review_session.py
scripts/review_log.py
scripts/due_today.py
```

理由：

- 数据契约和问题模板已经补齐。
- 下一步应该让一门真实课程能生成 `review/` 工作区，并进入试卷分析、出题、规划、一题一答、错题复查的 CLI 闭环。

## 下一轮开发 Sprint

目标：把“大学生期末需求调研”真正变成能跑的 CLI 链路。

### Sprint A：真实课程初始化

任务：

1. 对 `../计算机网络` 运行 `scripts/init_course_review.py`。
2. 检查 `计算机网络/review/files.yaml` 的文件分类是否合理。
3. 检查 `progress.md` 是否能指导下一步。
4. 如果分类不准，改进 `guess_material_type()`。

验收：

- `计算机网络/review/` 下 8 个标准文件存在。
- 原始课件目录不被移动、不被覆盖。
- 重复运行 `init_course_review.py` 时全部跳过已有文件。

提交建议：

```text
test: initialize real computer network review workspace
```

### Sprint B：试卷分析脚本雏形

新增：

```text
scripts/analyze_exam.py
```

第一版不要追求完美 PDF/PPT 解析，先做确定性能力：

- 读取 `review/files.yaml`。
- 找出 `past_exam`、`mock_exam`、`homework_answer`、`teacher_focus`。
- 根据文件类型和文件名生成初始优先级。
- 输出 `review/exam-analysis.yaml`。
- 输出 `review/past-exam-patterns.yaml` 的空壳或基础 pattern。

验收：

- 对 `计算机网络/review/files.yaml` 能生成非空 `exam-analysis.yaml`。
- 分析结果明确标注 evidence。
- 低置信度时不装作精准分析。

输出示例：

```text
高频来源：样题、往年题、作业答案
优先章节：Transport / Network
建议动作：先做协议流程题，再做计算题
置信度：low / medium / high
```

提交建议：

```text
feat: add initial exam analysis script
```

### Sprint C：变式题生成雏形

新增：

```text
scripts/generate_questions.py
```

第一版能力：

- 读取 `past-exam-patterns.yaml` 或 `exam-analysis.yaml`。
- 使用 `references/question_patterns.md` 中的题型模板。
- 生成 5 道 `模拟题` 或 `变式题`。
- 写入 `generated-questions.yaml`。
- 每题包含：题目、依据、评分点、建议限时。

验收：

- 生成题不声称押题。
- 每题能追溯到 pattern 或 priority。
- 题目格式能被后续 review session 使用。

提交建议：

```text
feat: generate practice variants from exam analysis
```

### Sprint D：今晚计划脚本

新增：

```text
scripts/plan_review.py
```

第一版能力：

- 读取 `progress.md`、`exam-analysis.yaml`、`cards.yaml`。
- 支持 `--minutes 30/90` 和 `--days 3/7`。
- 输出 `plan.md`。
- 计划末尾给出“现在开始”的第一步。

验收：

- 对 `计算机网络` 能生成 90 分钟保底计划。
- 计划引用本地资料或分析结果。
- 计划不是泛泛建议，而是可执行任务列表。

输出结构：

```text
目标：
依据：
先做：
后做：
可以先放弃：
最后 15 分钟：
现在开始：
```

提交建议：

```text
feat: add emergency review planning script
```

### Sprint E：一题一答会话脚本

新增：

```text
scripts/review_session.py
```

第一版能力：

- 读取 `generated-questions.yaml`、`cards.yaml` 或 `due_today.py --json` 输出。
- 一次只展示 1 道题。
- 接收用户答案。
- 根据标准答案和评分点输出 `correct | partial | wrong`。
- 对 `partial` 或 `wrong` 提供缺失要点和一个追问。
- 将需要复查的结果交给 `review_log.py`，不直接手写多个状态文件。

验收：

- 能从 5 道生成题中开始一轮会话。
- 用户答错 1 题后，错题能进入后续复查。
- 会话结束时更新 `progress.md` 的下一步建议。
- 没有题目时清楚提示先运行 `generate_questions.py` 或 `due_today.py`。

提交建议：

```text
feat: add one-question review session
```

### Sprint F：错题闭环升级

升级：

```text
scripts/review_log.py
scripts/due_today.py
```

能力：

- `review_log.py` 写入 `COURSE/review/mistake-log.md`。
- 同步追加 `cards.yaml`。
- `due_today.py` 扫描 workspace 下所有 `*/review/cards.yaml` 和 `mistake-log.md`。
- 支持 `--json`。

验收：

- 记录 1 条错题后，当天或次日能被 `due_today.py` 查到。
- 坏 YAML 不导致整个扫描崩溃。

提交建议：

```text
feat: connect mistake log to due review cards
```

## 质量指标

第一版不用复杂埋点，但每次端到端验证要人工记录这些指标：

- `time_to_first_question`: 从用户说开始复习到第一题出现的时间。
- `source_coverage`: 计划/题目引用了多少个本地资料。
- `actionability`: 输出是否包含明确“现在开始”。
- `question_quality`: 题目是否有标准答案和评分点。
- `review_recovery`: 关闭会话后能否从 `progress.md` 恢复。
- `due_recall`: 错题是否能在预定日期被查回。

验收阈值：

- 90 秒内能给出第一轮行动或明确缺什么资料。
- 每道生成题至少有 1 个来源依据或 pattern 依据。
- 每个计划必须包含第一步。
- 每条错题必须有 due。

## 风险和应对

### 风险 1：又变成总结器

表现：

- 输出很长。
- 没有问题。
- 没有评分点。

应对：

- `SKILL.md` 已规定 active recall before explanation。
- `question_patterns.md` 必须被出题脚本使用。
- 计划输出必须以“现在开始”结尾。

### 风险 2：试卷分析像押题

表现：

- 说“今年一定考”。
- 生成题像原题复刻。

应对：

- 只说高频、优先级、变式。
- 标记 `模拟题` / `变式题`。
- 每条建议都标 evidence 和 confidence。

### 风险 3：文件解析陷入泥潭

表现：

- 花大量时间处理 PPT/PDF 文本抽取。
- CLI 迟迟跑不通。

应对：

- 第一版先用文件名、文件类型、人工可见资料和轻量文本。
- 先让 YAML/Markdown 闭环跑起来。
- 精细解析放到 P2。

### 风险 4：前端太早

表现：

- 页面很好看，但没有真实数据。
- 数据格式频繁变。

应对：

- v0.2 先做 CLI。
- v0.4 再做 API。
- v0.5 才做 React。

### 风险 5：错题没有复查

表现：

- 错题只写日志，不进入 due。

应对：

- `review_log.py` 必须同步写 `cards.yaml`。
- `due_today.py` 必须扫描所有课程 review。
- 完成定义里保留 due 验收。

## 开发顺序原则

1. 先 CLI，后 API，最后前端。
2. 先确定性脚本，后 agent 自由生成。
3. 先跑通一门课，后抽象成多课程。
4. 先保底计划和变式题，后完整笔记。
5. 每个脚本都必须重复运行安全，不覆盖用户资料。

## 商业化路线图（顶层索引）

详细产品定义见 `PRODUCT_ARCHITECTURE.md`；SaaS 技术方案见 `FULLSTACK_AGENT_ARCHITECTURE.md` § SaaS；任务预览见 `tasks.md` Phase 3–4。

```text
v0.2  CLI MVP 闭环     ← 当前焦点（55 任务）
v0.3  Agent API
v0.4  FastAPI 后端
v0.5  React 工具前端   ← references/product_mvp.md 功能边界
v1.0  可用期末复习产品（无账号，3 门课跑通）
v1.5  商业化（账号、支付、对话、付费墙）
v2.0  SaaS 上线（多租户、校园、运营后台）
```

| 版本 | 里程碑（3–5 条） | 启动条件 |
|------|------------------|----------|
| **v1.0** | ① Web 完成上传→分析→计划→练习→错题闭环 ② 3 门真实课程验证 ③ 打开到第一题 ≤2 分钟 ④ 用户无需 CLI | v0.5 页面可用 |
| **v1.5** | ① 邮箱注册登录 ② 订阅支付打通 ③ 对话页 + 固定按钮双模式 ④ 免费层 + 冲刺包 SKU ⑤ 付费墙在分析/计划触发 | v1.0 验收通过 |
| **v2.0** | ① 多租户 workspace ② 校园套餐/机构码 ③ 运营后台 ④ 生产监控与合规 ⑤ 99.5% 可用性目标 | v1.5 付费转化验证 |

**现在不做**：v1.0 之前不接 OAuth/支付；`SKILL.md` 不写账号逻辑；商业化细节不写入 `references/product_mvp.md`。

---

## 不变量

无论后续怎么改，以下规则不能变：

1. 课程事实只来自本地资料，除非用户明确解除限制。
2. 先问问题，再讲解。
3. 往年题用于分析题型和生成变式，不用于押题承诺。
4. 计划必须落到行动。
5. 错题必须能复查。
6. `SKILL.md` 保持短，细节放 `references/`。
7. 脚本必须重复运行安全。
