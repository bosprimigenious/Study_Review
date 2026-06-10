# Study Review 任务清单

**v0.2 状态：✅ 完成（2026-06-10）**

制定时间：2026-06-10 · 最后加深：2026-06-10
依据：`PLAN.md`、`references/agent_development_plan.md`、`references/data_formats.md`、`references/orchestrator.md`、`references/question_patterns.md`

---

## 技术决策前置（实现任何 Epic 前必读）

以下 6 项跨模块决策影响所有脚本，Epic 0 实现时必须先定，后续不改。

### TD-1 YAML 库：PyYAML，但防类型强制

**决策**：`pip install pyyaml`，使用 `yaml.safe_load` / `yaml.safe_dump`。不上 ruamel.yaml。

**原因**：MVP 文件体积 < 500 行，不需要保留注释和手工排版。ruamel.yaml 的 round-trip 能力在题卡数 > 200 后再评估。

**强制规则**：
- 所有 `yaml.safe_dump` 必须传 `allow_unicode=True, default_flow_style=False, sort_keys=False`
- 所有 YAML 字符串值在写入前必须检查是否为 Python `bool` 类型 —— YAML 1.1 会把 `yes`/`no`/`on`/`off`/`true`/`false` 强制转为布尔
- 在 `review_io.py` 中封装 `yaml_safe_dump(data, path)` 统一出口，内部处理 bool→str 转换

**陷阱示例**：
```yaml
# 错误：topic 字段变成布尔值
topic: no
# 写入后变成：
topic: false

# 正确：始终加引号
topic: "no"
```

### TD-2 原子写入：tempfile + os.replace

**决策**：所有写 YAML/Markdown 的操作必须原子化。不允许直接 `open(path, "w")`。

**实现**（封装在 `review_io.py`）：
```python
import tempfile, os

def atomic_write(path: Path, content: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix="." + path.name + ".", suffix=".tmp")
    try:
        os.write(fd, content.encode("utf-8"))
    finally:
        os.close(fd)
    os.replace(tmp, path)  # 原子替换，在 NTFS 上也安全
```

**原因**：`cards.yaml` 和 `progress.md` 是用户长期积累的数据。脚本崩溃时不能丢失，也不能留下半截文件。

**注意**：`os.replace` 在 Windows 上要求 `tmp` 和 `path` 在同一卷。`tempfile.mkstemp(dir=path.parent)` 满足此条件。

### TD-3 Windows 路径与编码

**决策**：
- 所有内部文件（YAML / Markdown）统一 `encoding="utf-8"`
- `pathlib.Path` 操作全部用 `/` 分隔符（Python 3.6+ 在 Windows 上自动转换）
- `files.yaml` 中的 `path` 字段存 Unix 风格相对路径（`计算机网络/6-Transport.pptx`），不存 `\`
- 读取用户传入的 `sys.argv` 课程路径时，用 `Path().resolve()` 规范化

**已知坑**：
- git on Windows 可能配置 `core.autocrlf=true`，导致 YAML 文件换行符被改成 `\r\n`。在 `atomic_write` 中统一写 `\n`
- 中文文件名在 `cmd.exe` 和 `bash` 下传给 Python 的编码可能不同。`argparse` 在 3.8+ 已处理，但脚本仍应 print 路径确认

### TD-4 ID 生成的 slugify 必须避免空洞

**当前问题**：`init_course_review.py` 中的 `slugify("计算机网络")` → `""`（全部中文被 strip），fallback 为 `"course"`。这意味着两门纯中文课程会产生相同 `course_id`。

**决策**：在 `review_io.py` 中实现 `make_course_id(name: str) -> str`：
```python
def make_course_id(name: str) -> str:
    # 1. 尝试保留 ASCII 部分
    ascii_part = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    # 2. 如果 ASCII 部分为空，用拼音首字母 + crc32 后缀
    if not ascii_part:
        import zlib
        suffix = format(zlib.crc32(name.encode("utf-8")) & 0xFFFFFFFF, "08x")[:4]
        ascii_part = f"course-{suffix}"
    return ascii_part
```

**验收**：`计算机网络` 和 `计算机组成原理` 必须产生不同 course_id。

### TD-5 Schema 版本号

**决策**：每个 YAML 文件的第一行/第一个顶层键必须是 `schema_version`。

```
files.yaml            → schema_version: 1
cards.yaml            → schema_version: 1
exam-analysis.yaml    → schema_version: 1
past-exam-patterns.yaml → schema_version: 1
generated-questions.yaml → schema_version: 1
```

**原因**：v0.3 做 Agent 编排时几乎必然要改字段。没有 version，旧数据迁移只能靠猜。成本极低（一行），收益极高（向前兼容）。

**注意**：`progress.md`、`mistake-log.md`、`plan.md` 是给人读的 Markdown，不需要 version。

### TD-6 subprocess 调用的序列化边界

**决策**：当 `review_session.py` 调用 `review_log.py` 时，复杂参数（含中文、换行、特殊字符）**必须通过临时 JSON 文件传递**，禁止用 `sys.argv` 拼接多行文本。

```python
# 正确的跨进程调用方式
import tempfile, json, subprocess
tmp = Path(tempfile.mktemp(suffix=".json", dir=review_dir))
tmp.write_text(json.dumps({"prompt": "...", "answer": "...", ...}), encoding="utf-8")
subprocess.run([sys.executable, "scripts/review_log.py", "--course", str(course), "--json", "--input", str(tmp)])
tmp.unlink()
```

**原因**：用户答案可能包含换行、引号、特殊字符。shell escaping 在不同平台和 shell 下行为不一致，且可能触发 command injection。

---

## 任务分层

| 层级 | 任务数 | 含义 | 完成标志 |
|------|--------|------|----------|
| **MVP** | **55** | CLI 最小闭环 + E2E 验收 | 6 步命令链跑通，错题能复查 |
| **v0.2 完整** | **12** | 测试 + 文档 + init 打磨 | `unittest` 全绿，README 更新 |
| **可选** | **1** | 真实课程复验 | 有本地计网目录时执行 |
| **合计** | **68** | | |

**从当前 CLI 到 MVP**：55 个任务（`init_course_review.py` 已有，但任务条目不勾，4-03 fixture 仍要做）。

---

## MVP 是什么

做完 **55 个 MVP 任务**后，你可以：

```bash
python scripts/init_course_review.py "tests/fixtures/computer-network"
python scripts/analyze_exam.py "tests/fixtures/computer-network"
python scripts/generate_questions.py "tests/fixtures/computer-network" --count 5
python scripts/plan_review.py "tests/fixtures/computer-network" --minutes 90 --goal pass
python scripts/review_session.py "tests/fixtures/computer-network" --source generated
python scripts/due_today.py tests/fixtures
```

并得到：

- 每门课有完整 `review/` 工作区（8 个标准文件）
- 试卷/样题分析 → priorities + evidence
- 5 道变式题（有 scoring_points、来源）
- 90 分钟救火计划（含「现在开始」）
- 一题一答 + 规则判分
- 错题写入 `mistake-log.md` + `cards.yaml`，`due_today` 可查回

**MVP 不包含**：单元测试套件、README 大改、`init --json` 打磨、真实计网目录、前端、API、Agent 编排。

---

## 全局约束（所有脚本必须遵守）

1. **不覆盖用户数据**：默认 `write_if_missing`；覆盖需显式 `--force`。
2. **只写 `review/`**：原始课件目录只读，不移动、不修改。
3. **课程事实来自本地**：脚本不联网、不读 workspace 外路径、不编造考点。
4. **L2 = `--json`**：P0 脚本（除 `review_session` MVP 阶段）stdout 支持 JSON；stderr 用于人类日志和 warning。
5. **ID 规则**：见 `data_formats.md` § ID Rules + TD-4 slugify 实现。
6. **日期格式**：ISO `YYYY-MM-DD`。
7. **原子写入**：所有 YAML/Markdown 写操作走 `review_io.atomic_write`（TD-2）。
8. **YAML 安全**：所有 YAML 写操作走 `review_io.yaml_safe_dump`（TD-1）。
9. **UTF-8**：所有文件读写统一 `encoding="utf-8"`，换行符统一 `\n`（TD-3）。

---

## 进度总览

### MVP（55）

| Epic | MVP 任务 | 完成 | 状态 |
|------|----------|------|------|
| Epic 0 公共 IO | 8 | 8/8 | 已完成 |
| Epic 1 错题闭环 | 14 | 14/14 | 已完成 |
| Epic 2 分析 + 出题 | 15 | 15/15 | 已完成 |
| Epic 3 计划 + 会话 | 11 | 11/11 | 已完成 |
| Epic 4 fixture（仅 4-03） | 1 | 1/1 | 已完成 |
| Epic 6 E2E（6-01~6-06） | 6 | 6/6 | 已完成 |
| **MVP 合计** | **55** | **55/55** | **已完成** |

### v0.2 完整交付（+12）

| Epic | 任务 | 完成 | 状态 |
|------|------|------|------|
| Epic 4 init 打磨（4-01, 4-02） | 2 | 2/2 | 已完成 |
| Epic 5 单元测试 | 7 | 7/7 | 已完成 |
| Epic 7 文档 | 3 | 3/3 | 已完成 |
| **v0.2 合计** | **12** | **12/12** | **已完成** |

---

## MVP 验收清单（对照 PLAN.md）

- [x] **M1** 一门课（fixture）能生成 `review/` 工作区
- [x] **M2** 至少 1 份样题/往年题进入 `exam-analysis.yaml`
- [x] **M3** 至少 5 道带标准答案、评分点、来源的变式题
- [x] **M4** 至少 1 份 90 分钟保底计划
- [x] **M5** 用户能答 1 题并得到 `correct|partial|wrong` 判定
- [x] **M6** 至少 1 条错题写入 `mistake-log.md` 和 `cards.yaml`
- [x] **M7** `due_today.py` 当天或次日能查回该错题
- [x] **M8** 课程事实只来自本地资料 / 分析文件
- [x] **M9** 计划以「现在开始」进入第一项任务
- [x] **M10** 重复运行不覆盖用户已有 review 文件

---

## MVP 定量验收指标（Q1–Q12）

以下 12 项在 E2E 跑通时必须实测记录。**未达阈值的项不能宣称 MVP 完成。**

| # | 指标 | 阈值 | 测量方式 | 所属 Epic |
|---|------|------|----------|-----------|
| Q1 | `init_course_review` 执行耗时 | ≤2s | `time python scripts/init_course_review.py ...` | E4 |
| Q2 | `analyze_exam` 执行耗时 | ≤3s | 同上（纯规则匹配，不调 LLM） | E2 |
| Q3 | `generate_questions` 5 题耗时 | ≤5s | 同上（模板填充，不含 LLM） | E2 |
| Q4 | `plan_review` 90 分钟计划耗时 | ≤3s | 同上 | E3 |
| Q5 | time-to-first-question（用户端到端） | ≤90s | 从「开始复习」→ `plan.md` 出现 → session 第 1 题打印 | E6 |
| Q6 | 规则判分准确率（vs 人工标注） | ≥70% | 20 题 fixture，人工标注 verdict → 脚本判分对比 | E3 |
| Q7 | 错题落盘延迟（答完 → due 可查） | ≤60s | session 结束到 `due_today` 可见的时间差 | E1 |
| Q8 | `due_today` 扫描 5 课程耗时 | ≤2s | 3 课正常 + 1 课坏 YAML + 1 课空 | E1 |
| Q9 | 生成题评分点覆盖率 | 100% | 5 道生成题，每题 ≥2 个 scoring_points | E2 |
| Q10 | evidence 追溯率 | 100% | 每条 priority 的 evidence[] 非空且指向 fixture 内文件名 | E2 |
| Q11 | ID 唯一性（跨 3 次运行无碰撞） | 100% | 连跑 3 次 generate_questions，所有 id 无重复 | E0 |
| Q12 | 坏 YAML 容错率 | 100% | 5 课中坏 1 课 → `due_today` 仍返回其余 4 课结果 | E1 |

### Q6 判分准确率专项设计

在 fixture 上准备 **20 道计网题**，覆盖 5 种 verdict 分布：
- 8 题预期 `correct`（答案覆盖 ≥80% 评分点关键词）
- 6 题预期 `partial`（覆盖 40–79%）
- 6 题预期 `wrong`（覆盖 <40% 或完全答偏）

人工逐题标注 verdict 后，跑 `review_session --non-interactive --answer "预编答案"`。对比命中率。

**≥70% 通过**。70% 而非 90% 的原因：规则判分不处理同义词（"拥塞控制" vs "阻塞控制"）、语序颠倒、英文等价表达。这是 MVP 阶段**刻意接受的精度上限**，v0.3 接 LLM 后目标提升至 ≥90%。

### 各 Epic 执行耗时预算

MVP 全部脚本**不调 LLM API**，总链耗时预算：

```
init (2s) → analyze (3s) → generate (5s) → plan (3s) → session (交互，不计) → due (2s)
─────────────────────────────────────────────────────────
  非交互链路总耗时 ≤ 15s
