# ResearchPilot 后端服务

研途智控后端：Python + FastAPI + SQLite，提供项目 / 任务 / 进度记录的增删改查接口。
数据持久化在 `backend/research.db`，重启服务、刷新网页数据都不会丢失。

## 启动步骤（Windows）

首次使用需要安装依赖（只需做一次）：

```bash
cd backend
python -m venv .venv                          # 创建虚拟环境
.venv\Scripts\python -m pip install -r requirements.txt   # 安装依赖
```

启动服务：

```bash
cd backend
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

看到以下输出即启动成功：

```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

- 健康检查：<http://127.0.0.1:8000/api/health> → `{"status": "ok"}`
- 接口文档（可在线调试全部接口）：<http://127.0.0.1:8000/docs>

> 前端开发服务器（Vite）已配置代理，会把 `/api` 请求转发到 `127.0.0.1:8000`，
> 前后端同时启动即可联调。

## 项目结构

```
backend/
├── requirements.txt          # Python 依赖
├── research.db               # SQLite 数据库（首次启动自动创建，勿提交 git）
└── app/
    ├── main.py               # 应用入口：CORS、路由注册、启动建表
    ├── config.py             # 数据库路径、风险阈值常量
    ├── database.py           # SQLAlchemy 连接与会话
    ├── models.py             # 4 张表：project / task / progress_record / replan_history
    ├── schemas.py            # Pydantic 请求/响应模型（入参校验，中文错误提示）
    ├── routers/
    │   ├── projects.py       # 项目 CRUD
    │   ├── tasks.py          # 任务 CRUD + 进度记录
    │   └── home.py           # 首页聚合数据
    └── services/
        ├── risk.py           # 风险识别引擎（纯本地规则，不调 AI）
        ├── serializers.py    # ORM → 响应模型
        └── home.py           # 首页统计聚合
```

## 接口一览（统一前缀 /api，错误统一返回 {"detail": "错误说明"}）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 健康检查 |
| GET | `/api/home` | 首页聚合：统计卡片 + 项目列表 + 风险任务 + 趋势图 + 状态分布 |
| POST | `/api/projects` | 创建项目（name / goal / deadline / weeklyHours） |
| GET | `/api/projects` | 项目列表（含整体进度、任务数、风险等级、剩余天数） |
| GET | `/api/projects/{id}` | 项目详情 + 任务列表（每个任务附带风险标记） |
| PUT | `/api/projects/{id}` | 更新项目（只更新提交的字段） |
| DELETE | `/api/projects/{id}` | 删除项目（级联删除任务、进度记录、重规划历史） |
| POST | `/api/tasks` | 创建任务（projectId 必填，可挂 parentId 里程碑） |
| PUT | `/api/tasks/{id}` | 更新任务（status=done 自动进度 100；progress=100 自动完成） |
| DELETE | `/api/tasks/{id}` | 删除任务（级联删除进度记录和子任务） |
| POST | `/api/tasks/{id}/progress` | 新增进度记录（写入 history 并同步 task.progress） |
| GET | `/api/tasks/{id}/progress` | 进度记录列表（时间升序） |

## 入参校验说明

非法输入返回 HTTP 422，`detail` 中带明确的中文错误提示，例如：

- 项目名称 / 科研目标为空 → `项目名称不能为空` / `科研目标描述不能为空`
- `weeklyHours` ≤ 0 → `每周可用小时数必须大于 0`
- 截止日期早于今天 → `截止日期不能早于今天`
- 任务状态非法 → `任务状态必须是 todo（待开始）/ doing（进行中）/ done（已完成）之一`
- 计划截止早于计划开始 → `计划截止日期不能早于计划开始日期`
- 进度超出 0~100 → `进度必须在 0 到 100 之间`
- 访问不存在的项目 / 任务 → HTTP 404 `项目不存在` / `任务不存在`
- 请求体不是合法 JSON 或包含非 UTF-8 编码的中文（Windows 终端 curl 发中文时的 GBK 编码问题）→ 400 `请求体不是合法的 JSON（或包含非 UTF-8 编码的中文），请使用 UTF-8 编码提交`

## 冒烟测试

后端启动后，可一键回归全部接口（脚本只操作名称带「【冒烟测试】」前缀的数据，不影响已有数据）：

```bash
cd backend
venv\Scripts\python smoke_test.py
```

36 项检查：项目/任务 CRUD、状态流转、进度记录、入参校验、编码错误处理、风险引擎、级联删除。

## 已知约定

- 暂未接入 DeepSeek API，AI 拆解 / 重规划（replan_history 表已建好）在后续版本提供。
- 风险识别为纯本地规则（逾期 → 高风险；进度落后 >20 个百分点 → 中风险），随查询实时计算、不落库。
- 接口错误统一返回 `{"detail": "..."}`；即使请求体编码异常或出现未预期异常，也不会返回 500 裸文本（有兜底处理器）。
