# ResearchPilot 2.0 升级规划：从任务管理工具到科研工作台

| 项目 | 内容 |
| --- | --- |
| 文档版本 | v1.0（待审核） |
| 编写日期 | 2026-11-11 |
| 状态 | 规划稿，等待审核；未修改任何业务代码 |
| 适用范围 | ResearchPilot 预赛反馈整改 + 决赛功能升级 |

---

## 0. 一句话回应评委意见

> 评委意见：科研过程不像工程项目那样容易通过任务管理解决；产品思路不错，但没有清楚展示系统具体解决了什么科研问题。

**回应**：ResearchPilot 1.0 的骨架（项目/任务/风险/重规划）是"科研项目的时间管理工具"，它管理的是科研的**排期**，不是科研的**内容**。2.0 将把系统的重心从"任务看板"前移到科研工作的真实载体上——**研究问题、文献证据、实验设计与运行记录、结果分析、研究决策**——任务看板退居为这些科研实体的"执行出口"。系统回答的核心问题从"你延期了吗"变为：**"你的研究现在知道了什么、还缺什么证据、下一步该做什么实验、为什么。"**

2.0 核心闭环：

```
研究问题 → 文献证据(结构化卡片) → 实验设计 → 实验运行记录(真实数据)
    ↑                                        │
    └── 转为科研任务(看板/周报) ← 下一步研究决策 ← 结果分析(基于真实记录)
```

---

## 1. 现状盘点（基于逐文件通读代码，非文件名推断）

审计日期 2026-11-11。审计方式：通读全部后端路由/服务/模型、前端页面/组件/API 层、测试与文档。**本次审计受运行权限限制，未实际启动服务重跑测试**（见 §1.4 验证说明）。

### 1.1 前端（React 19 + TypeScript + Vite 7 + Tailwind 4 + shadcn/ui + Recharts）

| 页面/组件 | 文件 | 实际内容 |
| --- | --- | --- |
| 首页仪表盘 | [HomePage.tsx](../frontend/src/pages/HomePage.tsx) | 统计卡片、项目列表、风险提醒、7 天完成趋势图、状态分布环形图，全部来自 `GET /api/home` |
| 新建项目 | [CreateProjectPage.tsx](../frontend/src/pages/CreateProjectPage.tsx) | 表单 → AI 计划预览（演示模式徽章/警告）→ 确认写入，或跳过 AI 直接创建 |
| 任务看板 | [BoardPage.tsx](../frontend/src/pages/BoardPage.tsx)、[ProjectBoard.tsx](../frontend/src/components/board/ProjectBoard.tsx)、[TaskFormSheet.tsx](../frontend/src/components/board/TaskFormSheet.tsx) | 三列看板、状态流转、新增/编辑抽屉、进度条、风险标记、里程碑徽章 |
| 项目详情 | [ProjectDashboardPage.tsx](../frontend/src/pages/ProjectDashboardPage.tsx) | 项目信息卡 + 风险横幅 + 4 个 Tab：任务看板 / 文献库 / 汇报中心 / 重规划 |
| 文献库 Tab | [DocumentLibraryTab.tsx](../frontend/src/components/documents/DocumentLibraryTab.tsx)、[DocumentQaPanel.tsx](../frontend/src/components/documents/DocumentQaPanel.tsx) | PDF 上传、文献列表、切片原文（点击引用跳转）、AI 问答（引用+置信度）、保存笔记 |
| 汇报中心 Tab | [ReportCenterTab.tsx](../frontend/src/components/reports/ReportCenterTab.tsx) | 组会周报/导师汇报生成、Markdown 渲染、编辑保存、复制、导出 .md |
| 重规划 Tab | [ReplanTab.tsx](../frontend/src/components/replan/ReplanTab.tsx) | 风险预警列表、生成方案、原计划 vs 新计划对比表（改动高亮）、采纳/放弃、历史留档 |
| 周报页 | [WeeklyReportPage.tsx](../frontend/src/pages/WeeklyReportPage.tsx) | 近 7 天活动聚合统计 + AI 周报生成 + 复制 |
| API 层 | [api.ts](../frontend/src/services/api.ts) | 32 个接口函数，与后端路由一一对应；axios 统一错误转中文 toast |

**结论：前端无"仅有界面"的功能**。M2 时期的模拟静态数据已全部被真实 API 替换；`PagePlaceholder` 仅用于 404 页。

### 1.2 后端（FastAPI + SQLAlchemy 2 + SQLite）

| 路由文件 | 端点 | 功能 |
| --- | --- | --- |
| [projects.py](../backend/app/routers/projects.py) | `/api/projects` CRUD | 项目增删改查，返回实时进度/风险/剩余天数 |
| [tasks.py](../backend/app/routers/tasks.py) | `/api/tasks` CRUD + `/tasks/{id}/progress` | 任务增删改、状态↔进度联动、进度记录（历史只增不删） |
| [home.py](../backend/app/routers/home.py) | `GET /api/home` | 首页聚合：统计/风险任务/趋势/分布 |
| [ai.py](../backend/app/routers/ai.py) | `POST /api/ai/plan`、`/api/ai/plan/confirm` | 计划草稿生成（不落库）→ 确认后原子写入项目+任务 |
| [documents.py](../backend/app/routers/documents.py) | 文献上传/列表/详情/删除、问答、笔记 | PDF 文字提取+切块、top5 检索问答（引用溯源）、笔记保存 |
| [reports.py](../backend/app/routers/reports.py) | 汇报生成/历史/编辑/导出 .md | 组会周报与导师汇报，Markdown |
| [report.py](../backend/app/routers/report.py) | `GET /api/report/weekly`、`POST /api/report/weekly/generate` | 周报活动聚合 + AI 周报正文 |
| [replans.py](../backend/app/routers/replans.py) | 重规划生成/采纳/放弃/历史 | 采纳后把调整应用到任务表（reschedule/reprioritize） |

服务层：[risk.py](../backend/app/services/risk.py)（4 条本地风险规则：逾期/前置阻塞/进度落后/工时不足，纯规则零 token）、[ai_planner.py](../backend/app/services/ai_planner.py)（严格 JSON Prompt + 格式重试 + 演示模式）、[document_service.py](../backend/app/services/document_service.py)（pypdf + jieba + 引用校验防编造）、[replan_service.py](../backend/app/services/replan_service.py)、[meeting_report.py](../backend/app/services/meeting_report.py)、[report.py](../backend/app/services/report.py)、[home.py](../backend/app/services/home.py)。