```

---

## Epic 0：公共模块 `scripts/review_io.py` `[MVP 8/8]`

**Epic 目标**：5 个脚本共用一套 IO，避免 YAML/路径/ID/日期逻辑复制粘贴。
**Epic 验收**：`review_log`、`due_today`、`analyze_exam`、`generate_questions`、`plan_review`、`review_session` 均 `import review_io`。

**Epic 级技术决策**：
- 所有 `review_io` 函数签名用 `pathlib.Path`，不接受 `str` 路径参数
- 模块启动时不做任何文件 IO（lazy init），避免 import 副作用
- `review_io` 自身不 import 其他项目脚本，形成单向依赖：`review_io ← 各脚本`

---

- [x] **0-01** `MVP` 安全读取 YAML

  - **目标**：统一入口，坏文件不 silent fail，空文件有约定行为。
  - **验收**：
    | 情况 | 行为 |
    |------|------|
    | 文件不存在 | 返回 `None`（不抛异常，让调用方决定） |
    | 文件为空（0 bytes） | 返回 `{}` |
    | YAML 语法错误 | 抛 `YamlParseError(message, path)` |
    | 正常 YAML | 返回 `dict` |
  - **输入/输出**：`Path` → `dict | None`
  - **技术决策**：
    - 使用 `yaml.safe_load`（拒绝 `yaml.load`，防止任意代码执行）
    - **不在此函数内做 YAML 1.1 bool 修正**——那是写入侧的责任（TD-1）。此函数只负责解析
    - 空文件判断用 `path.stat().st_size == 0`，不依赖 `yaml.safe_load` 返回 `None`
  - **跨任务契约**：0-08 的 4 个 loader 函数均调用此函数
  - **已知陷阱**：
    - YAML 中 `null`、`~`、空值会被 `safe_load` 解析为 Python `None`。调用方必须对缺失键做 `dict.get(key, default)` 而非 `dict[key]`
    - 空 YAML 文档（只有注释）`safe_load` 返回 `None`，与空文件的 `{}` 不同——需在函数内统一为 `{}`
  - **不做**：不做 JSON Schema 校验、不做 YAML 1.2 spec 合规检查

- [x] **0-02** `MVP` 解析 `COURSE/review/` 路径

  - **目标**：所有脚本用同一逻辑定位 `review/`。
  - **验收**：
    - `get_review_dir(course_path)` 返回 `Path` 对象
    - 输入可为相对路径 `"../计算机网络"` 或绝对路径，内部统一 `resolve()`
    - `course_path` 本身不存在时抛 `FileNotFoundError`
    - `course_path/review/` 存在 → 直接返回
    - `course_path/review/` 不存在 → 返回路径（不创建目录），调用方判断
  - **技术决策**：此函数只做路径拼接和检查，不创建目录。目录创建权留给 `init_course_review.py` 和各脚本的 `--force` 逻辑
  - **已知陷阱**：
    - 如果用户传入 `"."` 或 `"计算机网络"`，`resolve()` 后的绝对路径依赖 `cwd`。脚本应打印解析后的绝对路径供用户确认
    - 符号链接：`resolve()` 会跟随 symlink，这符合预期

- [x] **0-03** `MVP` 不覆盖写入 / YAML 列表追加

  - **目标**：「重复运行安全」不变量 + YAML 列表原子追加。
  - **验收**：
    - `write_if_missing(path, content)`: 已存在 → skip 返回 `False`；不存在 → `atomic_write` 写入返回 `True`
    - `append_yaml_list(path, key, item)`: 读取现有 YAML → 追加 `item` 到 `data[key]` 列表 → `atomic_write` 写回；文件不存在时创建 `{key: [item]}`
    - `--force` 不在此函数层处理——各脚本 CLI 自行判断后直接调 `atomic_write`
  - **技术决策**：
    - `append_yaml_list` 必须先 `load_yaml` 再 `yaml_safe_dump` 完整文件，不能做文本级追加（YAML 不是行格式）
    - 这意味着大 card 集合（>500 条）时每次追加都全量读写。MVP 阶段可接受，>1000 条时再考虑增量策略
  - **跨任务契约**：
    - 1-04（同步 cards.yaml）依赖此函数
    - 2-14（写 generated-questions.yaml）依赖此函数
  - **已知陷阱**：
    - `append_yaml_list` 会丢失文件中的 YAML 注释。这是 PyYAML 的固有限制（TD-1）。如果后续有强烈需求，切换到 ruamel.yaml
    - 读取-修改-写入之间存在 TOCTOU race condition。单用户 CLI 场景可接受；多进程并发时需加 `fcntl.lockf` / `msvcrt.locking`

- [x] **0-04** `MVP` 稳定 ID 生成

  - **目标**：card / question / pattern ID 自动生成，可读、不冲突。
  - **验收**：
    - `make_course_id(name: str) -> str` 按 TD-4 实现（pinyin fallback + crc32）
    - `next_id(prefix: str, existing_ids: set[str], topic: str = "") -> str`:
      - 格式：`{prefix}-{course_id}-{slug}-{n}`
      - `slug` = topic 的 ASCII 降级（同 slugify 逻辑，但允许数字）
      - `n` 从 1 开始递增，找到第一个未占用的
      - 同 prefix + course_id + topic 连续调用不重复
  - **输入/输出**：`(str, set[str], str)` → `str`
  - **技术决策**：
    - `existing_ids` 用 `set` 语义——调用方从 YAML 中提取现有 ID 集合传入
    - `n` 的上限不设（理论上 topic 不会超过 99 次重复）
  - **已知陷阱**：
    - 两个不同 topic 可能 slugify 成相同 ASCII（如 "TCP" 和 "tcp"）——此时由 prefix + n 区分，属于预期行为
    - 删除旧卡片后 `n` 可能产生空洞，不回收。这是预期行为：ID 稳定 > ID 连续

- [x] **0-05** `MVP` 评分 → due 日期

  - **目标**：四档间隔重复逻辑只写一处，所有脚本调用同一函数。
  - **验收**：
    ```python
    due_dates_from_rating("忘了", date(2026, 12, 31))  # → [2026-12-31, 2027-01-01]
    due_dates_from_rating("困难", date(2026, 6, 10))   # → [2026-06-11]
    due_dates_from_rating("还行", date(2026, 6, 10))   # → [2026-06-13]
    due_dates_from_rating("很熟", date(2026, 6, 10))   # → [2026-06-17]
    ```
  - **参数化测试场景**：
    - 正常日期
    - 跨月边界（`date(2026, 1, 31)` + 1 = `2026-02-01`）
    - 跨年边界（`date(2026, 12, 31)` + 1 = `2027-01-01`）
    - 闰年 2 月 29 日
    - 非法 rating → `ValueError`
  - **跨任务契约**：
    - 1-05（review_log due）、3-11（session 错题落盘）直接调用
    - `due_today.py` 的日期比较逻辑（1-09）与这里的输出格式强耦合：都用 `date <= today` 比较
  - **已知陷阱**：
    - `忘了` 返回 **2 个日期**（今天 + 明天）。调用方写入时必须遍历列表，不能只取 `[0]`
    - `date.fromisoformat("2026-06-10")` 返回 `date` 对象，不含时区。所有脚本使用同一时区（本地），不涉及 UTC 转换

- [x] **0-06** `MVP` 追加 `cards.yaml` 条目

  - **目标**：`review_log` 和后续出题脚本共用卡片写入，字段保证合规。
  - **验收**：
    ```python
    append_card(review_dir, card_dict) -> card_id
    ```
    - 必填字段检查：`id, course_id, subject, topic, prompt, answer, schedule`
    - 缺字段时抛 `ValueError(f"missing required fields: {fields}")`，不吞错
    - `schedule.due` 字段写入时确保为 `str`（ISO 日期），不是 `date` 对象
    - YAML 写入前对所有字符串字段做 bool 检查（TD-1），防止 `topic: "no"` 变成 `topic: false`
    - 文件不存在 → 创建 `schema_version: 1\ncards: []` + 追加
  - **跨任务契约**：1-04（review_log 同步写 cards）和 2-14（generate_questions 写入后也可标记为 card）调用
  - **已知陷阱**：
    - `yaml.safe_dump` 会把 Python `date` 对象序列化为 `2026-06-10`（不含引号），读回时变成 `datetime.date` 对象。如果脚本混用 `str` 和 `date`，比较会失败。**约定**：YAML 中 `due` 存字符串、`last_reviewed` 存字符串；脚本内统一 `date.fromisoformat()` 后再比

- [x] **0-07** `MVP` 更新 `progress.md` 下一步

  - **目标**：会话/计划结束后 progress 可恢复，且不破坏手写内容。
  - **验收**：
    ```python
    update_progress_next_action(review_dir, next_action: str, **kwargs) -> bool
    ```
    - 只修改 2 行：「最近复习」和「下一步」
    - 「当前最弱」可根据 `kwargs.get("weakest_topics")` 更新
    - 其他行（章节进度、错因）**原样保留**，包括用户手写的勾选和注释
    - 文件不存在 → 创建最小模板（对齐 `progress.md` 格式）
  - **技术决策**：
    - 用**行级正则替换**，不解析整个 Markdown 再重建。原因：用户可能在「章节进度」里手写笔记，重建会丢失
    - 匹配模式：
      ```python
      re.sub(r"^- 最近复习：.*$", f"- 最近复习：{today}", text, flags=re.M)
      re.sub(r"^- 下一步：.*$", f"- 下一步：{next_action}", text, flags=re.M)
      ```
  - **跨任务契约**：3-11（session 更新 progress）、3-05（plan 写完后更新 progress 下一步）调用
  - **已知陷阱**：
    - 如果用户修改了 `progress.md` 的格式（如把 `- 下一步：` 改成 `* 下一步：`），正则匹配失败，静默不更新。这是预期行为——不破坏用户自定义格式。如果多次运行都不更新，用户需要自己检查格式
    - 不处理 Markdown frontmatter 或嵌套列表

- [x] **0-08** `MVP` 统一读取 review 状态文件

  - **目标**：各脚本用同一 loader，字段缺省时行为一致，不再各自 `yaml.safe_load`。
  - **验收**：四个函数，均返回 typed dict（带默认值）：
    ```python
    load_files_yaml(review_dir) -> dict       # 缺 files 键 → {"files": []}
    load_exam_analysis(review_dir) -> dict    # analysis: null → {"analysis": None}
    load_generated_questions(review_dir) -> dict  # questions: [] → {"questions": []}
    load_cards(review_dir) -> dict            # cards: [] → {"cards": []}
    ```
  - **技术决策**：
    - 使用 `TypedDict` 注释返回值类型（不做运行时校验），帮助 IDE 和代码审查
    - `course.id` 和 `course_id` 字段同时存在时，优先 `course_id`（新格式），fallback `course.id`（历史兼容）
  - **已知陷阱**：
    - 不同脚本对"文件不存在"的容错需求不同：`analyze_exam` 需要 exit 1 并提示，`plan_review` 可以降级。所以 loader 返回 `None` 或空结构（不含 `sys.exit`），由调用方决定

---

## Epic 1：错题闭环 `[MVP 14/14]`

**Epic 目标**：答错一次 → `mistake-log.md` + `cards.yaml` 双写 → `due_today` 可查回。
**Epic 验收**：在 fixture 上记录 1 条错题后，当天或次日 `due_today.py --json` 可见对应 card。

**Epic 级技术决策**：
- `review_log.py` 是**唯二**会同时修改两个文件的脚本（另一个是 `review_session.py` 3-11）。双写失败必须 rollback 或至少报错不静默
- mistake-log.md 是给人看的，cards.yaml 是给脚本读的。两者数据源相同但格式不同——**cards.yaml 是 canoncial，mistake-log.md 是 derived view**

---

### `review_log.py` 升级

- [x] **1-01** `MVP` `--course` 定位 review 目录

  - **目标**：从「根目录单文件复习记录.md」迁移到「每课 `review/mistake-log.md`」。
  - **验收**：
    - `--course ../计算机网络` → 写入 `../计算机网络/review/mistake-log.md`
    - 未传 `--course` 且未传 `--log` → stderr 打印用法，exit 1
    - 传了 `--course` 但 `review/` 不存在 → 提示先 `init_course_review`，exit 1
  - **依赖**：0-02（`get_review_dir`）
  - **技术决策**：`--course` 参数接受课程目录路径（不是 review 路径）。内部调 `get_review_dir` 自动拼接 `/review/`
  - **已知陷阱**：用户可能传入 `--course 计算机网络/review`，此时 `get_review_dir` 会返回 `计算机网络/review/review/`。需在 `get_review_dir` 中检查路径是否已经以 `review` 结尾

- [x] **1-02** `MVP` 扩展 CLI 参数：元数据

  - **目标**：题卡元数据完整，支持后续按章节/难度/标签筛选和回顾。
  - **验收**：
    - 新增 `--chapter`（str）、`--difficulty`（choices: basic/medium/hard）、`--tags`（逗号分隔，如 `TCP,易混`）、`--source`（str，文件名或路径）
    - 以上参数均写入 `cards.yaml` 对应字段（`chapter`、`difficulty`、`tags` 列表、`source.file`）
    - 不传时写入默认值：`difficulty: medium`、`tags: []`、`source: null`
  - **跨任务契约**：`cards.yaml` 的 `difficulty` 字段值必须与 `data_formats.md` 中的 allowed values 一致
  - **已知陷阱**：`--tags "TCP, 易混"` 中 `, `（逗号+空格）需 strip 后再 split。写 `tags: [TCP, 易混]`，不是 `tags: [TCP, 易混]`

- [x] **1-03** `MVP` 写入 `mistake-log.md`

  - **目标**：人类可读，格式对齐 `data_formats.md` § mistake-log.md。
  - **验收**：每条含：
    - 日期（`## YYYY-MM-DD - {subject}`）
    - 知识点（`### 知识点` 下列 `- {topic}`）
    - 原题/问题（`### 原题/问题`）
    - 我的错误（`### 我的错误`）
    - 正确理解（`### 正确理解`）
    - **错因标签**（`### 错因标签`，至少 1 个，可选值见下）
    - 下次复查 checkbox（`### 下次复查` 下 `- [ ] YYYY-MM-DD` 列表）
  - **错因标签可选值**（来自 `orchestrator.md` MistakeLogTool）：
    ```
    concept_confusion | formula_condition | process_missing
    | calculation_error | expression_incomplete | memory_gap
    ```
    中文映射：`概念混淆 | 公式条件 | 流程遗漏 | 计算错误 | 表达不完整 | 记忆缺口`
  - **技术决策**：mistake-log.md 是**追加**模式——每次调用在文件末尾 append 一个新 section。不解析已有内容、不修改历史条目
  - **已知陷阱**：
    - 同一 session 多次答错同一 topic 会产生多个条目。这是预期行为——每次错因可能不同
    - 如果 `mistake-log.md` 被用户手工编辑后格式异常，脚本只追加不修复。下一个 section 可能插在错误位置

