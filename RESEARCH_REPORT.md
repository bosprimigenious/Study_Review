# 复习类 Agent Skill 调研报告

调研时间：2026-06-09  
目标：寻找 GitHub/开源生态中已有的学习、复习、题卡、间隔重复、`SKILL.md` 仓库设计，提炼可用于 `study-review` 的架构和产品思路。

## 结论先行

目前没有看到一个已经成熟、专门面向“中国大学期末复习资料文件夹”的 Codex/OpenAI `study-review` skill。市面上的相关项目大致分为三类：

1. **Agent Skill 结构范例**：告诉我们 skill 仓库应该怎么组织，如 OpenAI 官方 skills catalog。
2. **学习型 Skill / Tutor**：强调苏格拉底提问、主动回忆、学习日志、间隔重复，如 `learn-codebase` 和 Claude `/learn`。
3. **学习包 / 题卡生成工具**：从 PDF、网页、视频生成学习资料、quiz、flashcards，并可导出为 agent skill，如 `Skill-Anything` 和 NotebookLM 相关工具。

对我们的 `study-review` 来说，最佳方向不是做一个大而全的“总结器”，而是做成：

> 本地课件资料索引 + 主动回忆问答 + 题卡/错题产物 + 轻量间隔重复调度。

也就是：先问你，再讲；先记录薄弱点，再安排复查。

## 搜索范围

重点搜索关键词包括：

- `SKILL.md study review flashcards`
- `Codex skill study review`
- `Claude Code learn skill spaced repetition`
- `AI study assistant flashcards spaced repetition`
- `Obsidian spaced repetition AI flashcards`
- `FSRS Anki scheduler GitHub`

重点参考项目：

