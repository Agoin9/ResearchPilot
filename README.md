# ResearchPilot 研途智控

> 研究生的"科研导航员"：把大目标拆成小任务，延期了自动帮你重新规划。

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

## 2. 功能截图

> 截图存放于 `docs/screenshots/`，运行项目后按以下页面截取并替换：

| 页面 | 路径 | 说明 |
| --- | --- | --- |
| 首页仪表盘 | `docs/screenshots/01-home.png` | 统计卡片 + 项目列表 + 风险提醒 + 趋势图 |
| 新建项目 AI 拆解 | `docs/screenshots/02-ai-plan.png` | 生成科研计划 → 预览 → 确认写入 |
| 任务看板 | `docs/screenshots/03-board.png` | 三列看板 + 风险标记 + 状态流转 |
| 风险预警与重规划 | `docs/screenshots/04-replan.png` | 风险列表 + 新旧计划对比表 + 历史记录 |
| 文献库问答 | `docs/screenshots/05-documents.png` | PDF 上传 + 提问 + 引用溯源 |
| 汇报中心 | `docs/screenshots/06-reports.png` | 组会周报/导师汇报生成、编辑、导出 |

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
│ 10 张表       │   │ chat/completions          │
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

项目/任务 CRUD、风险预警、看板、图表等核心功能不依赖 AI，**完全照常可用**。

## 7. 项目目录结构

```
ResearchPilot/
├── backend/                        # FastAPI 后端
│   ├── requirements.txt            # Python 依赖
│   ├── .env.example                # 密钥配置模板（复制为 .env）
│   ├── smoke_test.py               # 36 项接口冒烟测试（一键回归）
│   ├── research.db                 # SQLite 数据库（启动时自动创建）
│   └── app/
│       ├── main.py                 # 入口：CORS、路由注册、异常处理
│       ├── config.py               # 配置：数据库路径、DeepSeek、风险阈值
│       ├── database.py             # SQLAlchemy 连接
│       ├── models.py               # 10 张表：project/task/progress_record/
│       │                           #   replan_history/document/doc_chunk/
│       │                           #   doc_qa/reports
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
| 一键回归 | 后端启动后执行 `cd backend && .venv\Scripts\python smoke_test.py`，36 项全过即接口全部正常 |

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

*ResearchPilot 研途智控 —— 科研任务智能管理，让每一步推进都有据可依。*