- [x] **1-04** `MVP` 同步追加 `cards.yaml`

  - **目标**：脚本可查 due，不只靠 Markdown checkbox。
  - **验收**：
    - `card_type: mistake_review`
    - `prompt` ← `--question`
    - `answer` ← `--correction`
    - `topic` ← `--topic`
    - `source.file` ← `--source`
    - `schedule.rating` ← `--rating`
    - `schedule.due` ← `due_dates_from_rating` 的第一个日期（最近一次复查日）
  - **依赖**：0-05（due_dates）、0-06（append_card）
  - **技术决策**：
    - 先写 `mistake-log.md`（文本追加，失败概率低），再写 `cards.yaml`（YAML 全量重写，失败概率高）
    - 如果 `cards.yaml` 写入失败，`mistake-log.md` 已经写入无法回滚。此时**必须** stderr 打印 `ERROR: cards.yaml write failed, mistake-log.md already written`，并 exit 1
    - 不尝试自动回滚 `mistake-log.md`（破坏性操作，可能删掉用户手写笔记）
  - **已知陷阱**：
    - `schedule.due` 存的是 `due_dates_from_rating` 返回列表的**第一个**（最近复查日）。完整的复查链存 `mistake-log.md` 的 checkbox 列表。`due_today.py` 的 cards 扫描只看 `schedule.due`；checkbox 扫描是独立的补充路径

- [x] **1-05** `MVP` 按 rating 生成 due

  - **目标**：mistake-log 的 checkbox 日期与 cards.yaml 的 `schedule.due` 一致。
  - **验收**：同一 rating 生成的两份 due 日期完全一致。
  - **实现**：直接调用 `review_io.due_dates_from_rating(args.rating, date.today())`
  - **依赖**：0-05
  - **已知陷阱**：如果在 23:59:59 运行脚本，`date.today()` 在 00:00:00 切换后，log 和 card 可能跨天。这在实践中不影响——很少有学生在午夜复习。如果真发生，最多差 1 天，不破坏闭环

- [x] **1-06** `MVP` 自动生成 card id

  - **目标**：多次 log 同一 topic 产生不冲突的 card id。
  - **验收**：
    - 从 `cards.yaml` 加载已有 ID 集合
    - 调用 `next_id("card", course_id, existing_ids, topic)`
    - 同 topic 第二错题 → `card-net-tcp-002`
  - **依赖**：0-04（next_id）、0-08（load_cards）

- [x] **1-07** `MVP` `--json` 输出（L2）

  - **目标**：供 `review_session` 和 future API 消费，机器可读。
  - **验收**：
    ```json
    {
      "schema_version": 1,
      "card_id": "card-net-tcp-001",
      "mistake_log_path": "计算机网络/review/mistake-log.md",
      "cards_yaml_path": "计算机网络/review/cards.yaml",
      "due_dates": ["2026-06-11", "2026-06-13", "2026-06-17"]
    }
    ```
  - **跨任务契约**：3-11（session 调 review_log）解析此 JSON 获取 `card_id` 和 `due_dates`
  - **已知陷阱**：
    - `review_session.py` 以 subprocess 调用 `review_log.py` 时，stdout 可能混入 stderr 日志。subprocess 调用时必须分别捕获 `stdout` 和 `stderr`，`json.loads(stdout)` 后再打印 stderr

- [x] **1-08** `MVP` 旧 `--log` 行为迁移

  - **目标**：不破坏已有使用习惯，但引导到新模型。
  - **验收**：
    - **决定：废弃 `--log`**。未传 `--course` 时 exit 1，stderr 输出 `Use --course <course_dir> instead.`
    - README 说明迁移方式：旧 `复习记录.md` 内容需手动迁移到 `课程/review/mistake-log.md`
  - **技术决策**：同时维护两套模型（单文件 log vs per-course review/）会显著增加 Epic 1 复杂度。当前仓库是 v0.1，不存在不可迁移的存量数据
  - **不做**：不实现自动迁移脚本

---

### `due_today.py` 升级

- [x] **1-09** `MVP` 扫描 `*/review/cards.yaml`

  - **目标**：多课程 workspace 级 due 查询。
  - **验收**：
    - `due_today.py <workspace_root>` 递归找 `**/review/cards.yaml`（排除 `tests/`、`.git/`、`__pycache__/`）
    - 所有 `schedule.due <= today` 的卡片列出
    - 每条显示：course name、card id、topic、prompt 摘要（前 60 字）、due 日期
    - 按 due 日期升序（最近 overdue 的排前面）
  - **依赖**：0-08（load_cards）
  - **技术决策**：
    - `workspace_root` 默认 `Path.cwd()`，与 `inventory.py` 行为一致
    - `schedule.due` 可能为 `null`（新卡片未安排复查）或缺失——跳过这些卡片，不计入 due
    - 日期比较：`date.fromisoformat(due_str) <= date.today()`
  - **已知陷阱**：
    - `cards.yaml` 中 `due` 字段可能被手写 `2026-06-10`（不带引号），PyYAML 解析为 `datetime.date` → `str()` 变成 `"2026-06-10"`。`fromisoformat` 两种都接受
    - 但如果手写 `2026-6-10`（缺少前导零），`fromisoformat` 会失败。此时应 WARN + 跳过该卡片

- [x] **1-10** `MVP` 扫描 `mistake-log.md` 未勾选 due

  - **目标**：兼容只有 Markdown 没有 YAML 的历史数据或手工记录。
  - **验收**：
    - 解析 `- [ ] YYYY-MM-DD` 且日期 ≤ today
    - 与 1-09 的 cards 结果去重：同一 `(topic, due_date)` 组合不重复显示
    - 去重策略：topic 文本匹配 + due 日期匹配（不要求完全精确，用 `topic in card_topic or card_topic in topic`）
  - **技术决策**：
    - Markdown 解析用正则 `r"^- \[ \] (?P<due>\d{4}-\d{2}-\d{2})"`，不要自己写状态机
    - 为了获取 topic 信息，需要向上查找最近的 `### 知识点` section
  - **已知陷阱**：
    - 用户的 mistake-log.md 可能被多次手工编辑，日期格式不统一（`- [ ] 2026/06/10`）。正则只匹配 `YYYY-MM-DD`，其他格式 silently skip——不是 bug，是明确拒绝非标准格式
    - 如果误解析到非 due 行的 `- [ ] YYYY-MM-DD`（如用户笔记中的示例日期），会产生 false positive。这是 regex 扫描的固有限制，MVP 可接受

- [x] **1-11** `MVP` 按课程分组输出

  - **目标**：「今天复习什么」一眼看清各科情况。
  - **验收**：
    - 人类输出格式：
      ```
      ## 计算机网络 (2)
      - 2026-06-10 | card-net-tcp-001 | TCP 拥塞控制 vs 流量控制
      - 2026-06-11 | card-net-ip-001 | 子网划分计算
      ## 概率论 (1)
      - 2026-06-10 | card-prob-001 | 贝叶斯公式适用条件
      ```
    - 无 due 时输出 `No due items today.`（单行，无额外信息）
    - 不输出统计、不输出鼓励语（保持简洁，供后续 agent/UI 消费）
  - **已知陷阱**：如果 course name 在两个来源不一致（YAML 里是 `计算机网络`，Markdown heading 里是 `计网`），会产生两个分组。分组 key 用 YAML 的 `course_id` 优先，fallback Markdown heading 文本

- [x] **1-12** `MVP` `--subject` 过滤

  - **验收**：
    - `--subject 计算机网络` 只返回该 subject 的 due
    - 匹配逻辑：case-insensitive 子串匹配 `course_id` 和 `subject` 字段
    - 无匹配时输出 `No due items for 计算机网络.`
  - **技术决策**：`--subject` 和 `workspace_root` 是两个独立维度——`--subject` 缩小结果范围，`workspace_root` 决定扫描起点

- [x] **1-13** `MVP` `--json` 输出（L2）

  - **目标**：`review_session --source due` 可直接消费。
  - **验收**：
    ```json
    {
      "schema_version": 1,
      "generated_at": "2026-06-10",
      "courses": [
        {
          "course_id": "computer-network",
          "name": "计算机网络",
          "items": [
            {
              "id": "card-net-tcp-001",
              "topic": "TCP congestion control",
              "prompt": "TCP 拥塞控制和流量控制的区别是什么？",
              "due": "2026-06-10",
              "source": "card",
              "source_path": "计算机网络/review/cards.yaml"
            }
          ]
        }
      ]
    }
    ```
  - **跨任务契约**：3-07（`review_session --source due`）解析此 JSON
  - **已知陷阱**：Windows `Path` 对象在 JSON 序列化时必须转 `str`；默认 `json.dumps` 不处理 `Path`

- [x] **1-14** `MVP` 单文件损坏容错

  - **目标**：一课坏数据不拖垮全局。
  - **验收**：
    - 某 `cards.yaml` 解析失败 → stderr `WARN: skipping cards.yaml in <path>: <reason>`
    - 某 `mistake-log.md` 不存在 → 静默跳过（不是错误）
    - 存在 partial 结果时 exit 0
    - 全部课程都失败时 exit 1（所有脚本 exit 码约定：0 = 成功/partial，1 = 输入错误，2 = 内部错误）
  - **依赖**：0-01（load_yaml 返回 None 或抛异常）

---

## Epic 2：试卷分析 + 出题 `[MVP 15/15]`

**Epic 目标**：`files.yaml` → `exam-analysis.yaml` → `past-exam-patterns.yaml` → `generated-questions.yaml`，全程有 evidence，不押题。
**Epic 验收**：fixture 上 `analyze_exam` 出 ≥3 priorities；`generate_questions` 出 5 道带 `scoring_points` 的变式题。

**Epic 级技术决策**：
- 这两个脚本是**整个系统算法最复杂的部分**——从文件名推断考点、从 pattern 生成变式题
- MVP 阶段不用 LLM，全部靠规则和模板。这意味着输出质量受限于模板质量和关键词映射准确度
- 两个脚本的输出**必须能被 Epic 3 的脚本直接消费**——字段名、类型、可选性必须完全对齐

---

### `analyze_exam.py`（Sprint B）

- [x] **2-01** `MVP` CLI 骨架

  - **目标**：统一入口，参数完整。
  - **验收**：
    ```
    python scripts/analyze_exam.py <course_dir> [--goal pass|score_high] [--dry-run] [--json]
    ```
    - `--goal` 默认 `pass`
    - `review/` 不存在 → exit 1，提示 `Run init_course_review.py first`
    - `--dry-run` 只打印将做什么（读哪些 files，生成哪些 priority），不写文件
  - **技术决策**：`course_dir` 是位置参数（positional），不是 `--course` flag。因为它是脚本的主操作对象

