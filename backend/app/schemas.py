"""Pydantic 请求/响应模型：入参校验（中文错误提示）+ 输出序列化。

对外字段统一为 camelCase（与前端约定一致），数据库字段为 snake_case。
"""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic.alias_generators import to_camel

PROJECT_STATUSES = ("active", "completed", "paused")
TASK_STATUSES = ("todo", "doing", "done")
PRIORITIES = ("high", "medium", "low")
RISK_LEVELS = ("none", "medium", "high")


class CamelModel(BaseModel):
    """所有对外模型的基类：字段名 ↔ camelCase 互相兼容。"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


# ══════════════════════════════ 项目 ══════════════════════════════

class ProjectCreate(CamelModel):
    """创建项目：name / goal / deadline / weekly_hours。"""

    name: str
    goal: str
    deadline: date
    weekly_hours: float = Field(allow_inf_nan=False)

    @field_validator("name")
    @classmethod
    def check_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("项目名称不能为空")
        if len(v) > 100:
            raise ValueError("项目名称不能超过 100 个字符")
        return v

    @field_validator("goal")
    @classmethod
    def check_goal(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("科研目标描述不能为空")
        if len(v) > 2000:
            raise ValueError("科研目标描述不能超过 2000 个字符")
        return v

    @field_validator("deadline")
    @classmethod
    def check_deadline(cls, v: date) -> date:
        if v < date.today():
            raise ValueError("截止日期不能早于今天")
        return v

    @field_validator("weekly_hours")
    @classmethod
    def check_weekly_hours(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("每周可用小时数必须大于 0")
        if v > 168:
            raise ValueError("每周可用小时数不能超过 168（一周最多 168 小时）")
        return v


class ProjectUpdate(CamelModel):
    """更新项目：所有字段可选，只更新提交的字段。"""

    name: str | None = None
    goal: str | None = None
    deadline: date | None = None
    weekly_hours: float | None = Field(default=None, allow_inf_nan=False)
    status: str | None = None

    @field_validator("name")
    @classmethod
    def check_name(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("项目名称不能为空")
        if len(v) > 100:
            raise ValueError("项目名称不能超过 100 个字符")
        return v

    @field_validator("goal")
    @classmethod
    def check_goal(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("科研目标描述不能为空")
        if len(v) > 2000:
            raise ValueError("科研目标描述不能超过 2000 个字符")
        return v

    @field_validator("deadline")
    @classmethod
    def check_deadline(cls, v: date | None) -> date | None:
        if v is not None and v < date.today():
            raise ValueError("截止日期不能早于今天")
        return v

    @field_validator("weekly_hours")
    @classmethod
    def check_weekly_hours(cls, v: float | None) -> float | None:
        if v is None:
            return v
        if v <= 0:
            raise ValueError("每周可用小时数必须大于 0")
        if v > 168:
            raise ValueError("每周可用小时数不能超过 168（一周最多 168 小时）")
        return v

    @field_validator("status")
    @classmethod
    def check_status(cls, v: str | None) -> str | None:
        if v is not None and v not in PROJECT_STATUSES:
            raise ValueError(
                "项目状态必须是 active（进行中）/ completed（已完成）/ paused（已暂停）之一"
            )
        return v


class ProjectOut(CamelModel):
    id: int
    name: str
    goal: str
    deadline: date
    weekly_hours: float
    status: str
    created_at: datetime
    updated_at: datetime


class ProjectSummary(ProjectOut):
    """项目列表项：附带整体进度、任务数、风险等级、剩余天数（实时计算）。"""

    progress: int
    tasks_total: int
    tasks_done: int
    risk: str
    days_left: int


# ══════════════════════════════ 任务 ══════════════════════════════

def _check_title(v: str) -> str:
    v = v.strip()
    if not v:
        raise ValueError("任务标题不能为空")
    if len(v) > 200:
        raise ValueError("任务标题不能超过 200 个字符")
    return v


def _check_optional_text(v: str | None, label: str, limit: int) -> str | None:
    if v is None:
        return v
    v = v.strip()
    if len(v) > limit:
        raise ValueError(f"{label}不能超过 {limit} 个字符")
    return v


class TaskCreate(CamelModel):
    """创建任务：project_id 必填，其余字段有默认值。"""

    project_id: int = Field(gt=0)
    parent_id: int | None = Field(default=None, gt=0)
    title: str
    description: str | None = None
    status: str = "todo"
    priority: str = "medium"
    planned_start_date: date | None = None
    planned_end_date: date | None = None
    estimated_hours: float | None = Field(default=None, allow_inf_nan=False)
    is_milestone: bool = False
    sort_order: int = 0

    @field_validator("title")
    @classmethod
    def check_title(cls, v: str) -> str:
        return _check_title(v)

    @field_validator("description")
    @classmethod
    def check_description(cls, v: str | None) -> str | None:
        return _check_optional_text(v, "任务描述", 2000)

    @field_validator("status")
    @classmethod
    def check_status(cls, v: str) -> str:
        if v not in TASK_STATUSES:
            raise ValueError("任务状态必须是 todo（待开始）/ doing（进行中）/ done（已完成）之一")
        return v

    @field_validator("priority")
    @classmethod
    def check_priority(cls, v: str) -> str:
        if v not in PRIORITIES:
            raise ValueError("任务优先级必须是 high（高）/ medium（中）/ low（低）之一")
        return v

    @field_validator("estimated_hours")
    @classmethod
    def check_estimated_hours(cls, v: float | None) -> float | None:
        if v is None:
            return v
        if v <= 0:
            raise ValueError("预计耗时必须大于 0")
        if v > 1000:
            raise ValueError("预计耗时不能超过 1000 小时")
        return v

    @model_validator(mode="after")
    def check_dates(self):
        if (
            self.planned_start_date
            and self.planned_end_date
            and self.planned_end_date < self.planned_start_date
        ):
            raise ValueError("计划截止日期不能早于计划开始日期")
        return self


class TaskUpdate(CamelModel):
    """更新任务：所有字段可选。status=done 时进度自动置 100；progress=100 时自动标记完成。"""

    parent_id: int | None = Field(default=None, gt=0)
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    planned_start_date: date | None = None
    planned_end_date: date | None = None
    estimated_hours: float | None = Field(default=None, allow_inf_nan=False)
    progress: int | None = None
    is_milestone: bool | None = None
    sort_order: int | None = None

    @field_validator("title")
    @classmethod
    def check_title(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return _check_title(v)

    @field_validator("description")
    @classmethod
    def check_description(cls, v: str | None) -> str | None:
        return _check_optional_text(v, "任务描述", 2000)

    @field_validator("status")
    @classmethod
    def check_status(cls, v: str | None) -> str | None:
        if v is not None and v not in TASK_STATUSES:
            raise ValueError("任务状态必须是 todo（待开始）/ doing（进行中）/ done（已完成）之一")
        return v

    @field_validator("priority")
    @classmethod
    def check_priority(cls, v: str | None) -> str | None:
        if v is not None and v not in PRIORITIES:
            raise ValueError("任务优先级必须是 high（高）/ medium（中）/ low（低）之一")
        return v

    @field_validator("estimated_hours")
    @classmethod
    def check_estimated_hours(cls, v: float | None) -> float | None:
        if v is None:
            return v
        if v <= 0:
            raise ValueError("预计耗时必须大于 0")
        if v > 1000:
            raise ValueError("预计耗时不能超过 1000 小时")
        return v

    @field_validator("progress")
    @classmethod
    def check_progress(cls, v: int | None) -> int | None:
        if v is not None and not 0 <= v <= 100:
            raise ValueError("进度必须在 0 到 100 之间")
        return v

    @model_validator(mode="after")
    def check_dates(self):
        if (
            self.planned_start_date
            and self.planned_end_date
            and self.planned_end_date < self.planned_start_date
        ):
            raise ValueError("计划截止日期不能早于计划开始日期")
        return self


class TaskOut(CamelModel):
    id: int
    project_id: int
    parent_id: int | None
    title: str
    description: str | None
    status: str
    priority: str
    planned_start_date: date | None
    planned_end_date: date | None
    estimated_hours: float | None
    progress: int
    is_milestone: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime
    risk: str = "none"       # 实时计算的风险等级
    risk_reason: str = ""    # 风险原因（给用户看的说明）


# ═══════════════════════════ 进度记录 ═══════════════════════════════

class ProgressCreate(CamelModel):
    progress: int
    hours_spent: float | None = Field(default=None, allow_inf_nan=False)
    note: str | None = None

    @field_validator("progress")
    @classmethod
    def check_progress(cls, v: int) -> int:
        if not 0 <= v <= 100:
            raise ValueError("进度必须在 0 到 100 之间")
        return v

    @field_validator("hours_spent")
    @classmethod
    def check_hours_spent(cls, v: float | None) -> float | None:
        if v is None:
            return v
        if v < 0:
            raise ValueError("投入小时数不能为负数")
        if v > 168:
            raise ValueError("投入小时数不能超过 168")
        return v

    @field_validator("note")
    @classmethod
    def check_note(cls, v: str | None) -> str | None:
        return _check_optional_text(v, "备注", 2000)


class ProgressRecordOut(CamelModel):
    id: int
    task_id: int
    progress: int
    hours_spent: float | None
    note: str | None
    created_at: datetime


class ProgressUpdateOut(CamelModel):
    """新增进度记录的响应：新记录 + 更新后的任务。"""

    record: ProgressRecordOut
    task: TaskOut


# ═══════════════════════ 项目详情 / 首页聚合 ═══════════════════════════

class ProjectDetailOut(CamelModel):
    project: ProjectSummary
    tasks: list[TaskOut]


class RiskTaskItem(CamelModel):
    id: int
    project_id: int
    task_title: str
    project_name: str
    level: str
    reason: str


class HomeStats(CamelModel):
    active_projects: int
    todo_tasks: int
    weekly_hours_spent: float
    weekly_hours_delta: float
    risk_task_count: int


class TrendPoint(CamelModel):
    date: str
    completed: int


class StatusSlice(CamelModel):
    name: str
    value: int


class HomeOut(CamelModel):
    stats: HomeStats
    projects: list[ProjectSummary]
    risk_tasks: list[RiskTaskItem]
    trend: list[TrendPoint]
    distribution: list[StatusSlice]


# ═══════════════════════ AI 科研计划（DeepSeek） ═══════════════════════════

class AiPlanRequest(CamelModel):
    """生成科研计划的输入：研究主题 / 截止日期 / 每周小时 / 当前阶段 / 已完成工作。"""

    topic: str
    deadline: date
    weekly_hours: float = Field(allow_inf_nan=False)
    current_stage: str
    completed_work: str | None = None

    @field_validator("topic")
    @classmethod
    def check_topic(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("研究主题不能为空")
        if len(v) > 2000:
            raise ValueError("研究主题不能超过 2000 个字符")
        return v

    @field_validator("deadline")
    @classmethod
    def check_deadline(cls, v: date) -> date:
        if v < date.today():
            raise ValueError("截止日期不能早于今天")
        return v

    @field_validator("weekly_hours")
    @classmethod
    def check_weekly_hours(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("每周可用小时数必须大于 0")
        if v > 168:
            raise ValueError("每周可用小时数不能超过 168（一周最多 168 小时）")
        return v

    @field_validator("current_stage")
    @classmethod
    def check_stage(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("当前研究阶段不能为空")
        if len(v) > 100:
            raise ValueError("当前研究阶段不能超过 100 个字符")
        return v

    @field_validator("completed_work")
    @classmethod
    def check_completed(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if len(v) > 2000:
            raise ValueError("已完成工作不能超过 2000 个字符")
        return v


class AiPlanTask(CamelModel):
    """计划中的单个任务（与前端约定的 JSON 结构，priority 为 高/中/低）。"""

    task_id: str
    title: str
    description: str = ""
    start_date: date
    due_date: date
    priority: str = "中"
    expected_deliverable: str = ""
    dependencies: list[str] = []
    estimated_hours: float
    rationale: str = ""


class AiPlanOut(CamelModel):
    """生成计划的响应：source=deepseek 真实生成 / demo 演示模式。"""

    source: str
    tasks: list[AiPlanTask]
    warning: str = ""


class AiPlanConfirmRequest(CamelModel):
    """确认计划：用户点「确认」时才写入数据库（项目 + 任务一起创建）。"""

    project: ProjectCreate
    tasks: list[AiPlanTask]


class AiPlanConfirmOut(CamelModel):
    project: ProjectSummary
    tasks: list[TaskOut]


# ═══════════════════════ 周报生成 ═══════════════════════

class WeeklyCompletedTask(CamelModel):
    id: int
    title: str
    completed_at: datetime


class WeeklyProgressItem(CamelModel):
    task_title: str
    progress: int
    hours_spent: float | None
    note: str | None
    created_at: datetime


class WeeklyProjectReport(CamelModel):
    project_id: int
    project_name: str
    completed_tasks: list[WeeklyCompletedTask]
    progress_records: list[WeeklyProgressItem]


class WeeklyStats(CamelModel):
    tasks_completed: int
    hours_spent: float
    progress_updates: int


class WeeklyReportOut(CamelModel):
    """近 7 天科研活动聚合（不依赖 AI，随时可用）。"""

    week_start: date
    week_end: date
    stats: WeeklyStats
    projects: list[WeeklyProjectReport]


class AiWeeklyReportOut(CamelModel):
    """AI 生成的周报正文（source=deepseek / demo）。"""

    source: str
    content: str


# ═══════════════════════ 文献库（精读与引用溯源） ═══════════════════════

class DocumentOut(CamelModel):
    id: int
    project_id: int
    title: str
    file_name: str
    chunk_count: int
    created_at: datetime


class DocChunkOut(CamelModel):
    id: int
    chunk_index: int
    content: str


class DocumentDetailOut(DocumentOut):
    full_text: str
    chunks: list[DocChunkOut]


class QaCreate(CamelModel):
    """对文献提问。"""

    question: str

    @field_validator("question")
    @classmethod
    def check_question(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("问题不能为空")
        if len(v) > 2000:
            raise ValueError("问题不能超过 2000 个字符")
        return v


class CitationOut(CamelModel):
    """引用片段：chunk_index 指向文献的切片序号，quote 为原文原句。"""

    chunk_index: int
    quote: str


class QaOut(CamelModel):
    id: int
    document_id: int
    project_id: int
    question: str
    answer: str
    citations: list[CitationOut]
    confidence: float
    source: str  # deepseek / demo
    is_saved: bool
    created_at: datetime


# ═══════════════════════ 组会周报与导师汇报 ═══════════════════════

class ReportCreate(CamelModel):
    """生成汇报：汇报类型 + 数据时间范围。"""

    report_type: str = "meeting"
    week_start: date | None = None
    week_end: date | None = None

    @field_validator("report_type")
    @classmethod
    def check_type(cls, v: str) -> str:
        if v not in ("meeting", "supervisor"):
            raise ValueError("汇报类型必须是 meeting（组会周报）/ supervisor（导师汇报）之一")
        return v

    @model_validator(mode="after")
    def check_range(self):
        if self.week_start and self.week_end and self.week_end < self.week_start:
            raise ValueError("结束日期不能早于开始日期")
        return self


class ReportUpdate(CamelModel):
    """编辑汇报正文。"""

    content: str

    @field_validator("content")
    @classmethod
    def check_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("汇报内容不能为空")
        if len(v) > 50000:
            raise ValueError("汇报内容不能超过 50000 个字符")
        return v


class ReportOut(CamelModel):
    id: int
    project_id: int
    title: str
    report_type: str
    week_start: date | None
    week_end: date | None
    content: str
    source: str  # deepseek / demo
    created_at: datetime
    updated_at: datetime