AI 客户端 [ai_client.py](../backend/app/ai_client.py)：DeepSeek 单点封装，401/402/429/超时全部映射中文提示；所有 AI 功能在无 Key 时降级为明确标注的演示模式。

### 1.3 数据库（[models.py](../backend/app/models.py)，实际 8 张表）

`project`、`task`（自关联 parent_id 表示前置/里程碑）、`progress_record`、`replan_history`、`document`、`doc_chunk`、`doc_qa`、`reports`。

> ⚠️ 现状问题①：README 与 models.py 文档字符串声称"10 张表"，实际 8 张，需修正文档。

### 1.4 测试与启动

- **测试**：仅 [smoke_test.py](../backend/smoke_test.py)（36 项接口冒烟：健康检查、项目/任务 CRUD 与校验、状态联动、进度记录、首页聚合、风险引擎、级联删除、GBK 编码防护）。**无 pytest、无单元测试、无前端测试**（package.json 无 test 脚本，仅 oxlint）。
- **启动**：后端 `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`；前端 `npm run dev`（Vite 代理 /api 到 8000，已规避 Chrome PNA 跨域）。
- **验证说明**：冒烟测试覆盖项目/任务/进度/风险/首页；AI 类功能无自动化测试。README 声称 36 项全过，但**本次审计未重跑**（会话运行权限受限），以下状态标注以此为据。

### 1.5 功能验证状态矩阵

| 功能 | 状态 | 依据 |
| --- | --- | --- |
| 项目 CRUD + 校验（中文 422 提示） | ✅ 已实现且已验证 | smoke 2.1–2.6、3.1–3.3、9.x；路由+schemas 通读确认 |
| 任务 CRUD + 状态/进度联动 | ✅ 已实现且已验证 | smoke 4.1–4.6、5.1–5.7 |
| 进度记录（历史曲线） | ✅ 已实现且已验证 | smoke 6.1–6.4 |
| 风险识别引擎（4 条本地规则） | ✅ 已实现且已验证 | smoke 8.1–8.3；规则代码通读确认 |
| 首页聚合仪表盘 | ✅ 已实现且已验证 | smoke 7.2 |
| 健康检查/异常处理/GBK 防护 | ✅ 已实现且已验证 | smoke 1.1、2.6 |
| AI 科研计划生成（DeepSeek+demo 双模式） | ✅ 已实现但未验证 | 代码完整（严格 JSON+重试+校验），**无测试覆盖**，实际效果依赖 Key，本次未实机调用 |
| 动态重规划（生成/采纳/放弃/历史） | ✅ 已实现但未验证 | 代码完整，**无测试覆盖** |
| PDF 文献问答（提取/切块/检索/引用溯源/笔记） | ✅ 已实现但未验证 | 代码完整（含防编造引用校验），**无测试覆盖** |
| 周报生成 + 汇报中心 | ✅ 已实现但未验证 | 代码完整，**无测试覆盖** |
| 仅有界面的功能 | — **无** | 所有 UI 均接入真实后端 API |
| 研究问题管理 | ❌ 尚未实现 | 无此实体 |
| 结构化文献证据（卡片化、可对比） | ❌ 尚未实现 | 文献问答是对话式的，不沉淀结构化字段 |
| 实验设计与运行记录 | ❌ 尚未实现 | 实验只是任务描述文本 |
| 结果比较 | ❌ 尚未实现 | 无结构化结果数据 |
| 基于真实实验记录的 AI 分析 | ❌ 尚未实现 | AI 只做拆解/重排/问答/写汇报 |
| 研究决策 → 任务闭环 | ❌ 尚未实现 | 任务无"科研来源"概念 |

> ⚠️ 现状问题②：`backend/venv/` 虚拟环境目录被提交进了 git（约 1.7MB 文件列表），应 `git rm -r --cached backend/venv` 并在 backend/.gitignore 中补充 `venv/`（当前只忽略了 `.venv/`）。此项不涉及业务代码。

---

## 2. 为什么当前系统更像工程任务管理工具

评委的意见是准确的。逐层分析：

**（1）数据模型里没有"科研对象"。** 核心实体只有 Project → Task → ProgressRecord，这是任何工程管理软件的通用骨架。文献、实验、结果、假设在系统里没有一等公民身份：实验是任务标题里的几个字，结果是进度备注里的自由文本。系统无法回答"你研究到什么了"。

**（2）任务依赖图错误地表达了科研过程。** AI 拆解输出的是"文献调研 → 方法设计 → 实验 → 写作"的单向前置链（见 [ai_planner.py](../backend/app/services/ai_planner.py) 的 Prompt 与演示模板）。但科研是探索性循环：实验结果会改变假设、推翻方法、引出新的文献调研。单向前置依赖链可以排期论文写作，但表达不了"阴性结果 → 换方法 → 新实验"这类科研最日常的路径。

**（3）风险识别只认识时间风险。** 四条规则（逾期/阻塞/进度落后/工时不足）全部是进度维度。科研最危险的风险不在排期里：实验结果不支持假设、复现失败、文献证据互相矛盾、方法行不通。这些风险当前系统完全看不见。

**（4）重规划只会改日期和优先级。** 采纳重规划只能 reschedule / reprioritize（见 [replans.py](../backend/app/routers/replans.py) adopt 逻辑）。而科研遇到问题时真正需要的"重规划"是：换实验方案、修正假设、缩小/调整研究问题、补充证据。

**（5）文献问答没有沉淀为证据。** 现有文献功能是"单篇对话 + 保存笔记"，问答记录散落在每篇 PDF 下。它回答"这篇论文说了什么"，但回答不了"这些论文放在一起，我的研究问题目前有多少证据支持、哪些方法被证明有效、哪些指标是领域标准"。笔记无法参与比较与决策。