- [x] **2-02** `MVP` 读 `files.yaml`

  - **验收**：
    - 调 `load_files_yaml(review_dir)`
    - `files` 为空或 `files.yaml` 不存在 → exit 1，输出 `No materials registered. Upload files first.`
    - 提取 `course.id` 作为后续输出的 `course_id`
  - **依赖**：0-08
  - **已知陷阱**：`files.yaml` 中 `material_type` 可能已被用户手动修改。脚本应相信 `files.yaml` 中的标记，不重复 `guess_material_type()`

- [x] **2-03** `MVP` 筛选高价值文件

  - **目标**：分析输入聚焦考试相关资料。
  - **验收**：
    - 筛选 `material_type in (past_exam, mock_exam, homework_answer, teacher_focus)`
    - 若 ≥1 个高价值文件 → 继续分析
    - 若 0 个 → 降级用 `slides`，但所有 output 标记 `confidence: low`，同时 stderr WARN
    - 筛选结果按 `material_type` 优先级排序（past_exam > mock_exam > teacher_focus > homework_answer > slides）
  - **技术决策**：不在此步骤做任何内容解析——只看 `files.yaml` 中的 metadata

- [x] **2-04** `MVP` 推断 priorities（≥3 条）

  - **目标**：不解析 PDF/PPT 也能产出可用的优先级分析。
  - **验收**：
    - 至少输出 3 条 priority
    - 每条含：`topic, chapter, weight(1-5), question_types[], recommended_action`
    - `weight` 推断规则：
      - 文件名含 `*Transport*` / `*传输层*` + 存在于 past_exam → weight 5
      - 文件名含关键词 + 存在于 mock_exam / homework_answer → weight 4
      - 文件名含关键词 + 仅存在于 slides → weight 2-3
    - `question_types` 推断规则：文件名/章节名含 `计算`、`协议`、`流程` → 对应 question_type
  - **技术决策**：
    - **关键词→章节映射表**内嵌在脚本中（不是外部配置文件，MVP 阶段硬编码）：
      ```python
      CHAPTER_KEYWORDS = {
          "Transport": ["传输层", "transport", "tcp", "udp", "拥塞", "流量"],
          "Network": ["网络层", "network", "ip", "路由", "子网", "arp"],
          "Data Link": ["数据链路", "datalink", "mac", "帧", "差错"],
          "Physical": ["物理层", "physical", "编码", "调制"],
          "Application": ["应用层", "application", "http", "dns", "smtp"],
      }
      ```
    - `question_types` 推断规则：文件名含 `计算`/`子网` → `calculation`，含 `协议`/`流程`/`过程` → `flow`，含 `区别`/`对比`/`比较` → `contrast`，否则 `short_answer`
  - **不做**：不 OCR、不 PDF 全文抽取、不 PPT 文本抽取
  - **已知陷阱**：
    - 文件名是中文时，关键词匹配可能漏掉（如 "运传层" 误拼）。降低误拼的权重影响——只要 1 个文件命中就纳入
    - 纯英文课件（如 "6-Transport(3).pptx"）需要同时检查英文关键词

- [x] **2-05** `MVP` 匹配 evidence

  - **目标**：每个 priority 可追溯到本地文件。
  - **验收**：每条 priority 的 `evidence[]` 含：
    ```yaml
    evidence:
      - source_file: "计算机网络/计算机网络样题(5).pdf"
        reason: "appears in past exam as short_answer"
    ```
  - **技术决策**：`reason` 由规则生成（不是 LLM 自由文本）。格式：`"found in {material_type} file {filename}"` 或 `"chapter keyword matched in {filename}"`
  - **跨任务契约**：evidence 格式对齐 `data_formats.md` § exam-analysis.yaml

- [x] **2-06** `MVP` 写 `exam-analysis.yaml`

  - **目标**：持久化分析结果供 `plan_review` 和 `generate_questions` 读取。
  - **验收**：
    - 含 `schema_version, analysis.id, course_id, generated_at, goal, source_files[], summary, priorities[], plan_refs`
    - `summary` 一句话（如 `"传输层和网络层题型优先级较高，建议先做协议流程题再做计算题"`）
    - `plan_refs` 指向 `plan.md`
    - 文件已存在时默认 skip（除非 `--force`）
    - 写入前字段做 bool 检查（TD-1）
  - **参考**：`examples/sample_exam_analysis.yaml`、`data_formats.md`
  - **已知陷阱**：`generated_at` 应存 ISO datetime（`2026-06-10T20:30:00`）还是 ISO date（`2026-06-10`）？MVP 用 date，因为精度够用。存为字符串（加引号），防止 YAML 解析为 `datetime.date` 对象

- [x] **2-07** `MVP` 写 `past-exam-patterns.yaml`

  - **目标**：为 `generate_questions` 提供可复用的题型模板。
  - **验收**：
    - 每个 priority 至少 1 条 pattern
    - 每条含 `id, course_id, source_file, question_type, topic, chapter, difficulty, answer_shape, scoring_points[], reusable_template`
    - `reusable_template` 是自然语言描述（如 `"解释协议机制时按作用、触发条件、过程、结果组织答案"`）
    - `answer_shape` 可选值：`"作用 -> 触发条件 -> 过程 -> 结果"` / `"公式 -> 条件 -> 代入 -> 结果"` / `"定义 -> 区别 -> 例子"`
  - **技术决策**：
    - MVP 阶段 patterns 从规则生成：`question_type` 映射到 `answer_shape` 和 `reusable_template`，topic/chapter 由 2-04 的映射表填充
    - 每条 pattern 的 `id` 格式：`pattern-{course_id}-{n:03d}`
  - **跨任务契约**：2-11（`generate_questions` 套用模板）直接消费此文件的 `reusable_template` 和 `answer_shape`

- [x] **2-08** `MVP` analyze `--json` 输出（L2）

  - **验收**：
    ```json
    {
      "schema_version": 1,
      "analysis_id": "exam-analysis-net-001",
      "priorities_count": 4,
      "confidence": "medium",
      "warnings": [],
      "artifacts": ["exam-analysis.yaml", "past-exam-patterns.yaml"]
    }
    ```
  - **已知陷阱**：`confidence` 值需要在脚本内判定：有过 `past_exam` 文件 → `high`；只有 `mock_exam` / `teacher_focus` → `medium`；只有 `slides` → `low`

---

### `generate_questions.py`（Sprint C）

- [x] **2-09** `MVP` CLI 骨架

  - **验收**：
    ```
    python scripts/generate_questions.py <course_dir> --count 5 [--source patterns|analysis] [--goal pass|score_high] [--force] [--json]
    ```
    - `--count` 默认 5
    - `--source` 默认 `patterns`（优先从 past-exam-patterns.yaml），fallback `analysis`（从 exam-analysis.yaml priorities）
    - `review/` 中无 `past-exam-patterns.yaml` 且无 `exam-analysis.yaml` → exit 1，提示 `Run analyze_exam.py first`
  - **依赖**：0-02（get_review_dir）、0-08（loader）

- [x] **2-10** `MVP` 读分析输入并选 topic

  - **验收**：
    - 优先加载 `past-exam-patterns.yaml` 的 `patterns` 列表
    - 如果空，fallback `exam-analysis.yaml` 的 `priorities` 列表（此时 `confidence: low` 在 stderr WARN）
    - 两者都空 → exit 1
    - 按 `weight` 降序选 topic（高频优先），选满 `--count` 个
    - 同一 topic 不重复出题
  - **技术决策**：如果 `patterns/priorities` 数量 < `--count`，生成到实际数量为止（不填充随机题），stderr 输出实际数量

- [x] **2-11** `MVP` 套用问题模板

  - **目标**：题目风格一致，不依赖 LLM。
  - **验收**：
    - 从 `question_patterns.md` 中按 `question_type` 选择模板
    - 映射关系：
      | question_type | 模板来源 | 示例 |
      |---------------|----------|------|
      | `contrast` | Concept Contrast Patterns | "比较 {A} 和 {B}：控制对象、使用场景..." |
      | `flow` | Protocol Flow Patterns | "从 {start} 到 {end}，按顺序说出协议交互" |
      | `formula` | Formula Patterns | "{formula_name} 的公式是什么？适用条件？" |
      | `calculation` | Calculation Patterns | "先判题型，列步骤，不用算最终答案" |
      | `short_answer` | Active Recall Patterns | "不看资料，说出 {concept} 的定义和适用条件" |
    - 占位符 `{A}` `{B}` `{concept}` `{topic}` 等从 pattern 的 `topic` 和 `question_type` 推断填充
  - **技术决策**：
    - 模板引擎用 Python `string.Template`（`$variable` 语法），不用 Jinja2（避免引入依赖）
    - 占位符映射表内嵌在脚本中：
      ```python
      TEMPLATE_VARS = {
          "contrast": {"A": "...", "B": "...", "concept": "{topic}"},
          "flow": {"start": "起始事件", "end": "结束事件", "protocol": "{topic}"},
          ...
      }
      ```
  - **已知陷阱**：
    - 中文 topic 填入英文模板时会产生中英混排（如 "比较 TCP congestion control 和 UDP：..."）。MVP 阶段可接受——中文 topic 名称也会填，效果是 "比较 TCP 拥塞控制 和 UDP：..."
    - `string.Template` 的 `$variable` 语法与 YAML 中的 `${}` 不冲突，但如果模板中出现 `$$` 会被转义。模板文本中不应出现 `$`

- [x] **2-12** `MVP` 题目 12 个必填字段完整

  - **目标**：`review_session` 和 future API 无需猜测字段是否存在。
  - **验收**：每题必填字段（来自 `data_formats.md` § generated-questions.yaml）：
    - `id` ← `gen-{course_id}-{n:03d}`（n 从现有最大 +1 开始）
    - `course_id`
    - `based_on_pattern_id` ← 来源 pattern 的 id（如无可为 null）
    - `source_materials[]` ← pattern 的 `source_file`
    - `question_type` ← 从 pattern 继承
    - `topic`
    - `difficulty` ← 从 pattern 继承，缺省 `medium`
    - `similarity` ← `same_type`（默认）、`same_topic`、`mixed`
    - `label` ← `变式题`
    - `prompt` ← 模板填充结果
    - `expected_answer` ← 模板答案（可为空字符串 `""`——MVP 阶段 `scoring_points` 足够判分）
    - `scoring_points[]` ← 从 pattern 继承，至少 2 个
    - `time_limit_sec` ← 根据 `difficulty` 估计（basic=120, medium=180, hard=300）
  - **跨任务契约**：3-09（规则判分）依赖 `scoring_points` 的格式——每个点必须是一个短句/短语，不能是一段话。判分算法做子串匹配，评分点越原子化越好
  - **已知陷阱**：`scoring_points: ["说明目的", "说明触发条件"]` 这样的评分点太短，可能匹配到用户答案中的无关词汇。建议长度：6-15 个中文字

- [x] **2-13** `MVP` 安全标注

  - **验收**：
    - `label` 只能是 `模拟题`、`变式题`、`错题变式`
    - stdout/stderr 全文不含「押题」「必考」「命中」「预测」等字样
    - `similarity: same_type` 表示同题型不同参数；`same_topic` 表示同考点不同问法；`mixed` 表示混合卷
  - **技术决策**：检查在写入前做——全文扫描 `prompt` + `expected_answer` + `scoring_points` 的拼接文本，匹配黑名单正则 `押题|必考|命中|预测|今年一定|很可能考`。命中则 WARN 并提示人工检查

- [x] **2-14** `MVP` 写 `generated-questions.yaml`

  - **验收**：
    - 默认追加模式：加载已有 questions → 追加新题 → 原子写入
    - `--force` 模式：覆盖已有文件（全新生成）
    - 写入前字段 bool 检查（TD-1）
    - `schema_version: 1` 在文件头部
  - **依赖**：0-03（append_yaml_list）、0-06（可选——将来可能同时写 cards.yaml）

- [x] **2-15** `MVP` generate `--json` 输出（L2）

  - **验收**：
    ```json
    {
      "schema_version": 1,
      "questions_count": 5,
      "question_ids": ["gen-net-001", ..., "gen-net-005"],
      "artifact": "generated-questions.yaml"
    }
    ```

---

## Epic 3：计划 + 会话 `[MVP 11/11]`

**Epic 目标**：从分析/题目到可执行计划 → 一题一答 → 错题自动落盘。
**Epic 验收**：90 分钟 `plan.md` 含「现在开始」单一动作；`review_session` 答错 1 题后，`due_today` 可见该错题。

