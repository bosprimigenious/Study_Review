# 文档体系与维护规则

最后更新：2026-06-27

## 目标

这个文档体系解决三个问题：

1. Codex 运行时只读必要规则，不被长规划拖慢。
2. 人类维护者能快速找到路线图、架构、开发和运维资料。
3. 每次迭代都有明确的文档落点，避免 README、PLAN、tasks 多头更新。

## 信息架构

```text
study-review-skill/
├── README.md                         # 项目入口：安装、运行、文档导航
├── SKILL.md                          # Codex 运行时入口：短契约
├── docs/
│   ├── README.md                     # 人类维护文档入口
│   ├── UPDATE_AND_ITERATION_PLAN.md  # 当前唯一迭代计划入口
│   ├── DOCUMENTATION_SYSTEM.md       # 本文档：文档治理
│   ├── architecture/                 # 架构索引和设计决策
│   ├── development/                  # 开发流程、测试、贡献规范
│   ├── operations/                   # 运行、发布、排障、真实课验收
│   ├── product/                      # 产品、用户、商业化
│   ├── reference/                    # references/ 的人类导航
│   └── templates/                    # 复用模板
├── references/                       # Codex 按需加载的运行时细则
├── examples/                         # 稳定样例数据
├── tests/                            # 测试代码和验收结果
└── scripts/ocr/README.md             # OCR 工具专项说明
```

## 文档职责

| 文档类型 | 放哪里 | 写什么 | 不写什么 |
| --- | --- | --- | --- |
| 项目入口 | `README.md` | 安装、快速运行、文档索引、当前状态 | 长路线图、细架构 |
| 运行时规则 | `SKILL.md` | Codex 如何调度、何时加载 references | 产品规划、长示例 |
| 当前迭代计划 | `docs/UPDATE_AND_ITERATION_PLAN.md` | 下一版本、验收、backlog | 历史长流水账 |
| 架构文档 | `docs/architecture/` | 系统边界、模块关系、技术决策 | 任务 checklist |
| 开发文档 | `docs/development/` | 本地开发、测试、编码约定 | 产品愿景 |
| 运维文档 | `docs/operations/` | 启动、排障、真实课程验收、发布 | 领域理论 |
| 产品文档 | `docs/product/` | 用户需求、MVP、商业化、体验原则 | API 字段细节 |
| 运行时参考 | `references/` | source policy、数据格式、题型模板 | 人类项目路线图 |
| 测试结果 | `tests/*_results.md` | 某次验收事实 | 未来计划 |

## 更新规则

### 每次功能改动

必须检查：

- `README.md` 是否需要新增入口。
- `docs/README.md` 是否需要新增导航。
- 对应分区 `README.md` 是否需要更新。
- `references/` 中的运行时规则是否受影响。
- `tests/*_results.md` 是否需要记录新的验收结果。

### 每次路线调整

只更新：

- `docs/UPDATE_AND_ITERATION_PLAN.md`
- 必要时更新 `tasks.md` 的状态表
- 必要时更新 `PLAN.md` 的历史路线说明

不要在多个文档写不同版本的“下一步计划”。

### 每次数据格式变更

必须同步：

- `references/data_formats.md`
- `examples/`
- 对应脚本或 API 测试
- 如影响用户迁移，新增 `docs/operations/` 迁移说明

### 每次 agent 行为变更

必须同步：

- `SKILL.md` 中的短规则
- 相关 `references/*.md`
- `scripts/agent/` 测试或 eval

## 命名约定

- 文档文件名使用 `UPPER_SNAKE_CASE.md` 表示重要入口，如 `UPDATE_AND_ITERATION_PLAN.md`。
- 分区索引用 `README.md`。
- 模板放入 `docs/templates/`，使用小写短横线命名。
- 验收结果放入 `tests/`，命名为 `*_results.md` 或 `*_validation.md`。

## Staleness 规则

每篇长期文档顶部保留：

```text
最后更新：YYYY-MM-DD
```

文档出现以下情况应标注为历史文档或合并：

- 当前状态和代码明显不一致。
- 只描述已完成实现，且没有维护价值。
- 与 `docs/UPDATE_AND_ITERATION_PLAN.md` 给出冲突路线。

历史文档不直接删除，除非确认没有链接和决策价值。优先在索引中标注“历史参考”。

## 文档审查清单

提交前检查：

- 链接是否相对路径可打开。
- 是否把运行时规则误放进产品文档。
- 是否把未来规划误放进测试结果。
- 是否出现多个互相冲突的 roadmap。
- 是否说明了功能如何验收。
- 是否保留本地资料为课程事实来源的原则。