**（6）汇报聚合的是任务数据，不是科研数据。** 周报/汇报中心的数据源是完成任务数、进度更新、投入小时（见 [meeting_report.py](../backend/app/services/meeting_report.py) `collect_project_data`）。一个"本周完成了 2 个任务、投入 8 小时"的周报，导师看不到"本周做了 3 组实验，模型在 X 数据集上从 82% 提升到 87%，但距离 SOTA 的 91% 还有差距，下一步计划消融实验"。

**（7）产品叙事围绕"管理"而非"研究"。** 首页第一句话是"今天也要稳步推进科研"（任务打卡语境），PRD 的核心痛点全部是拆解难/计划难/发现晚/调整难/无监督——这些是执行层痛点，不是科研层痛点。

**2.0 的升级方向**（保持原模块不动，在科研内容层补上缺失的实体与闭环）：

| 维度 | 1.0（工程视角） | 2.0（科研视角） |
| --- | --- | --- |
| 研究问题 | 写在项目 goal 里的一段话 | 独立实体，可关联证据与实验，状态可推进 |
| 文献 | 单篇 PDF + 对话问答 | 结构化证据卡片，字段级横向对比，标记支持/反对 |
| 实验 | 任务标题中的文字 | 设计+假设+多次运行记录+结构化结果，可比较 |
| 结果分析 | 进度备注 | 基于真实运行记录的 AI 解读+决策建议 |
| 决策 | 采纳/放弃重规划 | 分析结论可一键转为带来源的科研任务 |
| 风险 | 进度落后/逾期 | 保留时间风险，新增科研风险（停滞、假设受挫） |
| 周报 | 任务维度 | 追加实验进展与结论摘要 |

---

## 3. ResearchPilot 2.0 最小可行升级方案

### 3.1 设计原则

1. **不更换技术栈**：React + TypeScript + Vite / FastAPI + SQLite / DeepSeek 全部保留。
2. **不重写、不删除已工作模块**：1.0 的所有表、路由、页面原样保留；新功能以新表、新路由、新 Tab 形式叠加。
3. **科研不是工程任务**：实验、证据、问题都是一等实体；任务看板只是执行出口，不把科研过程塞进任务模型。
4. **不集成 GPU 训练执行平台**：实验执行发生在用户的实验室/服务器上，系统只做设计管理、结果记录与分析；结果由用户结构化录入。
5. **严禁伪造**：所有 AI 输出必须绑定真实录入数据（已上传文献、已录入实验记录），无数据时拒绝生成并提示；AI 内容标注来源、允许人工修改；不预置任何虚假论文/结果/测试数据。
6. **AI 仍是增强**：无 Key 时新模块同样有演示模式或纯手工模式，核心 CRUD 不依赖 AI。

### 3.2 核心闭环落点

| 闭环环节 | 2.0 落点 | 用户操作 |
| --- | --- | --- |
| 研究问题 | 新实体 `research_question` | 在项目下创建/回答/挂起问题 |
| 文献证据 | 新实体 `literature_card`（由已上传 PDF 经 AI 抽取 + 人工修正） | 上传文献 → 生成卡片 → 关联问题 → 标记证据立场 |
| 实验设计 | 新实体 `experiment`（目标/假设/方案/指标） | 从问题或分析建议创建实验 |
| 实验运行记录 | 新实体 `experiment_run`（条件/配置/结构化结果/附件） | 每次运行录入真实数据 |
| 结果分析 | 新服务 `experiment_analysis`（DeepSeek 基于真实 run 记录 + 卡片证据） | 点击"AI 分析" |
| 下一步研究决策 | 分析输出的结构化建议（新实验/新任务/补文献） | 一键转为任务 |
| 转为科研任务 | task 表新增来源字段 | 看板出现带"来源：实验分析"标记的任务 |

---

## 4. 三个新模块详细设计

### 4.1 模块 A：结构化文献研究卡片

**解决的问题**：把"读过的论文"变成"可比较、可引用、可决策的证据"。

**功能**：

1. **卡片生成**：对已上传的 PDF（复用现有上传/切块管线），用户点击"生成研究卡片"，后端把全文（或摘要+分段摘要）交给 DeepSeek，抽取严格 JSON 字段：
   - `title` / `authors` / `year`（若可提取）
   - `research_question`：该文研究的问题
   - `method`：方法简述
   - `materials_datasets`：数据集/材料/实验对象
   - `metrics`：使用的评价指标
   - `key_results`：主要结果（可多条）
   - `limitations`：作者自述或明显的局限
   - `relevance`：与我们研究问题的关联说明
   - `evidence_type`：support（支持我们的假设）/ against（反对）/ neutral（参考）
   - 抽取失败重试 2 次；无 Key 时演示模式返回字段模板并明确标注"请在卡片上手工填写"。
2. **人工修正**：所有字段可编辑保存（AI 抽取可能不准，最终以人确认为准；AI 来源标记 `source=deepseek`，手工改过标记 `source=manual`）。字段留空是合法状态——不允许 AI 编造填充。
3. **卡片对比**：在文献库中选择多张卡片（如 3~5 张），生成字段级横向对比表（研究问题/方法/数据集/指标/结果/局限逐行对齐），一眼看出方法差异与证据分布。对比为纯本地渲染，不调 AI。
4. **证据关联**：卡片挂到 `research_question`，并按 `evidence_type` 汇总——问题详情页显示"支持证据 n 条 / 反对证据 n 条 / 参考 n 条"。
5. **与现有 PDF 问答共存**：问答面板不动；卡片是问答之外的第二视图（Tab 内二级切换：原文问答 / 研究卡片）。

**反伪造约束**：卡片抽取的输入必须是数据库里真实存在的 `document`；抽取服务无文献记录可用时返回 400；每张卡片保留 `document_id` 溯源。

### 4.2 模块 B：实验管理与结果比较

**解决的问题**：实验不再是一句任务描述，而是一套可记录、可比较、可复盘的结构化数据。

**实体与字段**：

- `experiment`（实验）：
  - `title`、`objective`（实验目的）、`hypothesis`（假设，可空）
  - `design`（实验方案，Markdown 自由文本：变量、对照组、流程）
  - `metrics_json`（本实验关注的指标定义列表，如 `[{"name":"Accuracy","unit":"%","higher_is_better":true}]`）
  - `status`：draft（设计中）/ running（进行中）/ done（完成）/ failed（失败）/ paused（暂停）
  - 关联：`question_id`（回答哪个研究问题）、可选 `card_ids`（依据哪些文献设计）