**Epic 级技术决策**：
- `review_session.py` MVP 阶段是**交互式 CLI**（L1），不做 `--json` 输出（L2 留到 v0.3 Agent 编排时做）
- 会话状态 MVP 阶段**不持久化到 YAML**——内存中维护，会话结束即丢失。v0.3 再加 session yaml 持久化
- 规则判分是整个系统的教学核心——算法设计直接影响用户信任度

---

### `plan_review.py`（Sprint D）

- [x] **3-01** `MVP` CLI 骨架

  - **验收**：
    ```
    python scripts/plan_review.py <course_dir> --minutes 90 [--goal pass|score_high] [--json]
    python scripts/plan_review.py <course_dir> --days 3 [--goal pass|score_high] [--json]
    ```
    - `--minutes` 和 `--days` 互斥，至少传一个
    - 同时传 → exit 1，输出 `Use --minutes or --days, not both`
    - 默认 `--minutes 90 --goal pass`（如果两个都没传）
  - **已知陷阱**：`--minutes 30` 和 `--days 3` 的时间分配策略完全不同——不能共用一套分配逻辑

- [x] **3-02** `MVP` 读取状态输入

  - **验收**：按优先级加载：
    1. `progress.md` → 当前阶段、最弱 topic、chapter 进度
    2. `exam-analysis.yaml` → priorities（有则优先用于计划）
    3. `cards.yaml` → due items（复查项加入计划）
    - `exam-analysis.yaml` 缺失 → 降级读取 `files.yaml` 的 material counts + stderr WARN（`No exam analysis found, plan based on material counts only`）
    - 所有三个文件都不存在 → exit 1，输出 `No course state available. Run init_course_review and analyze_exam first.`
  - **依赖**：0-08（四个 loader）

- [x] **3-03** `MVP` 时间预算模式

  - **目标**：生成具体分钟数和任务，不是泛泛建议。
  - **验收**：
    - `--minutes 30`：3-4 个任务，每个任务 5-15 分钟
    - `--minutes 90`：5-7 个任务，每个任务 10-25 分钟
    - `--days 3`：3 天，每天 2-3 个任务，总时长约 90 分钟/天
    - `--days 7`：7 天，每天 2-3 个任务
    - 每个任务格式：`{duration}min: {action}（{source}）`
  - **技术决策**：时间分配算法——优先给高频 priority 的 topic 分配复习时间，再分配弱项 topic，最后分配 due 错题复查
  - **已知陷阱**：如果 materials 太少（< 3 个 topic），生成的计划会很短。此时不要填充"建议找更多资料"之类的废话——诚实输出可用的内容

- [x] **3-04** `MVP` `--goal` 影响优先级排序

  - **验收**：
    - `pass`：高频题型 > 弱项 topic > due 错题。跳过 `difficulty: hard` 的证明/构造题
    - `score_high`：高频题型 > 弱项 topic > due 错题 + 加入综合题和 `difficulty: hard` 题
    - 体现在「先做/后可做」排序上
  - **技术决策**：`--goal score_high` 时不跳过困难题，但 plan 中标注为「选做」

- [x] **3-05** `MVP` 输出 `plan.md` 七段结构

  - **目标**：可执行、可追溯、有「现在开始」。
  - **验收**：七段必含：
    ```markdown
    # {course}复习计划
    ## 目标
    - {pass / 高分} | {30/90 分钟 or 3/7 天}
    ## 依据
    - {exam-analysis.yaml}（analysis id: xxx）
    - {progress.md}
    - {cards.yaml}（due items: n）
    ## 先做
    {按优先级排列的任务列表}
    ## 后做
    {次要任务}
    ## 可以先放弃
    {本次不覆盖的 topic}
    ## 最后 15 分钟
    {收尾动作}
    ## 现在开始
    {单一明确动作，如 "运行 `python scripts/review_session.py ../计算机网络 --source generated`"}
    ```
  - **跨任务契约**：
    - 「现在开始」的动作文本会被 `review_session.py` 3-07 消费（CLI 自动填入 `--source`）
    - 3-11（session 结束后更新 progress 下一步）会覆盖「现在开始」中的下一步建议
  - **已知陷阱**：
    - 「现在开始」必须是**单一可执行动作**，不能是列表。如果是列表，用户会困惑
    - 「可以先放弃」必须诚实——标注了放弃就不要在后面段落中出现

- [x] **3-06** `MVP` plan `--json` 输出（L2）

  - **验收**：
    ```json
    {
      "schema_version": 1,
      "goal": "pass",
      "minutes": 90,
      "first_action": "python scripts/review_session.py ../计算机网络 --source generated",
      "artifact": "plan.md",
      "skipped_topics": ["Application Layer"]
    }
    ```

---

### `review_session.py`（Sprint E，L1）

- [x] **3-07** `MVP` CLI 骨架 + 题目来源加载

  - **验收**：
    ```
    python scripts/review_session.py <course_dir> --source generated|due|cards [--limit 5] [--non-interactive --answer "..."]
    ```
    - `--source generated` → 加载 `generated-questions.yaml`
    - `--source due` → 调 `due_today.py --json` subprocess，过滤当前 course
    - `--source cards` → 加载 `cards.yaml`
    - `--limit` 默认 5
    - 无题 → exit 1，输出 `No questions available. Run generate_questions or check due_today.`
    - `review/` 不存在 → exit 1，提示 run init
  - **技术决策**：
    - `--source due` 的 subprocess 调用：`subprocess.run([sys.executable, "scripts/due_today.py", str(workspace_root), "--json", "--subject", course_name], capture_output=True, text=True)`
    - 不 import `due_today` 模块——保持脚本间进程隔离（TD-6）
  - **已知陷阱**：`--source due` 和 `--source cards` 加载的题目结构不同——due 返回 card 格式，generated 返回 question 格式。需要在 session 内部统一为内部 `Question` 结构：
    ```python
    @dataclass
    class Question:
        id: str
        prompt: str
        expected_answer: str
        scoring_points: list[str]
        topic: str
        time_limit_sec: int
    ```

- [x] **3-08** `MVP` 一题一展示 + 交互循环

  - **验收**：
    - 交互模式：打印题号（第 1/5 题）、prompt、建议限时；等待 stdin 输入答案；输入空行或 EOF（Ctrl+Z/Ctrl+D）结束
    - `--non-interactive --answer "答案文本"`：不等待输入，直接提交答案并输出判分结果，exit 0
    - 永远不一次打印全部题目（即使 `--non-interactive`）
    - 每题之间打印分隔线 `---`
  - **技术决策**：交互输入用 `sys.stdin.read()` 读多行（直到 EOF）。用户答案可能跨多行
  - **已知陷阱**：
    - Windows `cmd.exe` 中 Ctrl+Z 是 EOF，bash 中 Ctrl+D 是 EOF。`sys.stdin.read()` 在两种终端行为一致
    - `--non-interactive` 下的 `--answer` 参数可能含换行符。argparse 默认不支持多行值，需要用 TD-6 的临时文件传参。MVP 阶段 `--non-interactive` 主要用于测试，单行答案够用

- [x] **3-09** `MVP` 规则判分

  - **目标**：第一版不依赖 LLM，用评分点关键词匹配判分。
  - **验收**：
    ```python
    def grade_answer(user_answer: str, scoring_points: list[str], expected_answer: str) -> dict:
        """
        Returns:
        {
            "verdict": "correct" | "partial" | "wrong",
            "score_hint": "3/5 scoring points covered",
            "covered_points": [...],
            "omissions": [...],
            "coverage_pct": 60.0
        }
        """
    ```
  - **技术决策/算法设计**：
    ```
    对每个 scoring_point:
      1. 提取评分点中的关键词（长度 ≥2 的中文词，或英文单词）
      2. 排除停用词："的"、"是"、"在"、"和"、"了"、"一个" 等
      3. 在 user_answer 中做 case-insensitive 子串匹配
      4. 如果 ≥50% 的关键词在 answer 中出现 → 该点 covered
    覆盖率 ≥80% → correct
    覆盖率 40-79% → partial
    覆盖率 <40% → wrong
    ```
  - **技术决策**：不用 jieba 分词（避免引入 C 扩展依赖）。用简单的**逐词子串匹配** + 最少字符长度过滤（避免"是"匹配到所有中文句子）
  - **跨任务契约**：此算法**强依赖** `scoring_points` 的写法。如果评分点写成 "拥塞控制防止网络过载，流量控制防止接收方被发送方压垮"（一个点含两个概念），算法会把整个句子当关键词集合，匹配效率下降。**评分点应每点一个原子概念**
  - **已知陷阱**：
    - 中文同义词："拥塞控制" vs "阻塞控制"——子串匹配会漏掉。MVP 不处理同义词
    - 用户用英文答中文题（或反之）——不处理，匹配失败也算错
    - 算法对「有回答但答偏了」和「完全没答」的区分度不高。两者都可能 0% 覆盖 → `wrong`。这是规则判分的固有限制
  - **不做**：不接入 OpenAI API、不用 embedding 相似度、不用 LLM 判分

- [x] **3-10** `MVP` 反馈与追问

  - **验收**：
    - `correct`：`✓ 正确。` + 可选追问题（如果 scoring_points 中有扩展点）
    - `partial`：`△ 部分正确（{score_hint}）。` + 遗漏要点列表 + 更稳答法（来自 expected_answer） + 1 个追问题
    - `wrong`：`✗ 错误（{score_hint}）。` + 遗漏要点 + 更稳答法 + 1 个追问题
    - 追问题从 `question_patterns.md` 的 Mistake Follow-Up Patterns 中选：
      - 如果 `omissions[0]` 是概念性 → 「最小补题」："{missing_point} 是什么？"
      - 如果是步骤性 → 「反向解释」："为什么错误答案不成立？"
  - **技术决策**：追问题生成不依赖 LLM——用预定义模板 + missing_point 文本拼接
  - **已知陷阱**：如果全部 scoring_points 都匹配但 `expected_answer` 中有额外细节 → 判 `correct` 但追问中提及遗漏的细节。这不增加算法复杂度

- [x] **3-11** `MVP` 错题落盘 + 更新 progress

  - **目标**：`partial` 或 `wrong` 时自动调 `review_log.py` 记录，会话结束时更新 `progress.md`。
  - **验收**：
    - `partial` 或 `wrong` → subprocess 调 `review_log.py --course <course> --json --topic ... --question ... --correction ... --rating ...`
    - `correct` → 不写错题，但可选是否标记为 `rating: 很熟`（用户手动确认）
    - 会话结束（所有题答完或用户 Ctrl+C）→ 调 `update_progress_next_action(review_dir, next_action, weakest_topics=[...])`
    - 用户 Ctrl+C 中断 → 已答题目（包括已记录的错题）不丢失
  - **依赖**：0-07（update_progress）、Epic 1（review_log.py 可用）
  - **技术决策**：
    - `rating` 自动推断：`partial` → `困难`，`wrong` → `忘了`
    - `--json` 输出解析：`json.loads(subprocess_result.stdout)`
    - 会话中维护 `session_results: list[dict]`，每答一题 append
    - Ctrl+C handler：`signal.signal(signal.SIGINT, save_and_exit)` ——保存已记录结果后退出
  - **已知陷阱**：
    - subprocess 调用 `review_log.py` 的开销：每错一题 fork 一个 Python 进程（~200ms）。MVP 可接受。如果后续性能成为问题，改为 `import review_log` 直接调用函数
    - 如果用 Ctrl+C 在 `review_log.py` subprocess 运行中中断，可能导致双写中的一部分（mistake-log 写了但 cards 没写）。`review_log.py` 本身不做事务（见 1-04 已知陷阱），此风险已文档化

---

## Epic 4：init 补齐 `[MVP 1/3 + v0.2 2/3]`

- [x] **4-01** `v0.2` `init_course_review.py` 补 `--json`

  - **验收**：
    ```json
    {
      "schema_version": 1,
      "course_id": "computer-network",
      "course_dir": "/abs/path/to/计算机网络",
      "review_dir": "/abs/path/to/计算机网络/review",
      "materials_count": 3,
      "created": ["files.yaml", "progress.md", ...],
      "skipped": ["mistake-log.md", ...]
    }
    ```
  - **说明**：MVP 不阻塞——`init` 的人类输出已经够用。L2 在 v0.3 Agent 编排时需要

