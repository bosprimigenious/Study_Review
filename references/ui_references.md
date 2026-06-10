# UI References

Study Review 前端视觉与交互的对标清单。不限于 NovaOrbit，聚焦 2025–2026 年主流「大厂简约现代」工作台写法：设计 token + 无头组件 + 少量动效。

相关文档：

- 技术栈选型：`references/tech_stack.md`
- 页面与组件任务：`tasks.md`（v0.5 前端章节）
- 产品节奏对标：`PRODUCT_ARCHITECTURE.md` §16

---

## 设计方向（一句话）

```text
Notion 的克制排版
+ Linear 的响应速度
+ Vercel 的设计语言
+ shadcn/ui 的组件质量
```

不是花哨 dashboard，是**让人想每天打开的工具**。主屏优先「今晚一个动作」，而非浏览型数据墙。

---

## 一、共识技术栈（2025–2026）

几乎所有现代 SaaS / 工作台都在用同一条线：

| 层 | 主流选择 | 作用 |
|---|---|---|
| 样式 | Tailwind CSS v4 + CSS Variables | 间距、颜色、暗色模式全走 token |
| 组件 | shadcn/ui（底层 Radix UI） | Button、Dialog、Sidebar、Command、Form… |
| 图标 | lucide-react | 统一线宽，贴近 Linear / Vercel |
| 命令面板 | cmdk | Cmd+K 全局导航（Raycast / Linear 感） |
| 提示 | sonner | 轻量 Toast |
| 表单 | React Hook Form + Zod | 与后端 Pydantic schema 对齐 |
| 服务端状态 | TanStack Query | 列表 / 缓存 / loading 三态 |
| 表格 | TanStack Table | 资料列表、错题表 |
| 图表 | recharts 或 Tremor | 克制的小卡片图，避免大屏 BI |
| 动效 | framer-motion 或纯 CSS | 翻转卡、入场 150–300ms |
| 主题 | next-themes（或自写） | 亮 / 暗切换 |

### 标准写法（不是装一个 UI npm 包）

```bash
npx shadcn@latest add button dialog sidebar command
```

组件源码落在 `components/ui/`，用 Tailwind + CSS 变量改样式。Study Review 当前路径：`apps/web/src/components/ui/`。

### Study Review 已落地 / 待补齐

| 能力 | 状态 | 本仓库位置 |
|---|---|---|
| shadcn 基础组件 | ✅ | `apps/web/src/components/ui/` |
| Zod + API | ✅ | `apps/web/src/lib/schemas.ts`, `api.ts` |
| sonner Toast | ✅ | 全局挂载 |
| 翻转卡 + 四档评分 | ✅ | `QuizCard.tsx`, `RatingButton.tsx` |
| 语义字号 token | ✅（持续微调） | `apps/web/src/index.css` |
| TanStack Query | 待接满 | Sprint 3 |
| cmdk CommandPalette | 待做 | Sprint 3 |
| react-dropzone | 待做 | Materials 页 |
| framer-motion | 可选 | 当前以 CSS 为主 |

---

## 二、开源参考：分三类抄

### 2.1 工作台壳子（Admin / Dashboard 模板）

最适合抄：侧栏、顶栏、Dashboard 卡片、目录结构。