- `experiment_run`（运行记录，一次实验的每次真实执行）：
  - `run_no`（第几次运行）
  - `config_json`（本次运行条件：模型/参数/数据/环境等自由键值）
  - `results_json`（结构化结果，按实验定义的指标名填写：`{"Accuracy": 87.3, "F1": 0.85, ...}`）
  - `notes`（现象、问题、观察，Markdown）
  - `attachments`（可选图片附件：结果图/日志截图，存 `backend/uploads/`，不入 git）
  - `started_at` / `finished_at`
  - 结果录入为纯手工表单 + 可粘贴 JSON 两种方式（**不集成训练平台，不做自动采集**）。

**结果比较视图**：

1. **同实验内**：该实验全部 run 的指标表（行=run，列=指标名自动对齐），数值上升/下降染色（依据 `higher_is_better`），支持选中两个 run 并排对比。
2. **跨实验**：项目下"结果总览"按指标名分组聚合（如所有报告了 Accuracy 的实验），生成对比表 + 简单趋势。指标名不一致时不做强行对齐，提示用户统一命名。
3. 比较为纯本地计算与渲染，不调 AI，零 token 成本。

**附件**：MVP 支持每 run 上传 ≤3 张图片（png/jpg，≤5MB/张），后端用 FastAPI 已有 multipart 能力落盘 `backend/uploads/`，数据库只存文件名。图片仅本人回看，不做任何 OCR/分析。

### 4.3 模块 C：基于真实实验记录的 AI 分析

**解决的问题**：把"结果说明了什么、下一步怎么办"从人脑搬进系统，且严格基于用户自己的真实数据。

**流程**：

1. 用户在实验详情页点击"AI 分析"。
2. 后端组装上下文（**只允许真实数据**）：
   - 该实验全部 `experiment_run` 的结构化结果与 notes（按时间排序；run 过多时摘要化，附 run 编号）；
   - 该实验关联的研究问题与假设；
   - 关联文献卡片的 `key_results` 摘要（作为领域参照，明确标注"文献参照"与"你的数据"的边界）。
3. DeepSeek 输出严格 JSON（沿用现有容错解析+重试模式）：
   - `summary`：结果概述（必须引用具体 run 编号，如"第 2 次运行（run_no=2）"）
   - `interpretation`：与假设的一致性判断、趋势与异常解读
   - `comparison_with_literature`：与所给文献证据的对比（有证据才写，没有写"无参照文献"）
   - `limitations`：基于现有数据能说/不能说什么（防过度解读）
   - `suggestions`：结构化下一步建议列表，每条含 `type`（`new_task` 新任务 / `new_experiment` 新实验 / `read_literature` 补文献 / `modify_design` 改设计）与具体内容、理由
4. 分析结果落库（`experiment_analysis`），前端展示 Markdown + 建议列表。
5. **闭环动作**：
   - 建议 → **转为任务**：创建 `task`（标题/描述取自建议，描述尾部带"来源：实验分析 #id / 实验名"），task 记录 `source_type/source_id`，看板卡片上显示来源徽章。
   - 建议 → **创建新实验草稿**：预填 `experiment` 的 objective/hypothesis 为草稿，用户补充方案后保存。
6. **约束**：实验没有任何 run 记录时，接口返回 400"请先录入至少一条实验运行记录，AI 分析只基于真实数据"；分析内容允许人工编辑；历史分析列表可回看。

---

## 5. 与现有功能的兼容方案（不删不重写）

| 现有功能 | 兼容策略 | 改动量 |
| --- | --- | --- |
| 项目/任务 CRUD、看板 | 完全不动。task 表仅**加列**（`source_type`、`source_id`，可空，默认 null = 手工任务），旧任务不受影响 | 迁移脚本 + 看板卡片加一个来源徽章（纯显示） |
| 风险识别引擎 | 4 条时间风险规则原样保留。**新增**第 5 条科研风险规则（可选开关）：实验 `status=running/draft` 且超过 N 天无新 run 记录 → 中风险"实验停滞"；`status=failed` → 提醒"实验失败待复盘"。在重规划 Tab 的风险列表追加展示，不修改现有计算函数签名 | 新增独立函数 `compute_experiment_risks`，与现有引擎并行 |
| DeepSeek 动态重规划 | 生成/采纳/放弃/历史全保留。增强：`build_snapshot` 的上下文 JSON 中追加实验摘要（实验数、状态分布、最近 run 摘要），让 DeepSeek 重排时知道"卡住的是实验而不是排期"；采纳动作仍只改任务表 | [replan_service.py](../backend/app/services/replan_service.py) 增加可选的实验摘要入参，路由不变 |
| PDF 问答与文献库 | 问答、笔记、切片原文全部保留。文献库 Tab 内新增二级视图"研究卡片"，与"原文问答"并列 | 新增组件 + 新路由，旧路由不动 |
| 周报生成（/report/weekly） | 保留。可选增强（P5）：聚合数据追加实验统计（本周新增 run 数） | 仅 [report.py](../backend/app/services/report.py) 聚合函数小改 |
| 汇报中心（组会周报/导师汇报） | 五章节模板与生成/编辑/导出全保留。`collect_project_data` 追加 `experiments_summary`（本周运行、最新结论、失败实验）与 `evidence_summary`（新增卡片数），Prompt 中作为可选素材章节"实验与证据进展" | [meeting_report.py](../backend/app/services/meeting_report.py) 数据聚合增强 + Prompt 微调 |
| 首页仪表盘 | 保留。P5 可选：统计卡片增加"本周实验运行次数" | 小改 home 聚合 |
| 演示模式（无 Key） | 新模块沿用：卡片抽取 demo 返回空字段模板并提示手工填写；AI 分析在无 Key 时返回 400 提示（不伪造分析结论，因为分析必须基于真实推理，演示模式下提供"手工分析笔记"入口：直接把分析内容作为纯人工笔记落库，source=manual） | 各新服务内部处理 |

---

## 6. 数据表设计（新增 5 张表 + task 加 2 列）