- [x] **4-02** `v0.2` 改进 `guess_material_type()`

  - **目标**：文件名分类准确率提升，减少人工修正。
  - **验收**：在 fixture 上：
    | 文件 | 期望类型 |
    |------|----------|
    | `计算机网络样题(5).pdf` | `mock_exam` |
    | `6-Transport(3).pptx` | `slides` |
    | `期末复习重点.pdf` | `teacher_focus` |
    | `计网往年题2024.pdf` | `past_exam` |
    | `作业答案-ch3.pdf` | `homework_answer` |
    | `我的笔记.md` | `notes` |
  - **技术决策**：
    - 扩展关键词表：
      ```python
      TYPE_KEYWORDS = {
          "past_exam": ["往年", "真题", "历年", "试题", "期末考试", "试卷"],
          "mock_exam": ["样题", "模拟", "sample", "mock"],
          "homework_answer": ["作业答案", "习题答案", "作业解答", "hw", "homework"],
          "teacher_focus": ["重点", "范围", "考纲", "划范围", "考点", "复习提纲"],
          "slides": [],  # fallback by extension
          "notes": ["笔记", "note", "总结", "整理"],
      }
      ```
    - 匹配顺序：past_exam > mock_exam > homework_answer > teacher_focus > notes > slides（extension）
    - 如果多条规则同时命中 → 按优先级取第一个
  - **已知陷阱**：
    - `"期末考试重点.pdf"` 同时命中 `past_exam`（考试）和 `teacher_focus`（重点）→ 按优先级 past_exam
    - 纯英文文件名 `"final-review.pdf"` 无关键词命中 → fallback 到 extension
  - **依赖**：4-03（fixture 先建好才能测试）

- [x] **4-03** `MVP` 创建 fixture 课程目录

  - **验收**：
    ```text
    tests/fixtures/computer-network/
    ├── 计算机网络样题(5).pdf      → mock_exam
    ├── 6-Transport(3).pptx        → slides
    └── 期末复习重点.pdf            → teacher_focus
    ```
    - 三个文件均为空文件（`touch` 创建，0 bytes）
    - 运行 `init_course_review.py tests/fixtures/computer-network` 后：
      - `review/files.yaml` 至少 3 条记录
      - 三条记录的 `material_type` 分别正确
      - 原始 fixture 文件不被修改
  - **不做**：不要求 fixture 文件有真实 PDF/PPTX 内容
  - **技术决策**：fixture 目录放在 `tests/fixtures/computer-network/`，不走真实课程路径。`.gitignore` 中不忽略 fixture（它是测试基础设施的一部分，需要版本控制）

---

## Epic 5：测试 `[v0.2 7/7，非 MVP]`

**Epic 目标**：确定性逻辑有回归保护；`python -m unittest` 一键跑完。
**Epic 验收**：7 条测试全部 pass，exit 0。

**Epic 技术决策**：
- 测试框架：`unittest`（标准库，零依赖）
- 测试文件：`tests/test_review_io.py`、`tests/test_review_log.py`、`tests/test_due_today.py`、`tests/test_analyze_exam.py`、`tests/test_generate_questions.py`、`tests/test_init.py`
- 所有测试使用 `tests/fixtures/` 下的临时副本，通过 `tempfile.TemporaryDirectory` 创建隔离环境
- **不依赖真实课程资料**——所有测试数据来自 fixture 或代码内嵌字符串

---

- [x] **5-01** `v0.2` init 重复运行不覆盖

  - **测试设计**：
    ```python
    def test_init_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            course = Path(tmp) / "test-course"
            course.mkdir()
            (course / "slides.pptx").touch()
            # 第一次运行
            subprocess.run([..., "init_course_review.py", str(course)])
            progress = (course / "review/progress.md").read_text()
            # 第二次运行
            result = subprocess.run([..., "init_course_review.py", str(course)], capture_output=True)
            assert "skipped existing" in result.stdout
            assert (course / "review/progress.md").read_text() == progress  # 内容不变
    ```

- [x] **5-02** `v0.2` review_log due 四档映射

  - **测试设计**：参数化测试覆盖四档 rating + 边界（跨月、跨年）：
    ```python
    @pytest.mark.parametrize("rating,base,expected", [
        ("忘了", date(2026, 6, 10), [date(2026, 6, 10), date(2026, 6, 11)]),
        ("困难", date(2026, 6, 10), [date(2026, 6, 11)]),
        ("还行", date(2026, 6, 10), [date(2026, 6, 13)]),
        ("很熟", date(2026, 6, 10), [date(2026, 6, 17)]),
        ("忘了", date(2026, 12, 31), [date(2026, 12, 31), date(2027, 1, 1)]),
        ("困难", date(2026, 2, 28), [date(2026, 3, 1)]),  # 非闰年跨月
    ])
    ```
  - **需要**：如果团队不想引入 pytest，用 `unittest` 的 `subTest` 等价实现

- [x] **5-03** `v0.2` due_today 多课程扫描

  - **测试设计**：在临时目录下创建 2 个课程 `review/`，各有 cards；验证 due_today 返回 2 组；只一课有 due 时另一课不出现在结果中

- [x] **5-04** `v0.2` due_today `--json` 结构验证

  - **测试设计**：snapshot 测试——固定 fixture 输入，断言 JSON 输出包含 `schema_version`、`courses[].items[]` 数组，每条 item 有 `id, topic, prompt, due, source`

- [x] **5-05** `v0.2` 坏 YAML 容错

  - **测试设计**：在 fixture 中故意写坏一个 `cards.yaml`（如 `cards: [unclosed string`），验证 `due_today.py` 仍返回另一课结果 + stderr 含 `WARN`

- [x] **5-06** `v0.2` analyze_exam 输出 schema

  - **测试设计**：在 fixture 上跑 `analyze_exam`，验证 `exam-analysis.yaml` 的 `priorities` 长度 ≥3，每条有 `evidence`、`weight`、`question_types`；`confidence` 字段存在

- [x] **5-07** `v0.2` generate_questions 字段完整

  - **测试设计**：验证 `--count 5` 后每题有 `prompt, scoring_points, label, time_limit_sec, source_materials`；`label in ("模拟题", "变式题")`；无「押题」措辞

```bash
python -m unittest discover -s tests -p "test_*.py"
```

---

## Epic 6：E2E 验证

**Epic 目标**：证明不是「文档好看」，而是命令链能跑。
**Epic 验收**：6 条命令顺序执行 exit 0。

- [x] **6-01** `MVP` fixture 完整命令链

  - **验收**：文首 6 条命令顺序执行 exit 0
  - **测试**：`review_session` 用 `--non-interactive --answer "拥塞控制面向网络"` 模拟部分正确
  - **记录**：结果写入 `tests/e2e_results.md`

- [x] **6-02** `MVP` review 工作区完整性

  - **验收**：8 个标准文件均存在；`git status` 显示仅 `review/` 和 `tests/` 有新文件，fixture 目录无改动

- [x] **6-03** `MVP` 分析结果有效

  - **验收**：`exam-analysis.yaml` 的 `source_files` 非空；`priorities` ≥3；每条 evidence 指向 fixture 内真实文件名

- [x] **6-04** `MVP` 生成题质量

  - **验收**：5 题均有 ≥2 个 `scoring_points`；`based_on_pattern_id` 非空；无「押题」措辞

- [x] **6-05** `MVP` 计划可执行

  - **验收**：`plan.md` 含七段；「现在开始」是单一动作；「依据」列出 ≥1 个本地文件名

- [x] **6-06** `MVP` 错题复查

  - **验收**：session 中答错 1 题 → `mistake-log.md` 有记录 → `cards.yaml` 有 `card_type: mistake_review` 的 card → `due_today` 当天或次日列出该 card
  - **关键**：这是 MVP 最难证伪的一环，必须人工跑通一次交互 session

- [ ] **6-07** `可选` 真实 `计算机网络` 目录复验

  - **验收**：对真实课程目录重复 6-01；记录与 fixture 差异（分类不准、缺文件等）到 issue
  - **前置**：用户提供本地 `计算机网络` 课程路径

---

## Epic 7：文档 `[v0.2 3/3，非 MVP]`

- [x] **7-01** `v0.2` 维护 `tasks.md` 勾选与进度表
  - **验收**：每 Epic 完成后更新进度总览表；已完成项勾选；阻塞项注明原因

- [x] **7-02** `v0.2` 更新 `README.md`
  - **验收**：含问题定义（一句）、依赖（Python 3.10+、pyyaml）、完整 CLI 示例（6 步命令链）、当前限制（不解析 PDF、规则判分、不接 LLM）；≤150 行；链接到 `tasks.md` 和 `PLAN.md`

- [x] **7-03** `v0.2` 记录 6 项质量指标实测值
  - **验收**：在 E2E 跑通后填入下表：

| 指标 | 阈值 | 实测 | 通过 |
|------|------|------|------|
| time_to_first_question | ≤90s | | |
| source_coverage | 每题 ≥1 依据 | | |
| actionability | 计划含「现在开始」 | | |
| question_quality | 有答案+评分点 | | |
| review_recovery | progress 可恢复 | | |
| due_recall | 错题可查回 | | |

---

## 执行顺序

### 只做 MVP（55 条）

```text
Epic 0 (8)
  → Epic 1 (14)
  → 4-03 (1)
  → Epic 2 (15)
  → Epic 3 (11)
  → 6-01 ~ 6-06 (6)
```

**关键路径**：`0 → 1 → 4-03 → 2 → 3-11 → 6-06`

### MVP 完成后做 v0.2 完整（+12）

```text
4-01 → 4-02 → Epic 5 (7) → Epic 7 (3)
```

---

## Phase 2 预览（MVP 后再展开）

### v0.3：Agent 编排闭环 `估 ~12 条`

**启动条件**：MVP 清单 M1–M10 + Q1–Q12 全部打勾。

#### Agent 编排定量指标

| # | 指标 | 阈值 | 测量方式 |
|---|------|------|----------|
| A1 | 意图分类准确率（7 类 intent） | ≥90% | 35 条中文用户输入（每 intent 5 条），人工标注 → agent 分类对比 |
| A2 | 工具选择准确率 | ≥85% | 同上——正确 tool_called 的比例 |
| A3 | Agent 响应延迟（端到端） | ≤5s | `POST /agent/run` 到返回 `nextAction` 的 wall-clock 时间 |
| A4 | Source policy 违规率 | ≤5% | 35 条 eval 中声称了非本地事实的比例 |
| A5 | 幻觉工具调用率 | 0% | 声称调用了未实现工具 → 直接 fail |
| A6 | 状态机跳转正确率 | ≥90% | 给定 state_before + intent，state_after 正确 |
| A7 | Session 中断恢复成功率 | 100% | 模拟 Ctrl+C 后重新进入，能从上次断点继续 |
| A8 | 7 条最小 eval 全部通过 | 100% | `agent_development_plan.md` § Evaluation Plan 的 7 个场景 |

#### Agent 架构设计

```
总控智能体 × 1（StudyReviewOrchestrator）
  ├── 不引入子 Agent（v0.3 阶段单总控足够）
  ├── Python 工具层 × 7（CLI 脚本封装为标准 tool contract）
  └── LLM 调用 × 1（仅 orchestrator 调模型做判分/出题/解释）
```

**调度原则**：
- 固定按钮走固定 API（`POST /courses/{id}/exam-analysis` 等），不经过 agent
- 自然语言输入走 `POST /agent/run`，由 orchestrator 路由
- 每个 agent turn 最多调 1 个工具，返回结果后再决定下一步（串行、可见、可打断）

#### Agent 任务概要（详细拆解留到 v0.3 独立 task 文件）

| ID | 任务 | 验收 |
|----|------|------|
| A-01 | `POST /agent/run` 端点 | 接收 `{courseId, message, goal}` → 返回 `{intent, nextView, message, artifacts[], nextAction}` |
| A-02 | Session 持久化 YAML | 会话状态写入 `review/session.yaml`；中断后可恢复；含 `current_index, answered[], pending_ids[]` |
| A-03 | LLM 判分替代规则判分 | 接 OpenAI API 判分；20 题准确率 ≥90%（vs Q6 的 70%）；延迟 ≤3s/题 |
| A-04 | 意图分类器 | 35 条 eval ≥90%；支持 8 种 intent |
| A-05 | 工具调度器 | 7 个 tool contract（init/analyze/generate/plan/session/review_log/due_today） |
| A-06 | GET `/courses/{id}/state` | 返回 course snapshot（`agent_development_plan.md` 定义的字段） |
| A-07 | 7 条最小 eval 自动化 | `pytest tests/test_agent_eval.py`；CI 可跑；回归保护 |

#### LLM 判分 prompt 设计

系统 prompt 注入 `SKILL.md` + `source_policy.md` + 当前题的 `expected_answer` + `scoring_points`。返回结构化 JSON：
```json
{
  "verdict": "correct|partial|wrong",
  "score_hint": "3/5 scoring points covered",
  "covered_points": ["...", "..."],
  "omissions": ["...", "..."],
  "better_answer": "...",
  "follow_up_question": "...",
  "should_log_mistake": true
}
```

**判分延迟预算**：≤3s/题（含 API round-trip）。超时 5s 则 fallback 规则判分。

---

### v0.4：FastAPI 后端 `估 ~14 条`

**启动条件**：v0.3 A1–A8 全部达标。

#### API 性能指标