| 项目 | Stars | 学什么 | Demo / 仓库 |
|---|---|---|---|
| [next-shadcn-dashboard-starter](https://github.com/Kiranism/next-shadcn-dashboard-starter) | ~6.5k | 侧栏+顶栏、多主题、Analytics 卡片、feature 目录 | [Demo](https://dub.sh/shadcn-dashboard) |
| [next-shadcn-admin-dashboard](https://github.com/arhamkhnz/next-shadcn-admin-dashboard) | ~2.5k | **更干净**，多套 theme preset，少 clutter | [Demo](https://next-shadcn-admin-dashboard.vercel.app) |
| [shadcn-admin](https://github.com/satnaing/shadcn-admin) | 经典 | Cmd+K、可折叠侧栏、表格页范式 | 仓库 README |
| [square-ui](https://github.com/ln-dev7/square-ui) | — | 多套 dashboard 布局，偏设计稿级 | [模板列表](https://github.com/ln-dev7/square-ui) 各模板独立 Demo |
| [Circle](https://github.com/ln-dev7/circle) | — | **仿 Linear**：issue 列表、键盘流、极简灰阶 | [circle.lndev.me](https://circle.lndev.me) |

**建议抄的文件类型（通用）：**

```text
src/components/layout/     # 侧栏 + 顶栏 + content area
src/components/ui/sidebar  # shadcn Sidebar 用法
src/features/              # 按功能分目录，而非按组件类型堆
src/styles/themes.css      # CSS 变量 / preset
```

---

### 2.2 真产品（学 UX 节奏，不只抄皮）

比模板更值得学：**信息架构、步骤流、空状态、键盘流**。

| 产品 | 前端栈 | 简约感从哪来 | 适合 Study Review 学什么 |
|---|---|---|---|
| [Cal.com](https://github.com/calcom/cal.com) | Next.js monorepo，`@calcom/ui` + Tailwind | 留白大、步骤清晰、几乎无装饰背景 | 设置流、状态页、克制表单 |
| [Documenso](https://github.com/documenso/documenso) | Remix + `@documenso/ui`（Shadcn+Radix） | 上传→处理→完成，每步一个主 CTA | Materials 上传、解析状态 badge |
| [Plane](https://github.com/makeplane/plane) | React + Vite + `@plane/ui` + Tailwind | Linear 替代：键盘优先、干净 issue 行 | Plan 任务列表、侧栏密度、空状态 |
| [Taxonomy](https://github.com/shadcn-ui/taxonomy) | shadcn 作者 SaaS 范例 | 营销页 + Dashboard + 计费一整条 | 若以后做订阅 / 账号 |

**Plane 特别值得看：**

- `packages/ui` 用 Storybook 维护组件
- 语义 token：`border-subtle`、`text-secondary` 统一全站
- 不靠大面积渐变背景

**建议抄的文件类型：**

```text
packages/ui/               # 或 apps/web 内共享组件包
apps/web/app/(dashboard)/  # 工作台路由与布局
components/file-upload/    # Documenso 类上传状态机
```

---

### 2.3 学习 / 复习类产品（业务最接近）

| 项目 | 栈 | 学什么 |
|---|---|---|
| [Deckly](https://github.com/guanjunming/deckly) | Next + shadcn + TanStack Query + Drizzle | 间隔重复产品化：deck 列表、复习会话、表格 |
| [Flashy](https://github.com/byigitt/flashy) | Next + shadcn + next-themes | 干净闪卡 UI：暗色、toast、进度统计 |
| [flashcardswithaigrading](https://github.com/cameronmcginley/flashcardswithaigrading) | shadcn + Framer Motion + `@dnd-kit` | 翻转动画、四档评分驱动算法、侧栏拖拽 |
| [shadcn Dialog Flashcard block](https://www.shadcn.io/blocks/dialog-flashcard) | 官方 block | 翻转、进度条、掌握标记——可直接当 Quiz 参考 |

**学习类产品 UI 共性：**

```text
一屏一件事（当前这题 / 当前这套卡）
大字号题干
底部四档评分（忘了 / 困难 / 还行 / 很熟）
顶部细进度条
```

Anki / Quizlet 几十年验证的模式；NovaOrbit 学的是节奏，视觉应跟 shadcn 生态 + 上述闪卡项目。

---

## 三、「好看」的 7 条原则（比选库更重要）

开源项目表面栈差不多，观感差很多，差在 execution：

| # | 原则 | 做法 | 反例 |
|---|---|---|---|
| 1 | 字体 | Inter / Geist + **Noto Sans SC**；中文题干不用 mono | 题干用 JetBrains Mono |
| 2 | 字号刻度 | 全站 5–6 档 token（`type-page` 等语义 class） | 页面里随手 `text-xs` / `text-2xl` 混用 |
| 3 | 颜色 | 灰阶底 + 一个 accent + 语义色（绿/黄/红仅状态） | 彩虹渐变、大面积光晕网格 |
| 4 | 边框 | 1px `border` + 轻 shadow | 粗边框 + 重阴影卡片墙 |
| 5 | 密度 | 侧栏窄、主区宽；卡片 `p-4` / `p-6` 一致 | 营销页式大 hero + 小字正文 |
| 6 | 动效 | 150–300ms `ease-out`；hover 微抬升；翻转 ≤400ms | 弹跳、长动画、装饰背景动效 |
| 7 | 键盘流 | Enter 提交 → 评分 → 下一题；Cmd+K 跳页 | 全靠鼠标点按钮 |

Linear / Raycast / Notion **没有**完整开源 UI 库；**Circle、Plane、shadcn-admin** 把它们的模式拆成了可抄代码。

---

## 四、与 NovaOrbit 的对齐策略

NovaOrbit 学**产品节奏**，视觉和组件层跟 **shadcn 生态 + Linear 系 clone**。

| 维度 | NovaOrbit | 更建议对齐 |
|---|---|---|
| 整体气质 | AI 学习架构师、图谱感 | Plane / Circle（任务工作台） |
| Dashboard | 浏览型 | Cal.com / Vercel Analytics（一张主行动卡片） |
| 复习卡 | 闪卡 | Anki 交互 + shadcn flashcard block |
| 全局导航 | — | Raycast → cmdk |
| 资料流 | 上传解析 | Documenso 上传→状态→就绪 |

从 NovaOrbit 保留的体验节奏（见 `PRODUCT_ARCHITECTURE.md`）：

- 轻量首屏：Dashboard 直接显示「今日 1 个动作」
- 判分后自动追问，可跳过
- 卡片翻转 ≤200ms 感知；四档评分
- 每页空状态有「下一步」CTA

---

## 五、按页面：该抄谁

与 `tasks.md` 路由清单对齐。

| 页面 | 路由 | 优先抄 | 具体看什么 |
|---|---|---|---|
| **Dashboard** | `/` | Cal.com 状态页、Vercel Analytics 卡片、Circle 收件箱 | 单主 CTA「开始今晚复习」；due 数字 badge；最近错题 3 条预览，不要满屏图表 |
| **Course** | `/course/:id` | Notion database view、Plane 项目概览 | 资料表格 + 类型标签；每行一个主操作（分析/出题/计划/练习） |
| **Materials** | `/course/:id/materials` | Documenso 上传流、shadcn-admin 表格页 | `react-dropzone` + 类型确认下拉；解析中 / 就绪 badge；批量操作放次要位置 |
| **Exam Analysis** | `/course/:id/analysis` | Notion 分栏、shadcn Accordion | 按 weight 排序的优先级列表；evidence tooltip 链到源文件 |
| **Plan** | `/course/:id/plan` | Plane issue 列表、Linear 任务行 | 时间轴或 checklist；倒计时；「现在开始」唯一高亮按钮 |
| **Quiz Session** | `/course/:id/quiz` | Anki、shadcn flashcard block、Flashy | 单题全屏感；翻转判分；底部 RatingButton；顶栏细进度条 |
| **Layout（全局）** | — | shadcn-admin、next-shadcn-admin-dashboard | 可折叠侧栏、路由高亮、暗色切换 |
| **CommandPalette** | Cmd+K | Raycast、shadcn-admin `command` | 跳页 + 搜课程 + 「开始复习」快捷动作 |

### 公共组件 → 参考

| 组件 | 参考 | 本仓库 |
|---|---|---|
| `CommandPalette` | Raycast / shadcn-admin | 待建 |
| `DueBadge` | Linear inbox | 待建 |
| `RatingButton` | Anki 四档 | `RatingButton.tsx` ✅ |
| `ProgressRing` | Vercel Analytics | 待建 |
| `EvidenceTooltip` | shadcn Tooltip | `tooltip.tsx` ✅ |
| `ScoreCard` | Linear issue status 色 | `ScoreCard.tsx` ✅ |
| `MarkdownRenderer` | Obsidian 简洁渲染 | 待建 |
| `FileDropZone` | Documenso + react-dropzone | 待建 |
| `EmptyState` | Linear empty state | `EmptyState.tsx` ✅ |
| `QuizCard` | shadcn flashcard block | `QuizCard.tsx` ✅ |

---

## 六、最小抄作业清单（按性价比）

1. **布局壳**：[shadcn-admin](https://github.com/satnaing/shadcn-admin) 或 [next-shadcn-admin-dashboard](https://github.com/arhamkhnz/next-shadcn-admin-dashboard) → 侧栏 + 顶栏 + 暗色
2. **Linear 感**：[Circle](https://github.com/ln-dev7/circle) → issue 行、列表密度、键盘提示文案
3. **Cmd+K**：`cmdk` + shadcn `Command`（Sprint 3）
4. **Quiz**：[shadcn flashcard block](https://www.shadcn.io/blocks/dialog-flashcard) + Flashy 进度统计 + 现有 `QuizCard`
5. **上传页**：Documenso 文件状态流 + `react-dropzone`
6. **字体 / 刻度**：Plane `@plane/ui` token 思路——**只改 `index.css` 一处，全站跟随**

### 与当前实现的差距（Sprint 1–2 之后）

| 差距 | 优先级 |
|---|---|
| Cmd+K 全局导航 | P0 |
| 统一 type scale（少改单页字号） | P0 |
| 减少装饰背景（网格/光晕克制） | P1 |
| Dashboard 只突出「今晚一个动作」 | P0 |
| TanStack Query 接满 8 个 API | P1 |
| Materials 上传 + 状态 badge | P1 |

---

## 七、闭源标杆（无代码可抄，学交互）

| 产品 | 学什么 | 链接 |
|---|---|---|
| **Linear** | 键盘快捷键、行内编辑、微交互、灰阶 | [linear.app](https://linear.app) |
| **Notion** | 侧栏导航、slash command、database view | [notion.so](https://notion.so) |
| **Vercel** | 克制配色、Analytics 小卡片、几乎无装饰 | [vercel.com](https://vercel.com) |
| **Raycast** | 命令面板、无鼠标流、动作列表 | [raycast.com](https://raycast.com) |
| **Anki** | 复习卡、翻转动效、四档评分 | [apps.ankiweb.net](https://apps.ankiweb.net) |
| **Quizlet** | Learn 模式、进度条、模式切换 | [quizlet.com](https://quizlet.com) |
| **Obsidian** | 本地文件感、Markdown 渲染克制 | [obsidian.md](https://obsidian.md) |

---

## 八、修订记录

| 日期 | 说明 |
|---|---|
| 2026-06-10 | 初稿：共识栈、三类开源参考、7 条原则、按页抄作业清单 |