> 全部新表由 `init_db()` 的 `create_all` 自动创建；task 加列通过一次性幂等迁移脚本完成（启动前执行，或集成到 lifespan）。SQLite 的 `ALTER TABLE ADD COLUMN` 安全且保留数据。**迁移前自动备份 `research.db` → `research.db.bak-v2`。**

### 6.1 research_question（研究问题）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER PK | |
| project_id | FK → project（CASCADE） | |
| content | TEXT 非空 | 问题描述 |
| status | TEXT 默认 open | open（待解决）/ answered（已解答）/ suspended（挂起） |
| created_at / updated_at | DATETIME | |

### 6.2 literature_card（文献研究卡片）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER PK | |
| project_id | FK → project（CASCADE） | |
| document_id | FK → document（SET NULL）| 溯源文献；文献被删除时卡片保留但失去溯源（保护用户整理成果） |
| question_id | FK → research_question（SET NULL）| 回答哪个研究问题，可空 |
| title / authors / year | TEXT | 可空（抽取不到就留空，不伪造） |
| research_question / method / materials_datasets / metrics / key_results / limitations / relevance | TEXT | 结构化字段，key_results 支持多行 |
| evidence_type | TEXT 默认 neutral | support / against / neutral |
| source | TEXT 默认 manual | deepseek / demo / manual（人工编辑后置 manual） |
| created_at / updated_at | DATETIME | |

### 6.3 experiment（实验）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER PK | |
| project_id | FK → project（CASCADE） | |
| question_id | FK → research_question（SET NULL）| |
| title / objective / hypothesis | TEXT | |
| design | TEXT | 方案 Markdown |
| metrics_json | TEXT 默认 `[]` | 指标定义列表 |
| status | TEXT 默认 draft | draft / running / done / failed / paused |
| created_at / updated_at | DATETIME | |

### 6.4 experiment_run（实验运行记录）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER PK | |
| experiment_id | FK → experiment（CASCADE） | |
| run_no | INTEGER | 第几次运行（同实验内自增编号） |
| config_json / results_json | TEXT 默认 `{}` | 自由键值 |
| notes | TEXT | Markdown 笔记 |
| attachments_json | TEXT 默认 `[]` | 附件文件名列表 |
| started_at / finished_at | DATE | 可空 |
| created_at | DATETIME | |

### 6.5 experiment_analysis（AI 分析记录）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER PK | |
| project_id | FK → project（CASCADE） | |
| experiment_id | FK → experiment（CASCADE） | 分析哪个实验 |
| question_id | FK → research_question（SET NULL）| 冗余关联，便于按问题回看 |
| run_ids_json | TEXT | 依据哪些真实 run（快照，防篡改溯源） |
| content | TEXT | 分析正文（Markdown，可人工编辑） |
| suggestions_json | TEXT 默认 `[]` | 结构化建议（type/content/reason） |
| source | TEXT | deepseek / manual |
| created_at | DATETIME | |

### 6.6 task 表扩展（加列，不建新表）

| 新列 | 类型 | 说明 |
| --- | --- | --- |
| source_type | TEXT 可空 | question / literature_card / experiment_analysis / manual（默认 null 视为 manual） |
| source_id | INTEGER 可空 | 来源实体 id |

> 说明：采用"加列"而非关联表，是因为查询简单（看板列表直接带来源），且 SQLite 加可空列零风险。若后续需要任务↔多来源，再演进为关联表。

---

## 7. API 设计（新端点，全部挂 `/api` 前缀；旧端点不动）

### 7.1 研究问题

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/projects/{project_id}/questions` | 问题列表（含证据计数：支持/反对/参考卡片数、实验数） |
| POST | `/projects/{project_id}/questions` | 创建问题 |
| PUT | `/questions/{question_id}` | 修改内容/状态（含解答摘要字段 answer_summary，可空） |
| DELETE | `/questions/{question_id}` | 删除（关联卡片/实验的 question_id 置空，不级联删除） |

### 7.2 文献卡片

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/documents/{document_id}/card` | AI 抽取卡片（输入=该文献全文；已有卡片则提示先删除或直接返回现有卡片） |
| GET | `/documents/{document_id}/card` | 该文献的卡片 |
| PUT | `/cards/{card_id}` | 人工编辑字段 |
| DELETE | `/cards/{card_id}` | 删除卡片 |
| GET | `/projects/{project_id}/cards?question_id=` | 项目卡片列表（可按问题筛选、按证据立场筛选） |
| GET | `/projects/{project_id}/cards/compare?card_ids=1,2,3` | 字段级对比数据（本地计算） |

### 7.3 实验

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/projects/{project_id}/experiments` | 实验列表（含 run 数、最近 run 时间、停滞标记） |
| POST | `/projects/{project_id}/experiments` | 创建实验（含指标定义） |
| GET / PUT / DELETE | `/experiments/{experiment_id}` | 详情（含全部 run）/ 修改 / 删除 |
| POST | `/experiments/{experiment_id}/runs` | 新增运行记录（含附件上传，multipart 或两步：先建 run 再传附件） |
| GET / PUT / DELETE | `/runs/{run_id}` | 运行记录详情 / 修改 / 删除 |
| POST | `/runs/{run_id}/attachments` | 上传附件图片（≤3 张/run） |
| GET | `/experiments/{experiment_id}/compare` | 同实验全部 run 指标对比（本地计算） |
| GET | `/projects/{project_id}/metrics` | 跨实验指标总览（本地聚合） |

### 7.4 AI 分析

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/experiments/{experiment_id}/analysis` | 生成分析（无 run 记录 → 400；无 Key → 400 提示手工分析） |
| GET | `/experiments/{experiment_id}/analyses` | 该实验分析历史 |
| GET / PUT | `/analyses/{analysis_id}` | 详情 / 人工编辑 |
| POST | `/analyses/{analysis_id}/suggestions/{suggestion_index}/to-task` | 建议转任务（创建 task 并写 source 字段，返回新任务） |
| POST | `/analyses/{analysis_id}/suggestions/{suggestion_index}/to-experiment` | 建议转实验草稿 |
| POST | `/analyses/{analysis_id}/notes` | 手工分析笔记（无 Key 时的人工替代，source=manual） |

### 7.5 现有端点增强（响应结构追加字段，向后兼容）