| # | 指标 | 阈值 | 说明 |
|---|------|------|------|
| P1 | 单接口响应时间（P50） | ≤200ms | 不含 LLM 调用的确定性接口 |
| P2 | 单接口响应时间（P95） | ≤500ms | 同上 |
| P3 | LLM 接口响应时间（P50） | ≤3s | `/agent/run`、判分接口 |
| P4 | LLM 接口响应时间（P95） | ≤8s | 含 API 重试 |
| P5 | 并发能力 | 5 req/s 不降级 | 本地单用户场景，够用 |
| P6 | 接口测试覆盖率 | ≥80% | `pytest --cov=services/api` |

#### 核心接口（8 个）

```
GET  /courses                                    → 课程列表 + 状态摘要
POST /courses/{id}/init-review                   → 初始化 review 工作区
GET  /courses/{id}/materials                     → 已登记资料列表
POST /courses/{id}/exam-analysis                 → 触发试卷分析
POST /courses/{id}/questions                     → 生成变式题
POST /courses/{id}/plan                          → 生成复习计划
POST /review-session/start                       → 开始一题一答会话
POST /review-session/answer                      → 提交答案 → 判分 → 记录错题
GET  /due-today                                  → 今日待复习
POST /agent/run                                  → 自然语言路由（v0.3 产物）
```

#### 后端任务概要

| ID | 任务 | 验收 |
|----|------|------|
| B-01 | FastAPI app 骨架 + 路由注册 | Swagger UI 可访问，`/openapi.json` 自动生成 |
| B-02 | `core/storage.py`：统一文件读写 | 替代 `review_io.py` 的直接调用；支持 SQLite 预备 |
| B-03 | `core/scheduler.py`：due 日期计算 | 封装 `due_dates_from_rating`；支持自定义间隔 |
| B-04 | `core/agent.py`：Orchestrator 入口 | 加载 SKILL.md + references → 组装 prompt → 调 LLM |
| B-05 | 8 个 route handler | 每个 route 调对应 core 模块 + 返回 Pydantic model |
| B-06 | Pydantic models（request/response） | 与 `data_formats.md` + TS 类型对齐 |
| B-07 | 输入校验 + 错误处理 | 404/422/500 统一格式；source policy 校验 |
| B-08 | API 集成测试（8 接口 × 2 case） | `tests/test_api.py`；使用 `TestClient` + fixture |

---

### v0.5：React + TypeScript 前端 `估 ~18 条`

**启动条件**：v0.4 全部接口稳定，P1–P6 达标。

#### 前端设计目标：大厂工具质感

一句话设计方向：

> **Notion 的克制排版 + Linear 的响应速度 + Vercel 的设计语言 + shadcn/ui 的组件质量**

不是花哨 dashboard，是**让你想每天打开的工具**。

#### 开源参考项目

| 参考 | 学什么 | 链接 |
|------|--------|------|
| **shadcn/ui** | 组件体系、配色、暗色模式 | github.com/shadcn-ui/ui |
| **Linear** | 键盘快捷键、行内编辑、微交互 | linear.app |
| **Notion** | 侧边栏导航、slash command、block 编辑器 | notion.so |
| **Vercel Analytics** | 数据卡片、图表克制、留白 | vercel.com/analytics |
| **Raycast** | 命令面板、快速操作、无鼠标流 | raycast.com |
| **Anki** | 复习卡片 UI、翻转动效、评分按钮 | apps.ankiweb.net |
| **Quizlet** | 答题模式切换、进度条、Learn 模式 | quizlet.com |
| **Obsidian** | 本地文件感知、graph view、Markdown 渲染 | obsidian.md |

#### 前端性能指标（Lighthouse / 实测）

| # | 指标 | 阈值 | 说明 |
|---|------|------|------|
| F1 | FCP (First Contentful Paint) | ≤1.2s | 首屏可见内容 |
| F2 | LCP (Largest Contentful Paint) | ≤2.0s | 最大可见元素 |
| F3 | TTI (Time to Interactive) | ≤2.5s | 可交互 |
| F4 | CLS (Cumulative Layout Shift) | ≤0.1 | 布局稳定性 |
| F5 | 路由切换感知延迟 | ≤150ms | 页面间导航 |
| F6 | 答题提交 → 判分展示 | ≤500ms | (本地 API) |
| F7 | 文件上传 → 就绪状态 | ≤2s | 含后端索引 |

#### 6 个页面 + 公共组件

**页面清单**：

| 页面 | 路由 | 核心交互 | 参考 |
|------|------|----------|------|
| **Dashboard** | `/` | 今日 due 数、各科进度环、快速开始按钮、最近错题预览 | Vercel Analytics 卡片 + Linear 快捷操作 |
| **Course** | `/course/:id` | 资料列表（表格 + 类型标签）、章节进度、操作入口（分析/出题/计划/练习） | Notion database view |
| **Materials** | `/course/:id/materials` | 拖拽上传、文件类型下拉选择、解析状态 badge、批量操作 | Linear 文件附件 + shadcn/ui upload |
| **Exam Analysis** | `/course/:id/analysis` | 优先级列表（按 weight 排序）、evidence tooltip、题型分布、一键生成按钮 | Notion 分栏 + shadcn/ui accordion |
| **Plan** | `/course/:id/plan` | 时间轴/任务列表、倒计时、跳过标记、「现在开始」大按钮 | Linear issue list + Raycast 快速操作 |
| **Quiz Session** | `/course/:id/quiz` | 单题展示、文本输入/选择、提交 → 翻转判分、评分按钮（忘了/困难/还行/很熟）、进度条 | Anki 卡片 + Quizlet Learn |

**公共组件**：

| 组件 | 用途 | 参考 |
|------|------|------|
| `CommandPalette` | Cmd+K 全局搜索/导航 | Raycast |
| `DueBadge` | 到期数量红点/数字 | Linear inbox |
| `RatingButton` | 四档评分（忘了/困难/还行/很熟） | Anki 评分按钮 |
| `ProgressRing` | 课程完成度环形图 | Vercel Analytics |
| `EvidenceTooltip` | hover 显示来源文件和依据 | shadcn/ui tooltip |
| `ScoreCard` | 判分结果卡片（correct/partial/wrong 三色） | Linear issue status |
| `MarkdownRenderer` | 渲染 plan.md / mistake-log.md | Obsidian 渲染风格（简洁、不高亮过度） |
| `FileDropZone` | 拖拽上传 + 类型选择 | shadcn/ui + react-dropzone |
| `EmptyState` | 空数据引导（"还没有题目？去分析试卷 →"） | Linear empty state（图标 + 一句话 + CTA） |

#### 技术栈

```
React 18+ + TypeScript 5+
Vite 5+（开发 HMR < 1s）
Tailwind CSS + shadcn/ui（组件 + 暗色模式）
TanStack Query（服务端状态 / 缓存 / 乐观更新）
Zod（API 响应校验——与后端 Pydantic schema 对齐）
react-router v6（路由）
```

#### 前端任务概要

| ID | 任务 | 验收 |
|----|------|------|
| C-01 | Vite + TS + Tailwind + shadcn/ui 项目脚手架 | `npm run dev` 启动 ≤3s；HMR ≤1s |
| C-02 | Zod schema 定义（与后端 Pydantic models 对齐） | 8 个 API response type；编译通过 |
| C-03 | TanStack Query hooks（8 个 API） | loading/error/data 三态覆盖 |
| C-04 | Layout + 侧边栏导航 + 暗色模式切换 | 课程列表自动刷新；当前路由高亮 |
| C-05 | Dashboard 页 | 展示各科进度环、今日 due 数、最近错题、快速开始 CTA |
| C-06 | Course 页（资料列表 + 章节进度） | 表格展示 files.yaml 内容；操作入口按钮 |
| C-07 | Materials 页（拖拽上传 + 类型选择） | 上传 → 后端索引 → 列表刷新 |
| C-08 | Exam Analysis 页 | 展示 priorities 列表（weight 排序）、evidence tooltip、生成按钮 |
| C-09 | Plan 页 | 时间轴/任务列表；倒计时；「现在开始」大按钮 → 跳转 Quiz |
| C-10 | Quiz Session 页 | 单题 → 输入 → 提交 → ScoreCard 翻转 → RatingButton → 下一题 |
| C-11 | CommandPalette（Cmd+K） | 搜索课程、快速导航、快捷命令 |
| C-12 | EmptyState 组件 | 每个页面空数据时有引导 CTA（而非白屏） |
| C-13 | 响应式布局（桌面优先） | 1280px+ 优化；768px 可用；移动端暂不强求 |
| C-14 | 加载骨架屏（Skeleton） | Dashboard 卡片、列表行、Quiz 题目区 |
| C-15 | 错误边界 + 网络断连提示 | API 失败 → toast 错误 + 重试按钮；不白屏 |
| C-16 | F1–F7 性能达标验证 | Lighthouse + React Profiler 实测 |

#### 前端交付效果检查清单

- [ ] 首屏 1.2s 内有内容
- [ ] 暗色模式切换无闪烁
- [ ] Cmd+K 能搜到所有课程和操作
- [ ] 上传资料 → 分析 → 出题 → 计划 → 答题 → 判分，全程不超过 5 次点击
- [ ] 错题卡片翻转动效 ≤200ms（60fps）
- [ ] 空状态有引导而非空白
- [ ] 断网时 toast 提示 + 已有数据仍然可见（TanStack Query cache）

---

### v1.0：可用期末复习产品 `验收项`

**启动条件**：v0.5 全部页面可用，F1–F7 达标。

- [ ] 至少 3 门课真实跑通完整复习流程
- [ ] 每门课完成：资料登记 → 试卷分析 → 变式题 → 计划 → 错题复查
- [ ] 输出内容可追溯到本地资料（evidence 链完整）
- [ ] 用户不需要理解仓库结构或 CLI 命令
- [ ] 从打开浏览器到开始答第一题 ≤2 分钟

### P2：后续增强 `估 ~8 条`

| 项目 | 进入条件 | 说明 |
|------|----------|------|
| Anki 导出 | cards.yaml ≥50 张 | 导出为 Anki apkg |
| FSRS 调度 | cards ≥200 张 + 用户每天复习 | 替代 D+1/D+3/D+7 |
| PPT/PDF 全文抽取 | 手动分类太慢 | Marker / PyMuPDF |

v0.3 启动条件：MVP 清单 M1–M10 全部打勾。

---

## Phase 3 预览：v1.5 商业化 `估 ~25 条`

**启动条件**：v1.0 验收通过（见上 § v1.0）。  
**产品定义**：`PRODUCT_ARCHITECTURE.md` § 10–11。  
**技术定义**：`FULLSTACK_AGENT_ARCHITECTURE.md` § SaaS。

> 现在不拆细项；MVP 55 完成前勿启动本 Phase。

| Epic | 估任务数 | 概要 |
|------|----------|------|
| P3-E1 账号认证 | ~6 | 注册/登录、JWT、密码重置、`/auth/*` |
| P3-E2 订阅支付 | ~6 | Stripe/微信、webhook、订阅状态机、付费墙 |
| P3-E3 对话 UI | ~5 | Chat 页、SSE 流式、结构化卡片、双模式（按钮+NL） |
| P3-E4 上传队列 | ~4 | 对象存储、异步 indexing、状态机 UI |
| P3-E5 设置与账单页 | ~4 | `/settings`、`/settings/billing`、用量展示 |

**v1.5 验收里程碑**：

- [ ] 用户可注册登录并看到个人 Dashboard
- [ ] 免费层额度用尽时显示付费墙且可完成支付
- [ ] 支付后分析/计划/生成题额度即时解锁
- [ ] 对话页可自然语言触发计划/分析/练习
- [ ] 用户资料与 review 数据按 workspace 隔离

---

## Phase 4 预览：v2.0 SaaS 上线 `估 ~20 条`

**启动条件**：v1.5 付费转化验证（至少 N 付费用户或校园试点意向）。  
**产品定义**：`PRODUCT_ARCHITECTURE.md` § 4、§ 14 v2.0。

| Epic | 估任务数 | 概要 |
|------|----------|------|
| P4-E1 多租户 | ~5 | workspace、成员角色、数据隔离审计 |
| P4-E2 校园套餐 | ~5 | 机构码、批量开通、SSO 对接 |
| P4-E3 运营后台 | ~4 | 用户/订阅/用量/admin 面板 |
| P4-E4 生产部署 | ~4 | PG 迁移、监控告警、备份恢复 |
| P4-E5 合规与信任 | ~2 | 隐私政策、数据导出/删除、AI 免责 |

**v2.0 验收里程碑**：

- [ ] 多 workspace 数据隔离测试通过
- [ ] 校园机构码可批量开通 50+ 账号
- [ ] 生产环境 7 天无 P0 故障
- [ ] 用户可一键导出并删除全部数据

---

## 工程质量与交付标准（全版本适用）

