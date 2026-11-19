# ResearchPilot 研途智控

> 研究生的"科研导航员"：把大目标拆成小任务，延期了自动帮你重新规划。

📄 **正式项目文档**：[docs/ResearchPilot2.0-项目文档.md](docs/ResearchPilot2.0-项目文档.md)（系统架构、数据库设计、API、AI 机制、测试体系与部署说明）

![技术栈](https://img.shields.io/badge/FastAPI-0.143-009688) ![前端](https://img.shields.io/badge/React-19.2-61dafb) ![数据库](https://img.shields.io/badge/SQLite-本地持久化-003b57) ![AI](https://img.shields.io/badge/DeepSeek-deepseek--chat-4d6bfe)

**⏱ 10 分钟极速复现**：装环境 → 启动后端 → 启动前端 → 打开浏览器（不需要 API Key 也能完整演示，见[演示模式](#6-演示模式没有-deepseek-key-也能跑)）

---

## 1. 项目简介

ResearchPilot 是面向研究生的科研任务智能管理 Web 应用，核心解决 5 个科研痛点：

| 痛点 | 现状 | 本项目的解法 |
| --- | --- | --- |
| 拆解难 | 导师只给大目标，不知如何拆成每天能干的事 | **AI 科研计划生成**：输入研究主题/截止时间/每周可用小时，DeepSeek 自动拆解为带依赖关系的任务链，预览确认后写入看板 |
| 发现晚 | 任务延期后知后觉，临近截止才发现来不及 | **本地风险预警引擎**：实时计算逾期 / 前置阻塞 / 进度落后 / 剩余工时不足，输出可解释原因，不消耗 AI token |
| 调整难 | 延期后不知如何重排优先级，往往直接放弃 | **DeepSeek 动态重规划**（核心创新）：一键生成调整方案，原计划 vs 新计划对比高亮，接受后自动更新任务并留档 |
| 无监督 | 没有进度反馈，动力不足 | 三列看板、进度记录、仪表盘图表（趋势/状态分布/风险提醒） |
| 汇报累 | 组会/导师汇报临时凑内容 | **汇报中心**：从数据库自动聚合本周数据，生成组会周报/导师汇报（Markdown，可编辑导出） |

**附加能力**：文献精读与引用溯源助手（上传 PDF → 按段切块 → 提问时检索相关片段 → DeepSeek 只依据原文回答并给出引用，点击引用直达原文）。

**v2 科研工作台**（围绕"文献理解—实验设计与复现—实验结果记录—研究分析—下一步决策"的科研闭环）：

| 模块 | 能力 |
| --- | --- |
| 科研驾驶舱 | 一屏聚合：研究问题、待验证假设、文献阅读进度、近期实验、重要发现、下一步计划 |
| 研究问题 | 独立实体管理研究问题（目标/假设/解答摘要），聚合每个问题的文献证据分布与实验数 |
| 文献研究库 | 上传 PDF → AI 抽取结构化卡片（问题/方法/数据/指标/创新点/局限）；字段级横向对比；原文证据片段（含页码）点击定位原文切片 |
| 实验工作台 | 实验设计（假设/变量/对照/数据集/模型/配置/指标定义）+ 运行记录（参数/随机种子/Git 提交/环境/日志/结果文件/附件）+ CSV 批量导入 + 同实验/跨实验指标对比（本地计算，不集成训练平台） |
| AI 研究分析 | 按研究问题聚合真实数据（PaperNote/Experiment/Run）生成七段结构化分析：实验事实（带 run id）、文献证据（带卡片/片段 id，防编造）、推测性解释、假设判定、不确定性、下一步实验建议（≤3）；数值由 Python 确定性计算，DeepSeek 只做解释与建议 |
| 科研决策 × 任务 | 分析建议经用户确认（可修改）→ 创建 Experiment + 关联 Task（实验/问题/日期/工时/依赖）；采纳/拒绝/修改全量留档；风险引擎与动态重规划只调执行安排，不触碰研究假设与实验结果 |
| 决策日志 | 研究者本人基于真实运行记录记录观察、解释、假设判定与下一步建议 |
| 科研风险 | 实验停滞 / 失败待复盘提醒（与任务时间风险并行） |
| 汇报增强 | 周报与组会/导师汇报自动聚合实验运行、分析结论与文献证据进展 |

## 2. 页面清单（11 个页面）

| 页面 | 路径 | 说明 |
| --- | --- | --- |
| 首页仪表盘 | `/` | 统计卡片 + 项目列表 + 风险提醒 + 趋势图 |
| 科研驾驶舱 | `/cockpit` | 一屏聚合问题/假设/文献进度/近期实验/重要发现/下一步计划 |
| 周报生成 | `/report` | 近 7 天活动聚合 + AI 周报 |
| 新建项目 AI 拆解 | `/projects/new` | 生成科研计划 → 预览 → 确认写入 |
| 文献研究库 | `/library` | 上传 PDF → 研究卡片（证据片段定位原文）+ 原文问答 |
| 实验工作台 | `/lab` | 实验设计/运行记录/CSV 导入/结果对比/AI 分析 |
| 结果比较 | `/compare` | 多实验同指标分组柱状图 + 数据表 |
| 决策日志 | `/decisions` | 观察事实/解释/假设判定/下一步建议 |
| AI 研究分析报告 | `/analysis/:id` | 七段式输出 + 建议修改/采纳/拒绝 + 操作历史（从研究问题 Tab 进入） |
| 任务看板 | `/board` | 三列看板 + 风险标记 + 状态流转 |
| 项目仪表盘 | `/projects/:id` | 6 Tab：任务看板/研究问题/文献库/实验/汇报中心/重规划 |

## 3. 系统架构

```
┌────────────────────────────────────────────────┐
│  浏览器（React 19 + TypeScript + Vite 7）        │
│  Tailwind CSS + shadcn/ui + Recharts            │
│  axios 统一封装（同源 /api，Vite 代理转发）       │
└───────────────────┬────────────────────────────┘
                    │ HTTP / JSON（RESTful API）
                    ▼
┌────────────────────────────────────────────────┐
│  后端 FastAPI 0.143（Python 3.12）               │
│  ├─ routers/  项目·任务·AI计划·文献库·周报·      │
│  │            汇报·重规划（全部 /api 前缀）       │
│  ├─ services/ 风险引擎（纯本地规则）·AI 编排·    │
│  │            文献切块检索·汇报聚合              │
│  ├─ ai_client DeepSeek 调用封装（重试/降级/      │
│  │            中文错误映射）                     │
│  └─ SQLAlchemy ORM + Pydantic 校验              │
└───────┬───────────────────────┬────────────────┘
        │ SQLite               │ HTTPS
        ▼                      ▼
┌───────────────┐   ┌─────────────────────────┐
│ research.db   │   │ DeepSeek API             │
│ 本地持久化    │   │ POST api.deepseek.com/    │
│ 16 张表       │   │ chat/completions          │
└───────────────┘   │ model: deepseek-chat      │
                    └─────────────────────────┘
```

**关键设计**：
- **风险计算不依赖大模型**：逾期/阻塞/落后/工时不足全部本地规则实时计算，DeepSeek 只负责给出调整建议；
- **API Key 只在后端**：存于 `backend/.env`，前端代码与接口响应中绝不出现；
- **AI 是增强不是必需**：未配置 Key 时全部功能进入演示模式，核心 CRUD/风险/图表照常可用；
- **数据持久化**：SQLite 落盘 `backend/research.db`，重启服务、刷新网页数据不丢。

## 4. 环境版本要求

| 环境 | 版本要求 | 验证命令 |
| --- | --- | --- |
| Python | **3.10+**（开发实测 3.12.3） | `python --version` |
| Node.js | **20+**（开发实测 v20.18.0） | `node --version` |
| npm | 随 Node 自带（实测 10.8.2） | `npm --version` |
| 操作系统 | Windows / macOS / Linux 均可（命令以 Windows PowerShell 为例） | — |

## 5. 分步启动教程

### ① 启动后端（终端 1）

```powershell
cd E:\ResearchPilot\backend

# 创建虚拟环境（首次）
python -m venv .venv

# 激活虚拟环境（每次启动前）
.venv\Scripts\activate

# 安装依赖（首次）
pip install -r requirements.txt

# 配置 DeepSeek 密钥（首次；不配也能跑演示模式）
copy .env.example .env
notepad .env        # 把 DEEPSEEK_API_KEY=sk-xxx 换成你的真实 Key

# 数据迁移（v2 升级需要执行一次；幂等，可重复运行，自动备份数据库）
venv\Scripts\python migrate_v2.py

# 启动后端
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

看到 `Application startup complete` 即成功。健康检查：浏览器打开 <http://127.0.0.1:8000/docs> 能看到全部接口分组。

### ② 启动前端（终端 2）

```powershell
cd E:\ResearchPilot\frontend

npm install         # 首次

npm run dev         # 启动，终端会打印访问地址（如 http://localhost:5173）
```

### ③ 打开浏览器

用终端 2 打印的地址打开页面（**Ctrl+F5** 强制刷新），即可开始使用。

> 建议首次体验路径：新建项目 → AI 生成科研计划 → 看板流转任务 → 故意设置一个过期任务 → 重规划 Tab 看风险预警与新旧计划对比 → 汇报中心生成导师汇报。

## 6. 演示模式（没有 DeepSeek Key 也能跑）

**不配置 `DEEPSEEK_API_KEY`（或留空）时，后端自动进入演示模式**，所有页面明确显示「演示模式」徽章：

| 功能 | 演示模式行为 |
| --- | --- |
| AI 科研计划生成 | 按阶段返回预设样例任务（6 个，带依赖链与日期排布） |
| 重规划 | 本地规则模拟调整（逾期任务顺延 + 提高优先级） |
| 文献问答 | 关键词匹配直接返回相关片段 |
| 汇报中心 / 周报 | 用真实数据库数据拼接模板内容 |
| 文献卡片抽取 | 返回空字段模板，提示手工填写（不伪造内容） |
| AI 实验分析 | 拒绝生成并提示改用「手工分析笔记」（不伪造结论）；转任务等闭环不依赖 AI 照常可用 |
| AI 研究分析 | 统计数值由后端基于数据库真实记录确定性计算；分析文字为模板并明确标注「演示模式，非真实分析结论」；七段结构（事实/证据/推测/假设判定/不确定性/建议）完整可验收 |

项目/任务 CRUD、风险预警、看板、图表等核心功能不依赖 AI，**完全照常可用**。

## 7. 项目目录结构

```
ResearchPilot/
├── backend/                        # FastAPI 后端
│   ├── requirements.txt            # Python 依赖
│   ├── .env.example                # 密钥配置模板（复制为 .env）
│   ├── smoke_test.py               # 144 项接口冒烟测试（一键回归，含 v2 全部模块）
│   ├── acceptance_test.py          # 10 场景质量验收端到端测试（--keep 保留数据）
│   ├── migrate_v2.py               # v2 数据迁移脚本（备份 + 加列，幂等）
│   ├── research.db                 # SQLite 数据库（启动时自动创建）
│   ├── uploads/                    # v2 实验附件图片（不进 git）
│   ├── tests/                      # 单元测试（unittest，34 项）
│   │   ├── test_research_analysis.py     # AI 研究分析：统计/校验/防编造/错误路径
│   │   └── test_research_adoption.py     # 建议采纳：实验+任务+历史/依赖校验/防重复
│   └── app/
│       ├── main.py                 # 入口：CORS、路由注册、异常处理
│       ├── config.py               # 配置：数据库路径、DeepSeek、风险阈值
│       ├── database.py             # SQLAlchemy 连接
│       ├── models.py               # 16 张表：project/task/progress_record/
│       │                           #   replan_history/document/doc_chunk/
│       │                           #   doc_qa/reports + research_question/
│       │                           #   literature_card/experiment/
│       │                           #   experiment_run/experiment_analysis/
│       │                           #   research_decision/research_analysis/
│       │                           #   research_action_log
│       ├── schemas.py              # Pydantic 校验（中文错误提示）
│       ├── ai_client.py            # DeepSeek 客户端（超时/余额/Key 错误映射）
│       ├── routers/                # projects·tasks·home·ai·documents·
│       │                           #   report·reports·replans
│       └── services/               # risk(风险引擎)·ai_planner·
│                                   #   document_service·replan_service·
│                                   #   meeting_report·report·serializers
├── frontend/                       # React + Vite 前端
│   ├── vite.config.ts              # /api 同源代理到 127.0.0.1:8000
│   └── src/
│       ├── pages/                  # 首页·新建项目·任务看板·项目仪表盘·周报
│       ├── components/             # board(看板)·documents(文献库)·
│       │                           #   replan(重规划)·reports(汇报中心)·
│       │                           #   home(仪表盘)·ui(组件库)
│       ├── services/api.ts         # axios 统一封装（全部接口函数）
│       ├── types/index.ts          # 前后端共享类型定义
│       └── hooks/                  # useAsyncData(加载三态)·useTheme
└── docs/                           # 产品需求文档、架构设计、截图
```

## 8. 常见问题排查

| 现象 | 原因与解决 |
| --- | --- |
| 前端提示「无法连接后端服务」 | 后端没启动，或 8000 被旧进程占用。先确认终端 1 有 `Application startup complete`；占用则 `netstat -ano \| findstr :8000` 找 PID，`taskkill //PID <PID> //F` 后重启 |
| 前端打开了但数据是旧的 | Vite 旧实例占着端口，页面连的是旧进程。**关掉所有旧的前后端终端**重新启动，浏览器 Ctrl+F5 |
| `ModuleNotFoundError: No module named 'httpx'` | 激活的虚拟环境不是装过依赖的那个。在 `backend` 目录下重新 `pip install -r requirements.txt` |
| DeepSeek 返回 HTTP 404 | `.env` 的 `DEEPSEEK_BASE_URL` 必须填 `https://api.deepseek.com`（不要带 `/chat/completions` 后缀） |
| 提示「API Key 无效 / 余额不足」 | 401：检查 `.env` 密钥；402：DeepSeek 账户充值。都是前端 toast 中文提示，不会崩溃 |
| Windows 终端 curl 发中文报 400/422 | 终端 GBK 编码问题（后端已做防护）。改用 `curl --data-binary @body.json`（文件存 UTF-8），或用浏览器/前端页面测试 |
| 上传扫描版 PDF 提示不支持 | 扫描版无文字层，需使用含文字层的 PDF（如知网/arXiv 下载的原文 PDF） |
| 下拉框点不出选项 | 已全部改为原生 select，若仍复现请强制刷新（Ctrl+F5） |
| 一键回归 | 后端启动后执行 `cd backend && venv\Scripts\python smoke_test.py`，144 项全过即接口全部正常（含 v2 科研工作台、AI 研究分析、决策×任务闭环） |
| 单元测试 | `cd backend && venv\Scripts\python -m unittest discover -s tests`（34 项，不依赖后端进程与外部 API） |
| 质量验收 | 后端启动后执行 `cd backend && venv\Scripts\python acceptance_test.py`（10 个关键业务场景；加 `--keep` 保留验收数据供界面复查） |

## 9. 开发演进与 AI 协作说明

### Git 演进

| 阶段 | 里程碑 | 内容 |
| --- | --- | --- |
| M1 | 架构设计（361d6eb） | PRD + 系统架构 + 4 张核心表结构设计定稿 |
| M2 | 前端静态 UI（8a82885） | 全部页面、看板、图表 UI，使用模拟静态数据 |
| M3 | 后端数据层 + 联调 | FastAPI + SQLite 全量 CRUD、入参校验、风险引擎 v1、前端接入真实接口 |
| M4 | AI 任务规划 | DeepSeek 客户端、计划生成/预览/确认、演示模式、周报生成 |
| M5 | 文献库 | PDF 提取切块、关键词检索、引用溯源问答、笔记 |
| M6 | 汇报中心 | 组会周报/导师汇报生成、编辑、导出 Markdown |
| M7 | **核心创新** | 风险预警增强（前置阻塞/工时不足）+ DeepSeek 动态重规划 + 新旧对比 + 历史留档 |

> 当前工作区包含 M1~M7 全部代码（backend/ 与前端改动尚未提交时，`git status` 可见；提交后按上述阶段描述演进）。

### AI 协作方式

- **Claude Code（Anthropic Claude）负责工程实现**：需求分析、前后端全部代码编写、接口联调、36 项冒烟测试与回归验证、故障排查（CORS/PNA 跨域、编码、虚拟环境等问题的定位与修复）；
- **DeepSeek 提供业务大模型能力**：科研任务拆解、动态重规划建议、文献问答（引用溯源）、组会/导师汇报生成——全部通过后端统一调用，Key 存于 `.env` 不出后端；
- **边界清晰**：风险识别等基础计算全部为本地规则引擎（可解释、零 token 成本、断网可用），大模型只负责"给建议"，用户确认后建议才落库。

---

## 10. 从安装到完整演示的复现步骤

**第 0 步 · 环境安装**（Windows PowerShell）：

```powershell
cd E:\ResearchPilot\backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env        # 不填 Key 也能完整演示（演示模式）；填真实 Key 获得真实 AI 分析

cd E:\ResearchPilot\frontend
npm install
```

**第 1 步 · 启动与迁移**：

```powershell
# 终端 1（后端）
cd E:\ResearchPilot\backend
venv\Scripts\activate
venv\Scripts\python migrate_v2.py        # 幂等迁移（自动备份数据库）
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 终端 2（前端）
cd E:\ResearchPilot\frontend
npm run dev                               # 打开打印的地址（如 http://localhost:5173）
```

**第 2 步 · 完整演示路径**（对应质量验收的 10 个场景，浏览器操作）：

1. **建项目与研究问题**：新建项目（可让 AI 拆解计划）→ 项目仪表盘「研究问题」Tab → 新建问题，填写目标与假设。
2. **上传 PDF**：项目「文献库」Tab → 上传一篇含文字层的 PDF。
3. **生成研究卡片并验证引用**：「研究卡片」二级视图 → 点该文献「一键抽取」（无 Key 时为空模板）→ 手工完善方法与创新点 → 添加原文证据片段（摘录原文+页码）→ 保存后点击片段，页面自动切到原文视图并高亮定位到包含该摘录的切片。
4. **根据文献建实验**：「实验」Tab → 新建实验：假设（参照文献结论）、实验变量、对照条件、数据集、模型、配置 JSON、指标定义。
5. **录入运行记录**：实验详情 →「新增运行记录」录入参数/随机种子/Git Commit/环境/实际指标/备注；多组数据可用「CSV 导入」批量录入（表头=列名、每行=一次运行、note 列写备注）。
6. **比较指标**：左侧「结果比较」页 → 勾选多个实验 → 同一指标按运行次数对齐的分组柱状图（悬浮看数值）+ 数据表视图。
7. **AI 研究分析**：项目「研究问题」Tab → 点「生成研究分析」→ 自动跳转分析报告页：七段结构（实验事实带 run id、文献证据带卡片/片段 id+页码、推测性解释、假设判定、不确定性、下一步实验建议 ≤3、确定性统计表）。无 Key 时统计数值真实、文字为明确标注的演示模板。
8. **确认建议 → 实验+任务**：分析报告页每条建议可「修改」（留档）、「拒绝」（留档）、「采纳」（确认表单：实验目的/假设/变量/所需数据/前置条件/预计工时/起止日期/依赖任务）→ 自动创建 Experiment 与关联 Task（任务卡片带「来源·研究分析」徽章），全部操作在「操作历史」区可回看。
9. **模拟延期**：把某任务计划日期改到过去 → 看板出现红色「已逾期」风险 →「重规划」Tab 生成方案 → 对比表查看调整 → 接受后任务日期更新；研究假设与实验结果不受影响。
10. **回看历史**：决策日志页（观察/解释/假设判定/建议）、实验详情（全部运行记录与附件）、重规划 Tab（原计划 vs 新计划 + 状态）、`GET /api/research-analyses/{id}/actions`（采纳/拒绝/修改全量留档）。

## 11. 质量验收结论（2026-11-11 执行）

| 项目 | 结果 |
| --- | --- |
| 后端接口回归（smoke_test.py） | ✅ 通过（无 Key 144 项 / 有 Key 143 项，1 项无 Key 专属断言条件跳过；1.0 原 36 项 + v2 各模块全覆盖） |
| 单元测试（unittest，36 项） | ✅ 全部通过（不依赖外部 API，mock DeepSeek 客户端） |
| 前端构建 | ✅ `npm run build` 通过、`npm run lint` 0 错误 |
| 10 场景端到端（acceptance_test.py） | ✅ 22/22 通过（真实 PDF 解析、证据定位、演示数据对比、七段分析、采纳闭环、风险/重规划、历史完整性） |
| 数据持久化 | ✅ 后端重启后项目/问题/分析历史/统计快照完好（SQLite 落盘） |
| 密钥场景 | ✅ 无 Key：全部 AI 功能走演示模式（明确标注）；✅ 无效 Key：注入假密钥实测 → 502 + "API Key 无效或已过期"中文提示；✅ **真实 Key（已实测）**：AI 研究分析 `source=deepseek`（约 10 秒返回）——6 条事实全部引用真实运行记录、证据引用真实卡片/片段/页码、解释引用后端确定性统计值、3 条建议含工时；AI 计划生成同样成功（9 个任务） |
| 前端密钥暴露 | ✅ 未发现（全库扫描无真实密钥格式字符串；密钥仅存 backend/.env） |
| SQL 注入 | ✅ 未发现注入面（全部查询走 SQLAlchemy ORM 绑定参数；无字符串拼接 SQL） |
| 文件上传风险 | ✅ PDF 仅提取文字不落盘（20MB 限制/加密与扫描版检测）；图片附件白名单类型+5MB 限制+uuid 文件名（无路径穿越） |
| 数据丢失 | ✅ 迁移自动备份 research.db.bak-v2；级联删除有测试覆盖；卡片/任务对文献的引用为 SET NULL 保护；删除操作前端二次确认 |
| 原有功能回归 | ✅ 1.0 全部功能（项目/任务/进度/风险/周报/汇报/PDF 问答）行为不变，36 项冒烟全过 |

*验收中发现并修复的 3 个问题：① 验收脚本场景 3 未把卡片关联研究问题导致分析证据为空——脚本缺陷，修复后通过（产品逻辑正确：分析只读取关联问题的卡片）；② 采纳服务把日期字符串直接写入 SQLite Date 列报 500——服务层增加日期归一化后修复；③ 真实 AI 输出的解释未强制使用推测性措辞——后端校验新增「推测/可能/尚不能确定」等标记词强制检查（缺失触发重试，仍缺则 502 友好提示），并新增 2 项单元测试。*

---

*ResearchPilot 研途智控 —— 科研任务智能管理，让每一步推进都有据可依。*