- `GET /api/projects/{id}` 详情追加 `questions` 计数、`experiments` 计数（前端未用到时无影响）；
- 汇报中心聚合内部追加实验/证据数据（端点不变）。

---

## 8. 前端页面设计（新增组件，不重写旧页面）

### 8.1 项目详情页 Tab 结构（2.0）

```
项目详情页
├── 研究问题  ← 新增 Tab（问题列表、证据计数、状态管理、解答摘要）
├── 任务看板  ← 原样
├── 文献库    ← 原 Tab 内新增二级视图切换：原文问答 | 研究卡片
├── 实验      ← 新增 Tab（实验列表 → 实验详情 → 运行记录/结果比较/AI 分析）
├── 汇报中心  ← 原样（内容自动含实验摘要）
└── 重规划    ← 原样（风险列表追加实验停滞/失败提醒）
```

### 8.2 新增页面/组件清单

| 组件 | 说明 |
| --- | --- |
| `QuestionsTab` | 问题列表 + 创建/编辑抽屉 + 状态徽章 + 证据计数（点计数跳到对应卡片/实验视图） |
| `LiteratureCardsView` | 文献库二级视图：卡片列表（按问题/立场筛选）、卡片详情编辑表单、勾选多卡片 → 对比表格 |
| `CardCompareTable` | 字段级横向对比表（行=字段，列=卡片），纯前端渲染 |
| `ExperimentsTab` | 实验列表（状态徽章、run 数、停滞提示）+ 新建实验表单（含指标定义编辑器） |
| `ExperimentDetail` | 实验详情：目标/假设/方案、运行记录时间线、新增 run 表单（结构化指标输入 + JSON 粘贴 + 图片上传）、结果对比表、AI 分析面板 |
| `RunCompareTable` | run 指标对比（同实验）/ 跨实验指标总览，升降染色 |
| `AnalysisPanel` | 分析正文（Markdown）+ 建议列表 + 「转为任务」「转为实验草稿」按钮 + 手工分析笔记入口 |
| `TaskCard` 来源徽章 | 看板卡片/任务表单展示 `source_type` 徽章与来源链接（纯显示，不影响原逻辑） |
| `NewExperimentSheet` | 从分析建议预填的草稿表单 |

### 8.3 评委演示路径（2.0 叙事主线）

1. 新建项目（沿用现有 AI 拆解）→ 2. 创建研究问题"方法 A 能否在 X 数据集上超越方法 B" → 3. 上传 5 篇相关论文，各生成研究卡片，标记 2 篇支持、1 篇反对 → 4. 在卡片对比表中看到方法差异 → 5. 依据卡片创建实验（假设：A 的精度更高）→ 6. 录入 3 次运行记录（真实指标）→ 7. AI 分析：第 2 次运行精度反超、与文献一致/矛盾、建议做消融实验 → 8. 一键转为任务 → 9. 看板出现带来源的任务，风险引擎照常工作 → 10. 汇报中心生成的周报里出现"本周完成 3 次实验运行，结论摘要……"。

这条路径完整展示了"研究问题 → 文献证据 → 实验设计 → 实验运行记录 → 结果分析 → 下一步研究决策 → 转为科研任务"的闭环，直接回应评委意见。

---

## 9. 实施顺序（6 个阶段，每阶段独立可验收、可回退）

### P0：数据层与迁移（0.5–1 天）
- 新增 5 张表模型（[models.py](../backend/app/models.py)）、Pydantic schemas；
- 迁移脚本 `migrate_v2.py`：备份 research.db → task 加列（幂等：检测列存在则跳过）；集成到 lifespan 启动流程（可选：独立运行）；
- 扩展 smoke_test.py 框架（新增"研究问题 CRUD"用例）。
- **验收**：迁移两次执行不报错、旧数据完好、原 36 项冒烟全过、新表可读写。

### P1：研究问题 + 文献卡片后端（1–2 天）
- questions 路由 + 证据计数聚合；
- 卡片抽取服务（严格 JSON Prompt + 重试 + 演示模式空模板；沿用 [ai_planner.py](../backend/app/services/ai_planner.py) 的容错解析模式）；
- cards CRUD + compare 本地计算；
- smoke 新增：问题 CRUD、卡片生成（demo 模式）、卡片编辑、对比数据正确性。
- **验收**：demo 模式下全流程可用；卡片字段缺失时留空而非编造；对比接口返回正确对齐数据。

### P2：文献卡片前端（1–2 天）
- 文献库 Tab 二级视图 + 卡片表单 + 对比表 + 问题关联选择；
- **验收**：手工走查：上传 → 生成卡片 → 编辑 → 关联问题 → 选 3 张对比 → 问题页证据计数正确。

### P3：实验管理与结果比较（2–3 天）
- experiment / run 后端 + 附件上传（`backend/uploads/`，加入 .gitignore）；
- 同实验对比 + 跨实验指标总览（本地计算）；
- ExperimentsTab + ExperimentDetail 前端；
- smoke 新增：实验 CRUD、run CRUD、附件上传、对比接口、结果 JSON 校验。
- **验收**：录入 3 次运行 → 对比表正确染色 → 跨实验总览聚合正确 → 无 GPU 集成（纯录入）。

### P4：AI 分析与决策闭环（2 天）
- 分析服务（真实 run 记录 + 卡片证据上下文、run 编号引用校验、建议结构化校验）；
- to-task / to-experiment 闭环端点 + task 来源列写入；
- 看板来源徽章；实验停滞风险规则（增强 risk 模块，独立函数）；
- smoke 新增：无 run 记录 → 400；分析（demo 拒绝）；to-task 创建任务且 source 字段正确；风险规则第 5 条触发。
- **验收**：闭环完整可走通；分析输出只引用真实 run 编号；旧功能零回归。

### P5：聚合增强与收尾（1–2 天）
- 汇报中心/周报聚合实验与证据摘要（Prompt 增可选章节）；
- 首页可选增强；
- 全量 smoke 回归（旧 36 项 + 新用例）；
- 文档更新（README、PRD v2 附录）；`backend/venv` 出库清理 + .gitignore 修正。
- **验收**：汇报里出现实验摘要；全量测试通过；git 仓库体积恢复正常。