以下标准横跨 v0.2–v1.0，每个阶段达到对应等级即可，不需 MVP 阶段就全部满足。

### 1. 数据完整性与灾备

**原则**：用户的复习数据（错题、卡片、进度）是**不可再生资产**。代码可以重写，数据丢了就是丢了。

| # | 标准 | 适用版本 | 说明 |
|---|------|----------|------|
| D1 | YAML schema 校验 | v0.2 | `review_io.load_yaml` 后对必填键做存在性检查；缺键 WARN + 填默认值 |
| D2 | 写入前 Dry-run 确认 | v0.2 | 覆盖已有文件的操作（`--force`）必须打印 diff 摘要，等用户确认 |
| D3 | `cards.yaml` 自动备份 | v0.3 | 每次 `append_card` 前 copy 到 `cards.yaml.bak`；保留最近 3 个 bak |
| D4 | 数据完整性检查脚本 | v0.4 | `scripts/check_integrity.py`：扫描所有 `review/`，检查 ID 唯一性、due 日期合法性、必填字段、cross-file 一致性（mistake-log 的 topic 在 cards 中有对应） |
| D5 | Schema 迁移工具 | v0.4 | 当 `schema_version` 升级时，提供 `scripts/migrate.py --from 1 --to 2` |
| D6 | 导出/导入 | v1.0 | 一键导出所有课程 review 数据为 `.zip`；支持导入恢复 |

### 2. 错误预算与可靠性

**原则**：期末考试前夜系统崩了是不可接受的。定义清楚什么场景下系统必须正常工作。

| # | 标准 | 阈值 | 适用版本 |
|---|------|------|----------|
| R1 | CLI 脚本 crash 率 | 0% | v0.2（每个脚本在 fixture 上连跑 20 次无 crash） |
| R2 | 坏输入不 crash | 100% | v0.2（非法参数 → exit 1 + 有用报错；不 traceback） |
| R3 | API 5xx 率 | ≤1% | v0.4（1000 次请求统计） |
| R4 | Agent 错误工具调用 | ≤5% | v0.3（35 eval 中选错工具的比例） |
| R5 | 判分严重错误率 | ≤5% | v0.3（correct 判成 wrong 或反之；partial↔wrong 不算严重） |
| R6 | 数据丢失事件 | 0 | v1.0（任何操作都不能导致已有 cards/progress/mistake-log 消失） |

### 3. 安全审计清单

**原则**：虽然是本地工具，但脚本接受用户输入（课程路径、答案文本、文件名），必须防注入和路径遍历。

| # | 检查项 | 适用版本 | 说明 |
|---|--------|----------|------|
| S1 | 路径遍历防护 | v0.2 | 所有接受路径参数的脚本：`course_path` resolve 后必须在 workspace 内或用户明确指定的目录内 |
| S2 | subprocess 注入防护 | v0.2 | 复杂参数走临时 JSON 文件传参（TD-6），不拼接 shell 命令 |
| S3 | YAML 反序列化安全 | v0.2 | 只用 `yaml.safe_load`，禁止 `yaml.load`（可执行任意 Python 代码） |
| S4 | 无硬编码密钥 | v0.2 | `.env` 在 `.gitignore`；LLM API key 只从环境变量读 |
| S5 | 前端 XSS 防护 | v0.5 | 用户答案渲染用 React 默认转义（不 `dangerouslySetInnerHTML`）；Markdown 渲染用 `remark`/`marked` sanitize |
| S6 | Source policy 审计点 | v0.3 | Agent 输出的每个 course-content claim 必须有 `source_basis`；validator 检查 |
| S7 | 依赖漏洞扫描 | v0.4 | `pip-audit` + `npm audit` 加入 CI；critical CVE → 阻止 merge |

### 4. 可访问性 (a11y)

**原则**：复习工具的核心操作（答题、判分、导航）必须键盘可达。色彩不应该是传达信息的唯一方式。

| # | 标准 | 阈值 | 适用版本 |
|---|------|------|----------|
| A11 | 答题全流程键盘可达 | Tab → 输入 → Enter 提交 → 判分 → Enter 下一题 | v0.5 |
| A12 | 判分三态区分不依赖颜色 | correct = ✓ + 绿色、partial = △ + 黄色、wrong = ✗ + 红色（图标 + 颜色双重编码） | v0.5 |
| A13 | 焦点管理 | 判分后焦点自动移到「下一题」按钮；Modal 打开时焦点 trapped | v0.5 |
| A14 | 颜色对比度 | WCAG AA（正文 4.5:1，大文本 3:1） | v0.5 |
| A15 | 屏幕阅读器友好 | 评分按钮有 `aria-label`；进度条有 `aria-valuenow`；动态内容有 `aria-live` | v0.5 |
| A16 | `prefers-reduced-motion` | 翻转动效、骨架屏动画在用户设置了减少动效时禁用 | v0.5 |

### 5. 可观测性

**原则**：Agent 决策不应该是黑箱。用户和开发者都应该能理解"系统为什么做了这个选择"。

| # | 标准 | 适用版本 | 说明 |
|---|------|----------|------|
| O1 | 脚本 `--verbose` 模式 | v0.2 | `--verbose` 打印：读取了哪些文件、匹配了哪些关键词、生成了哪些 ID |
| O2 | Agent 决策日志 | v0.3 | 每次 `POST /agent/run` 写入 `review/agent-runs.yaml`：`{run_id, timestamp, intent, state_before, tool_called, state_after, warnings}` |
| O3 | 判分 trace | v0.3 | LLM 判分时记录：prompt（截断）、response、latency_ms、fallback_used |
| O4 | 前端分析埋点 | v0.5 | 可选匿名：页面 PV、答题耗时、判分分布、功能使用率（本地存储，不上报） |
| O5 | 错误聚合 | v0.4 | 相同类型错误 5 分钟内不重复打印（防日志爆炸） |

### 6. 代码质量门禁

**原则**：代码风格和类型安全不靠 Code Review 人肉检查，靠工具自动拦。

| # | 标准 | 工具 | 适用版本 | 阻断级别 |
|---|------|------|----------|----------|
| CQ1 | Python type coverage ≥80% | `mypy --strict` (逐步) | v0.2 | WARN |
| CQ2 | Python lint 零错误 | `ruff check` | v0.2 | 阻断 commit |
| CQ3 | TypeScript strict mode | `tsconfig.json strict: true` | v0.5 | 阻断 CI |
| CQ4 | ESLint 零 error | `eslint --max-warnings 0` | v0.5 | 阻断 CI |
| CQ5 | Prettier 格式化 | `prettier --check` | v0.5 | 阻断 CI |
| CQ6 | 圈复杂度上限 | 单函数 ≤15 | v0.2 | WARN（不阻断） |
| CQ7 | 文件行数上限 | 单文件 ≤400 行 | v0.2 | WARN（不阻断） |

### 7. CI/CD 流水线

**原则**：Push 后自动验证，不靠人工记忆。

```text
Git Push
  → Pre-commit: ruff + prettier
  → CI:
      1. Python unittest (v0.2+)
      2. mypy type check (v0.2+)
      3. ruff lint (v0.2+)
      4. Agent eval (v0.3+, 7 scenarios)
      5. API integration tests (v0.4+)
      6. Frontend build + lint + type check (v0.5+)
      7. Lighthouse CI (v0.5+, F1-F4 阈值)
  → PR: 所有 CI 绿 + 1 review → merge
```

| # | 标准 | 适用版本 |
|---|------|----------|
| CI1 | Pre-commit hook：ruff + prettier --write | v0.2 |
| CI2 | GitHub Actions：unittest on push | v0.2 |
| CI3 | GitHub Actions：agent eval on push | v0.3 |
| CI4 | GitHub Actions：Lighthouse CI | v0.5 |
| CI5 | PR 模板：checklist（测试跑了？文档更新了？E2E 过了？） | v0.2 |

### 8. Git 规范与发布流程

| # | 标准 | 适用版本 | 说明 |
|---|------|----------|------|
| G1 | Conventional Commits | v0.1 | `feat:` / `fix:` / `docs:` / `test:` / `refactor:` / `chore:` |
| G2 | 分支策略 | v0.2 | `main` 保护分支；feature 分支 `feat/xxx`；PR merge（不直接 push） |
| G3 | 版本号语义 | v0.2 | `v{major}.{minor}.{patch}`；CLI `--version` 打印版本号 |
| G4 | CHANGELOG.md | v0.2 | 每个版本手写 3-6 条要点（不自动生成——保留人工判断哪些值得写） |
| G5 | Git tags | v0.2 | 每个 release 打 annotated tag：`git tag -a v0.2.0 -m "..."` |

### 9. 浏览器与运行环境支持

| # | 标准 | 适用版本 | 说明 |
|---|------|----------|------|
| E1 | Python 版本 | v0.2 | 3.10+（3.10 是 `str | None` 语法的最低版本） |
| E2 | 操作系统 | v0.2 | Windows 10/11 + macOS 13+；Linux 尽力兼容（不阻塞） |
| E3 | 浏览器 | v0.5 | Chrome 120+、Edge 120+、Safari 17+、Firefox 125+ |
| E4 | Node 版本 | v0.5 | Node 20 LTS+ |
| E5 | 终端 | v0.2 | Windows Terminal、macOS Terminal、iTerm2；cmd.exe 尽力兼容 |

### 10. 前端工程化补充

| # | 标准 | 阈值 | 适用版本 |
|---|------|------|----------|
| FE1 | JS bundle size（gzip） | 首页 ≤150KB | v0.5 |
| FE2 | 路由级代码分割 | 每页独立 chunk | v0.5 |
| FE3 | 图片/图标优化 | SVG icon 用 `lucide-react`；无位图 > 100KB | v0.5 |
| FE4 | 暗色模式 | CSS variables + Tailwind `dark:` + 系统偏好检测 + 手动切换 | v0.5 |
| FE5 | Loading 状态 | 每个 API 调用有 skeleton/disabled 状态；无闪烁 | v0.5 |
| FE6 | 乐观更新 | 评分提交先更新 UI，请求失败回滚（TanStack Query `onMutate`） | v0.5 |

### 11. 各阶段质量检查清单

这份清单在进入下一阶段前逐项打勾。不打勾不进入下一阶段。

#### v0.2 质量门

- [ ] `python -m unittest` 全绿
- [ ] 6 步命令链在 fixture 上 exit 0
- [ ] `due_today` 坏 YAML 容错通过
- [ ] `init` 重复运行安全
- [ ] 所有脚本 `--help` 可读、无错别字
- [ ] `ruff check` 零错误
- [ ] 无 `print(traceback)` 裸异常——所有错误走 `sys.exit(1)` + stderr 描述
- [ ] Q1–Q12 实测值填入并全部达标
- [ ] tasks.md 进度总览表更新

#### v0.3 质量门

- [ ] A1–A8 全部达标
- [ ] 7 条 agent eval 自动化
- [ ] Source policy 无违规
- [ ] Agent 日志写入 `agent-runs.yaml`
- [ ] LLM 判分延迟 P95 ≤8s
- [ ] 无幻觉工具调用

#### v0.4 质量门

- [ ] P1–P6 全部达标
- [ ] `/openapi.json` 与 Pydantic models 一致
- [ ] API 集成测试覆盖率 ≥80%
- [ ] 数据完整性检查脚本可用

#### v0.5 质量门

- [ ] F1–F7 全部达标
- [ ] C-01 到 C-16 全部完成
- [ ] Lighthouse score ≥90（Performance / Accessibility / Best Practices）
- [ ] 键盘可达答题全流程
- [ ] 暗色模式无样式异常
- [ ] Bundle size ≤150KB gzip
- [ ] 前端交付效果检查清单全部打勾

#### v1.0 质量门

- [ ] 3 门真实课程跑通
- [ ] 新用户 2 分钟内能开始答第一题
- [ ] 0 数据丢失事件

### 12. 不在任何阶段做的（明确排除）

这些是刻意不做的，防止 scope creep：

- **用户账号/OAuth**：本地工具，不需要登录
- **移动端 App**：桌面优先，移动端不强求
- **多人协作**：个人复习工具，不做共享
- **实时同步**：数据在本地文件系统，不同步到云
- **付费/订阅**：开源项目，不接入支付
- **社交功能**：不做排行榜、分享、学习小组
- **语音输入/朗读**：文本交互够用
- **数学公式渲染**：题目中出现 LaTeX 时用纯文本描述（v1.0 后再考虑 KaTeX）

---

## 任务粒度说明

- **68 条** = 全仓库任务
- **55 条 MVP** = 闭环可验收的最小集合
- **12 条 v0.2** = 工程质量（测试、文档、打磨）
- **1 条可选** = 真实课程

每条任务包含：层级标签 + 目标 + 验收 + 输入输出 + 技术决策 + 跨任务契约 + 已知陷阱 + 不做边界。