- [openai/skills](https://github.com/openai/skills)
- [ktaletsk/learn-codebase](https://github.com/ktaletsk/learn-codebase)
- [SYuan03/Skill-Anything](https://github.com/SYuan03/Skill-Anything)
- [teng-lin/notebooklm-py](https://github.com/teng-lin/notebooklm-py/blob/main/SKILL.md)
- [chr1stophe Claude /learn skill gist](https://gist.github.com/chr1stophe/22c62c92a0129a5f8f0c72263e3674ea)
- [open-spaced-repetition/fsrs4anki](https://github.com/open-spaced-repetition/fsrs4anki)
- [open-spaced-repetition/py-fsrs](https://github.com/open-spaced-repetition/py-fsrs)
- [st3v3nmw/obsidian-spaced-repetition](https://github.com/st3v3nmw/obsidian-spaced-repetition)
- [ai-learning-tools/obsidian-spaced-repetition-ai](https://github.com/ai-learning-tools/obsidian-spaced-repetition-ai)

## 项目观察

### 1. OpenAI 官方 Skills Catalog

仓库：[openai/skills](https://github.com/openai/skills)

官方 catalog 把 skill 定义为可被 agent 发现和复用的文件夹，通常包含：

- `SKILL.md`
- `references/`
- `scripts/`
- `assets/`
- 可选 `agents/openai.yaml`

可借鉴点：

- `SKILL.md` 要短而有决策力，不要把所有细节塞进去。
- 详细规则放到 `references/`，需要时再加载。
- 稳定、重复、容易出错的操作放到 `scripts/`。
- skill 的价值在于“重复工作流可靠化”，不是把 README 写得很长。

对我们的影响：

- 当前 `study-review` 的 `SKILL.md` 应保留核心行为：主动回忆、模式选择、产物规则。
- 学科细节、题卡质量、错题记录格式应拆到 `references/`。
- 资料扫描、错题追加、到期复习适合脚本化。

### 2. learn-codebase：最接近“导师型 skill”的参考

仓库：[ktaletsk/learn-codebase](https://github.com/ktaletsk/learn-codebase)

这个项目虽然目标是学习代码库，不是考试复习，但方法论非常接近。它强调：

- Socratic questioning：先让学习者解释。
- Prediction before revelation：先预测，再揭示。
- Active recall：主动回忆。
- Spaced repetition：间隔重复。
- Persistent learning journal：持久学习日志。
- Zone of Proximal Development：根据学习者水平调难度。

它的文件结构很轻：

```text
learn-codebase/
├── SKILL.md
├── JOURNAL-TEMPLATE.md
├── QUESTION-PATTERNS.md
├── README.md
└── LICENSE
```

可借鉴点：

- 不急着“讲课”，先用问题定位理解程度。
- 维护学习日志，而不是每次从零开始。
- 问题模式独立成 reference，方便扩展。
- 贡献方向围绕真实使用中的 question patterns 和 edge cases。

对我们的影响：

- `study-review` 应该有 `question_patterns.md`，专门沉淀不同题型的提问模板。
- 错题本不只是记录错题，还要记录“错误类型”和“下次怎么问”。
- 每轮复习要有难度校准：薄弱、可做题、冲刺。

### 3. Claude /learn gist：学习轨道和进度文件设计

链接：[Claude /learn skill gist](https://gist.github.com/chr1stophe/22c62c92a0129a5f8f0c72263e3674ea)

这个 gist 的亮点是“learning track”概念。它不是单次问答，而是把每个主题建成一个可恢复的学习轨道：

```text
personal/learning/{topic-slug}/
└── progress.md
```

它有几种路由：

- 无参数：列出已有学习轨道。
- 参数命中已有 topic：恢复学习。
- 参数是新 topic：创建新学习轨道。

可借鉴点：

- “今天复习什么”可以通过扫描 `progress.md` 或 `复习记录.md` 自动回答。
- 每门课可以有自己的 `review/progress.md`。
- 学习状态应包含：当前阶段、完成度、上次复习日期、下一步。

对我们的影响：

- 比单个 `复习记录.md` 更好的长期结构是：

```text
科目/review/
├── progress.md
├── mistake-log.md
├── cards.yaml
└── due.md
```

- 如果后续升级，`due_today.py` 应扫描每个科目的 `review/progress.md` 和 `mistake-log.md`。

### 4. Skill-Anything：从资料生成完整学习包

仓库：[SYuan03/Skill-Anything](https://github.com/SYuan03/Skill-Anything)

这是最接近“资料到学习包”的项目。它可以从 PDF、视频、网页、文本等来源生成学习包，并支持导出为 agent skill。

它的输出思路很完整：

```text
output/
├── my-skill.yaml
├── my-skill.md
└── my-skill-concept-map.png
```

导出为 agent skill 时：

```text
output/my-skill/
├── SKILL.md
├── references/
├── assets/
└── scripts/
```

它的学习包包含 12 类内容：

- summary
- concept map
- outline
- detailed notes
- key concepts
- glossary
- cheat sheet
- takeaways
- quiz
- flashcards
- exercises
- learning path

可借鉴点：

- 区分 `study pack` 和 `agent skill`：前者给人读，后者给 agent 用。
- 结构化 YAML 是后续 quiz/review 的好基础。
- Quiz 和 flashcards 可以放到 `assets/`，不一定都塞进 Markdown。
- 学习资料生成应分层：提纲、术语、题卡、练习、学习路径。

对我们的影响：

- `study-review` 不应该只维护 Markdown。后续可以加入：

```text
科目/review/
├── pack.yaml
├── outline.md
├── glossary.md
├── quiz.yaml
├── flashcards.yaml
└── exercises.md
```

- `SKILL.md` 负责复习行为，`pack.yaml` 负责可复用数据。

### 5. NotebookLM skill：工具型 skill 的工程化程度

仓库文件：[notebooklm-py/SKILL.md](https://github.com/teng-lin/notebooklm-py/blob/main/SKILL.md)

NotebookLM 这个 skill 不是复习 skill，但它覆盖了“从资料生成 study guide、quiz、flashcards”的功能，并且工程化程度很强。

值得借鉴的地方：

- 明确激活条件。
- 明确安装方式。
- 明确哪些命令可靠、哪些命令可能因为 rate limit 失败。
- 明确长任务的等待、重试、降级策略。
- 明确可导出格式：JSON、Markdown、HTML。

对我们的影响：

- 如果未来接入外部工具或 LLM API，必须写清楚失败模式。
- 题卡导出不应只支持 Markdown，至少应考虑 JSON/YAML。
- 本地脚本应有清晰 CLI，例如：

```bash
python scripts/inventory.py .
python scripts/review_log.py --subject 计算机网络 ...
python scripts/due_today.py
```

### 6. Open spaced repetition / Anki / Obsidian 生态

参考：

- [open-spaced-repetition/fsrs4anki](https://github.com/open-spaced-repetition/fsrs4anki)
- [open-spaced-repetition/py-fsrs](https://github.com/open-spaced-repetition/py-fsrs)
- [st3v3nmw/obsidian-spaced-repetition](https://github.com/st3v3nmw/obsidian-spaced-repetition)
- [ai-learning-tools/obsidian-spaced-repetition-ai](https://github.com/ai-learning-tools/obsidian-spaced-repetition-ai)

这些项目说明：复习系统的成熟形态通常包含三层：

1. **卡片格式**：题干、答案、标签、难度、来源。
2. **复习记录**：上次复习时间、评分、下次复习时间。
3. **调度算法**：SM-2、FSRS 或简化间隔。

可借鉴点：

- 评分最好是少量档位，而不是自由文本。
- 常见档位：Again/Hard/Good/Easy；中文可以映射为 `忘了/困难/还行/很熟`。
- 卡片需要 tags，否则以后很难按科目、章节、错因筛选。
- 初版不必直接上 FSRS，可以先用 D+1/D+3/D+7。

对我们的影响：

- 当前 `study-review` 的轻量调度是对的，但数据格式应为未来 FSRS 留口子。
- 推荐 `cards.yaml` 设计：

```yaml
cards:
  - id: cn-tcp-001
    subject: 计算机网络
    chapter: 传输层
    topic: TCP
    prompt: TCP 拥塞控制和流量控制的区别是什么？
    answer: 拥塞控制面向网络整体负载；流量控制面向接收端处理能力。
    difficulty: medium
    tags: [计算机网络, TCP, 易混]
    source: 6-Transport.pptx
    schedule:
      rating: 困难
      last_reviewed: 2026-06-09
      due: 2026-06-10
```

## 对当前仓库的评价

当前 `study-review-skill` 已经有一个合理的第一版结构：

```text
study-review-skill/
├── SKILL.md
├── DESIGN.md
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

这个结构符合 OpenAI skills 的基本范式：核心说明 + progressive disclosure + 小脚本。

但和上面优秀项目相比，还缺几块：

1. **缺 question patterns**
   现在有复习模式，但没有专门沉淀“怎么出好题”的模板库。

2. **缺结构化卡片数据**
   现在题卡格式主要写在 Markdown 里，后续应加 `cards.yaml` 示例和 schema。

3. **缺 progress track**
   目前是错题日志思路，还没有“每门课当前复习到哪里”的进度文件。

4. **缺安装/使用说明**
   虽然用户当前没有要求 README，但如果要做成 GitHub 仓库，至少需要一个极简 README。

5. **脚本还偏轻**
   `due_today.py` 目前只读简单 Markdown checklist。未来应支持 YAML 卡片和多个课程目录。

## 推荐升级架构

建议把仓库升级为：

```text
study-review-skill/
├── SKILL.md
├── DESIGN.md
├── RESEARCH_REPORT.md
├── README.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── modes.md
│   ├── subject_profiles.md
│   ├── question_patterns.md
│   ├── card_quality.md
│   ├── data_formats.md
│   └── artifacts.md
├── scripts/
│   ├── inventory.py
│   ├── init_course_review.py
│   ├── review_log.py
│   ├── due_today.py
│   └── export_anki.py
├── schemas/
│   ├── cards.schema.json
│   └── progress.schema.json
└── examples/
    ├── sample_session.md
    ├── sample_cards.yaml
    └── sample_progress.md
```

## 推荐数据格式

### progress.md

适合人类快速阅读。

```markdown
# 计算机网络复习进度

## 当前状态
- 阶段：诊断后补弱
- 最近复习：2026-06-09
- 当前最弱：TCP 拥塞控制、子网划分
- 下一步：传输层 10 题抽查

## 章节进度
- [x] Introduction
- [x] Physical
- [ ] Datalink
- [ ] Network
- [ ] Transport
- [ ] Application

## 最近错因
- 概念混淆：拥塞控制 vs 流量控制
- 流程不完整：三次握手只会背包名，不会解释原因
```

### cards.yaml

适合脚本处理。

```yaml
cards:
  - id: net-tcp-001
    subject: 计算机网络
    topic: TCP
    type: contrast
    prompt: TCP 拥塞控制和流量控制的区别是什么？
    answer: 拥塞控制面向网络整体负载；流量控制面向接收端处理能力。
    tags:
      - 计算机网络
      - 传输层
      - 易混
    source: 6-Transport(3).pptx
    difficulty: medium
    schedule:
      rating: 困难
      last_reviewed: 2026-06-09
      due: 2026-06-10
```

### mistake-log.md

适合回看错因。

```markdown
## 2026-06-09 - 计算机网络

### 知识点
- TCP 拥塞控制 vs 流量控制

### 原题/问题
拥塞控制和流量控制区别是什么？

### 我的错误
只说了“都是控制速度”，没有说清楚控制对象。

### 正确理解
拥塞控制防止网络过载，流量控制防止接收方被发送方压垮。

### 下次复查
- [ ] 2026-06-10
- [ ] 2026-06-12
- [ ] 2026-06-16
```

## 产品策略建议

### 第一阶段：把 skill 做稳

目标：真正好用，而不是功能多。

优先级：

1. 补 `question_patterns.md`。
2. 补 `data_formats.md`。
3. 补 `sample_cards.yaml`。
4. 让 `due_today.py` 能扫描多个课程目录。
5. 让 `review_log.py` 同时写 Markdown 和 YAML。

### 第二阶段：让它能生成复习包

目标：从课件目录生成 `review/`。

命令设想：

```bash
python scripts/init_course_review.py "../计算机网络"
```

输出：

```text
计算机网络/review/
├── progress.md
├── outline.md
├── cards.yaml
├── mistake-log.md
└── due.md
```

### 第三阶段：接入更强调度

目标：从 D+1/D+3/D+7 升级到 FSRS。

选择：

- 使用 [py-fsrs](https://github.com/open-spaced-repetition/py-fsrs)
- 或保持无依赖，实现简化 SM-2

建议先别上复杂调度。期末复习场景常常是短周期冲刺，过度精细的长期记忆模型收益不一定高。

## 最重要的设计原则

1. **主动回忆优先**
   不要一上来总结。先问，答错再讲。

2. **题卡必须原子化**
   一张卡只考一个点，答案必须可判定。

3. **按科目改变策略**
   毛概、概率论、计网、计组、理论计算机不能用同一套问法。

4. **保留复习状态**
   好的复习工具不是生成一次材料，而是知道你上次哪里错了。

5. **Markdown 给人看，YAML 给脚本跑**
   两者都需要。

6. **脚本只做确定性工作**
   扫描文件、写日志、查到期项、导出卡片适合脚本；判断讲解质量交给 agent。

## 对 `study-review` 的具体下一步

建议马上补这 4 个文件：

```text
references/question_patterns.md
references/data_formats.md
examples/sample_cards.yaml
examples/sample_progress.md
```

然后升级这 2 个脚本：

```text
scripts/due_today.py
scripts/review_log.py
```

升级目标：

- 支持扫描 `*/review/mistake-log.md`
- 支持读取 `*/review/cards.yaml`
- 支持输出今天该复习的科目、知识点、题卡数量
- 支持把一次错题同步写入 Markdown 和 YAML

## 最终建议

`study-review` 应该走一条比较克制但很实用的路线：

- 不做大型知识库。
- 不追求一次性完美提取 PPT/PDF。
- 不复制 Anki。
- 先成为一个“会追问、会记错题、会提醒复查”的考试搭子。

这个定位和现有开源项目相比有明显差异：它不是通用学习平台，而是 **Codex 内的本地课程复习工作流 skill**。这正好适合当前目录里这种按课程堆放的 PPT/PDF 期末资料。