**总工作量估计**：约 8–11 个工作日（单人）。P0–P2 完成后即可先向评委展示"文献证据"能力；P3–P4 完成展示完整闭环。

---

## 10. 风险与对策

| # | 风险 | 影响 | 对策 |
| --- | --- | --- | --- |
| R1 | AI 文献抽取质量不稳定（字段缺失/张冠李戴） | 卡片不可信 | 强约束 Prompt + 重试；**字段可人工编辑且留空合法**；卡片保留 document_id 溯源；source 标记区分 AI/人工 |
| R2 | 迁移破坏现有数据 | 存量项目丢失 | 迁移前自动备份 research.db；只加可空列；迁移脚本幂等；P0 阶段先跑原 36 项冒烟 |
| R3 | 实验结果结构千差万别，对比难以对齐 | 比较视图没意义 | 实验自定义指标定义（metrics_json）；同名指标才对齐，不同名提示用户统一；run 保留自由 JSON 兜底 |
| R4 | AI 分析上下文超长（多次 run + 多卡片） | 分析失败/贵 | run 记录摘要化（每 run 一条摘要行）；卡片只送 key_results 摘要；超过 N 条 run 时提示选择分析范围 |
| R5 | 新功能破坏旧功能 | 回归 | 新表新路由新 Tab 完全隔离；每阶段跑全量 smoke；不修改现有服务函数签名（replan/meeting_report 仅追加可选参数） |
| R6 | 用户没录数据就想看 AI 分析 | 出现"无米之炊" | 无 run 记录返回 400 并明确提示；无 Key 时提供手工分析笔记，不伪造 AI 结论 |
| R7 | 附件/上传目录膨胀或泄露 | 磁盘/隐私 | 限制每 run ≤3 张、每张 ≤5MB；uploads 目录 gitignore；删除实验级联清理文件 |
| R8 | 演示模式（无 Key）无法展示 AI 分析效果 | 评委体验打折 | 卡片抽取 demo 给可编辑空模板；分析功能在无 Key 时明确提示"需配置 Key"（评审前配置一次 Key 即可全链路演示）；其余闭环（转任务）不依赖 AI 照常可用 |
| R9 | venv 入库等仓库卫生问题 | 仓库臃肿 | P0 先行 `git rm -r --cached backend/venv`（不删本地文件），补 .gitignore |

---

## 11. 验收标准（总体验收清单）

### 11.1 功能验收

1. **闭环验收**（核心）：按 §8.3 演示路径从头走通，中间无断点；任务带来源徽章且可点击跳回来源实体。
2. **文献卡片验收**：同一 PDF 的卡片与问答共存；卡片对比表字段对齐正确；证据计数与筛选一致；AI 抽取失败不产生垃圾卡片（字段留空而非编造）。
3. **实验验收**：实验全生命周期（draft→running→done/failed）流转；多次 run 对比数值与染色正确；跨实验指标总览聚合正确；附件可上传/删除。
4. **AI 分析验收**：仅基于真实录入数据；输出引用具体 run 编号；无记录拒绝生成（400 中文提示）；建议转任务/转实验草稿成功且来源正确；分析历史可回看、可编辑。
5. **兼容验收**：1.0 全部功能照常可用——原 36 项冒烟测试全过；看板/风险/重规划/PDF 问答/周报/汇报行为与升级前一致（新增实验风险提示除外）。
6. **反伪造验收**：全库无预置论文/实验/分析数据；所有 AI 内容有 source 标记；删除文献后卡片不消失（仅溯源置空）；无 Key 时没有任何"伪装成 AI"的内容。

### 11.2 技术验收

- 后端所有新端点通过 smoke 用例；Pydantic 校验覆盖非法输入（中文提示）；
- 迁移脚本幂等 + 备份生效；旧库升级后旧数据完整可读；
- 前端 `npm run build` 与 `npm run lint` 通过；新页面无控制台报错；
- 数据库表数量 = 13（原 8 + 新 5），README 同步修正；
- `backend/venv` 已出库，`git ls-files | grep venv` 为空。

### 11.3 评委视角验收

- 打开项目，能在一屏内看到"研究问题—证据—实验—决策"的脉络（项目详情 Tab 结构 + 问题页证据计数）；
- 5 分钟演示能讲清"系统解决的具体科研问题"：证据分散难以对比 → 卡片对比；实验结果记录零散 → 结构化运行记录与比较；结果解读与下一步决策靠人 → 基于真实数据的 AI 分析并落成任务。

---

## 12. 附录：本次审计发现的现状问题清单（建议随 P0 一并处理）

| # | 问题 | 位置 | 建议 |
| --- | --- | --- | --- |
| 1 | `backend/venv/` 被提交进 git | 仓库 | `git rm -r --cached backend/venv`，backend/.gitignore 补 `venv/` |
| 2 | README 与代码注释称"10 张表"，实际 8 张 | [README.md](../README.md)、[models.py](../backend/app/models.py) | 修正为 8（2.0 后为 13） |
| 3 | README 引用 `docs/screenshots/`，目录不存在 | [README.md](../README.md) | 补截图或删引用 |
| 4 | AI 类功能（计划/重规划/问答/周报/汇报）无任何自动化测试 | 后端 | P0 起随新功能逐步补 smoke 用例；核心解析函数（_extract_json/validate）建议补纯函数单测 |
| 5 | ~~`docs/ResearchPilot-项目文档.md/html/pdf` 与最新代码不同步~~ | docs | ✅ 已解决：旧版已删除，正式文档为 `docs/ResearchPilot2.0-项目文档.md`（2026-11-13） |

---

*本规划文档只增不删：1.0 全部模块保留，2.0 以新实体叠加。审核通过后按 §9 顺序实施，每个阶段单独提交、单独验收。*

---

## 13. 实施状态（2026-11-11 更新）

规划已全部实施完成。逐阶段对照：

| 阶段 | 内容 | 状态 |
| --- | --- | --- |
| P0 | 5 张新表 + task 加列（source_type/source_id）、[migrate_v2.py](../backend/migrate_v2.py) 幂等迁移（自动备份 research.db）、schemas | ✅ 完成，迁移已执行 |
| P1 | 研究问题路由（含证据计数）+ 文献卡片后端（AI 抽取/手工/对比，无 Key 空模板不伪造） | ✅ 完成 |
| P2 | 文献库 Tab 二级视图「研究卡片」+ 卡片表单/对比表 + 研究问题 Tab | ✅ 完成 |
| P3 | 实验管理（实验/运行记录/附件上传/同实验对比/跨实验指标总览，全部本地计算） | ✅ 完成 |
| P4 | AI 分析（无记录/无 Key 拒绝生成、引用 run 编号校验）+ 建议转任务/转实验（防重复）+ 看板来源徽章 + 实验停滞/失败风险规则 | ✅ 完成 |
| P5 | 汇报中心/周报聚合实验与证据；全量回归；venv 出库；README 更新 | ✅ 完成 |

**验证结果**：

- 后端冒烟测试 [smoke_test.py](../backend/smoke_test.py)：**77 项全部通过**（原 36 项 1.0 回归 + 41 项 v2 新增：研究问题/卡片/实验/运行记录/附件/对比/总览/分析错误路径/转任务闭环/实验风险/级联清理）；
- 前端 `npm run build` 通过、`npm run lint` 0 错误；
- 端到端验证：演示模式下汇报中心生成的组会周报「本周完成」章节正确包含实验运行记录；
- 仓库卫生：`backend/venv` 已从 git 索引移除，backend/.gitignore 补充 `venv/` 与 `uploads/`。

**与规划的两处实现偏差（不影响验收）**：

1. 同实验 run 对比：规划中的 `/experiments/{id}/compare` 端点已实现并被冒烟测试覆盖；前端实验详情页直接使用详情接口数据本地渲染对比表（结果一致，减少一次请求）。
2. 手工分析笔记端点：规划路径为 `/analyses/{id}/notes`，实现为 `/experiments/{id}/analysis/notes`（笔记创建不依赖已存在的分析记录，语义更合理）。

**未完成项（如实说明）**：无 Key 环境下「建议转任务」的 AI 全链路只能通过夹具注入验证（冒烟测试 16 段已覆盖端点逻辑）；配置真实 DEEPSEEK_API_KEY 后即可端到端走通 AI 分析 → 建议 → 转任务。

---

## 14. v2.1 后端科研数据模块扩展（2026-11-11 追加）

按评审后的新规格扩展后端数据层（本轮仅后端，未动前端）：

**实体字段扩展（只加列，不改旧字段、不删数据）**：

| 实体 | v2.1 新增字段 | 说明 |
| --- | --- | --- |
| research_question | objective、hypothesis | 研究目标与研究假设（可空） |
| literature_card（即 PaperNote） | innovations、evidence_snippets_json | 创新点 + 原文证据片段（quote+page，用户真实摘录） |
| experiment | variables、control_conditions、dataset、model、config_json | 实验变量/对照条件/数据集/模型/配置 |
| experiment_run | random_seed、git_commit、environment_json、log_path、result_files_json | 复现要素：种子/提交/环境/日志/结果文件 |
| research_decision（新表） | — | 科研决策：观察到的事实/分析解释/是否支持假设/未知因素/下一步建议，内容全部由研究者本人录入 |

**字段映射说明**：ExperimentRun.config_json = 本次运行参数；results_json = 实际评价指标（均为用户真实录入，系统绝不生成虚假数值）。

**验证**：冒烟测试扩展至 **111 项全部通过**（1.0 回归 36 + v2 41 + v2.1 新增 34），迁移脚本幂等执行、旧数据完好。

---

## 15. v2.2 AI 研究分析服务（2026-11-11 追加）

按研究问题聚合真实数据（PaperNote/Experiment/ExperimentRun）生成结构化 AI 分析：

- **职责边界**：数值统计（min/max/mean/best/跨实验 delta）由 Python 后端确定性计算；DeepSeek 只做解释、判断与建议；前端不直接请求模型。
- **输出七段结构**（Pydantic 严格校验）：observed_facts（必须带真实 experiment_run_id）、paper_evidence（必须带真实 paper_note_id+snippet_id，页码/原文以数据库为准，找不到依据返回空）、interpretation（标注推测）、hypothesis_status（三态枚举，单组实验禁「证明」）、uncertainty、next_experiments（≤3 条 8 字段）、task_conversion（用户显式确认后才转 Task，source_type=research_analysis）。
- **防编造**：不存在的 run/卡片/片段引用一律丢弃（全部无效触发重试）；引文改写丢弃；数值只能引用统计块；无实验数据 → 400「当前缺少实验数据，无法进行结果分析」；无 Key → 演示模板（统计真实、文字模板、source=demo 明示）。
- **验证**：23 项单元测试（unittest：无数据/单组/多组/缺证据/坏 JSON/API 不可用等）+ 冒烟测试扩展至 **124 项全部通过**。

---

## 16. v2.3 科研决策 × 任务管理打通（2026-11-11 追加）

**分层原则**：科研决策层（AI 建议 → 用户确认）与执行计划层（任务 → 风险 → 重规划）严格分离。

- **新增关联字段**（task 表）：`experiment_id`、`question_id`、`dependencies_json`（迁移幂等，旧数据不受影响）；新增 `research_action_log` 表（采纳/拒绝/修改全量留档）。
- **采纳服务** `services/research_adoption.py`：用户确认（可先修改实验目的/假设/变量/所需数据/前置条件/预计工时/起止日期/依赖任务）后原子创建 Experiment + 关联 Task（parent_id 取首个依赖，复用风险引擎"前置阻塞"规则；全部依赖存 dependencies_json）。
- **分层守卫**：风险引擎只读任务进度（逾期/阻塞/落后/工时不足），不参与科研结论；重规划 Prompt 与采纳逻辑双守卫——只允许 reschedule/reprioritize 写任务表，结构上不触碰 Experiment/ExperimentRun（假设与结果）。
- **验证**：单元测试 34 项（采纳/依赖校验/防重复/拒绝/修改/历史）+ 冒烟测试 **144 项全部通过**，其中 §27 完整链路：分析建议 → 修改留档 → 采纳（实验+任务）→ 风险预警（逾期高/阻塞中）→ 重规划调整日期 → 守卫验证（假设与结果不变）→ 拒绝与历史。
