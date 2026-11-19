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
    # v2 任务来源：question / literature_card / experiment_analysis / manual（null = 手工创建）
    source_type: str | None = None
    source_id: int | None = None
    # v2.3 科研任务关联：所属实验 / 所属研究问题 / 依赖关系
    experiment_id: int | None = None
    question_id: int | None = None
    dependencies: list[int] = []
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

class ExperimentRiskOut(CamelModel):
    """实验维度的科研风险提醒（与任务风险并行；v2 新增）。"""

    experiment_id: int
    title: str
    level: str          # medium
    reason: str


class ProjectDetailOut(CamelModel):
    project: ProjectSummary
    tasks: list[TaskOut]
    # v2：实验维度的科研风险提醒（停滞/失败），与任务时间风险并行
    experiment_risks: list[ExperimentRiskOut] = []


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
    experiment_runs: int = 0  # v2：本周新增实验运行记录数


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


# ═══════════════════════ 重规划（风险预警 + 动态调整） ═══════════════════════

class ReplanTaskSnapshot(CamelModel):
    """重规划时的任务快照（原计划）。"""

    task_id: int
    title: str
    status: str
    progress: int
    priority: str
    planned_start_date: date | None
    planned_end_date: date | None
    estimated_hours: float | None
    risk_level: str = "none"
    risk_reasons: list[str] = []


class ReplanChange(CamelModel):
    """单条调整建议：改起止日期 / 改优先级 / 改预计工时。"""

    task_id: int
    action: str  # reschedule / reprioritize
    title: str = ""
    planned_start_date: date | None = None
    planned_end_date: date | None = None
    priority: str | None = None
    estimated_hours: float | None = None
    reason: str


class ReplanOut(CamelModel):
    id: int
    project_id: int
    trigger_type: str
    plan_content: str
    impact_summary: str
    changes: list[ReplanChange]
    original_tasks: list[ReplanTaskSnapshot]
    source: str  # deepseek / demo
    status: str  # pending / adopted / rejected
    created_at: datetime
    decided_at: datetime | None


class ReplanAdoptOut(CamelModel):
    replan: ReplanOut
    applied_count: int = 0


# ═══════════════════════════ v2：研究问题 ═══════════════════════════

QUESTION_STATUSES = ("open", "answered", "suspended")


class QuestionCreate(CamelModel):
    """创建研究问题（project_id 从路径获取，body 可不传）。"""

    project_id: int | None = Field(default=None, gt=0)
    content: str
    objective: str | None = None
    hypothesis: str | None = None
    status: str = "open"

    @field_validator("content")
    @classmethod
    def check_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("研究问题不能为空")
        if len(v) > 2000:
            raise ValueError("研究问题不能超过 2000 个字符")
        return v

    @field_validator("objective")
    @classmethod
    def check_objective(cls, v: str | None) -> str | None:
        return _check_optional_text(v, "研究目标", 2000)

    @field_validator("hypothesis")
    @classmethod
    def check_hypothesis(cls, v: str | None) -> str | None:
        return _check_optional_text(v, "研究假设", 2000)

    @field_validator("status")
    @classmethod
    def check_status(cls, v: str) -> str:
        if v not in QUESTION_STATUSES:
            raise ValueError("问题状态必须是 open（待解决）/ answered（已解答）/ suspended（挂起）之一")
        return v


class QuestionUpdate(CamelModel):
    """更新研究问题：所有字段可选。"""

    content: str | None = None
    objective: str | None = None
    hypothesis: str | None = None
    answer_summary: str | None = None
    status: str | None = None

    @field_validator("content")
    @classmethod
    def check_content(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("研究问题不能为空")
        if len(v) > 2000:
            raise ValueError("研究问题不能超过 2000 个字符")
        return v

    @field_validator("objective")
    @classmethod
    def check_objective(cls, v: str | None) -> str | None:
        return _check_optional_text(v, "研究目标", 2000)

    @field_validator("hypothesis")
    @classmethod
    def check_hypothesis(cls, v: str | None) -> str | None:
        return _check_optional_text(v, "研究假设", 2000)

    @field_validator("answer_summary")
    @classmethod
    def check_answer(cls, v: str | None) -> str | None:
        return _check_optional_text(v, "解答摘要", 5000)

    @field_validator("status")
    @classmethod
    def check_status(cls, v: str | None) -> str | None:
        if v is not None and v not in QUESTION_STATUSES:
            raise ValueError("问题状态必须是 open（待解决）/ answered（已解答）/ suspended（挂起）之一")
        return v


class QuestionOut(CamelModel):
    id: int
    project_id: int
    content: str
    objective: str | None
    hypothesis: str | None
    answer_summary: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class QuestionSummary(QuestionOut):
    """问题列表项：附带证据计数（卡片立场分布 + 实验数）。"""

    evidence_support: int = 0
    evidence_against: int = 0
    evidence_neutral: int = 0
    experiments_count: int = 0


# ═══════════════════════════ v2：文献研究卡片 ═══════════════════════════

EVIDENCE_TYPES = ("support", "against", "neutral")


class EvidenceSnippet(CamelModel):
    """原文证据片段（v2.1）：quote 为原文摘录（用户从文献中真实摘录），page 为页码（可空）。"""

    quote: str
    page: str | None = None

    @field_validator("quote")
    @classmethod
    def check_quote(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("证据片段原文不能为空")
        if len(v) > 500:
            raise ValueError("证据片段原文不能超过 500 个字符")
        return v

    @field_validator("page")
    @classmethod
    def check_page(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            return None
        if len(v) > 20:
            raise ValueError("页码不能超过 20 个字符")
        return v


def _check_evidence_snippets(v: list | None) -> list | None:
    """证据片段列表校验：最多 50 条。"""
    if v is None:
        return None
    if len(v) > 50:
        raise ValueError("证据片段最多 50 条")
    return v


class CardCreate(CamelModel):
    """手工创建研究卡片（字段全部可选，留空合法——不伪造；project_id 从路径获取）。"""

    project_id: int | None = Field(default=None, gt=0)
    document_id: int | None = Field(default=None, gt=0)
    question_id: int | None = Field(default=None, gt=0)
    title: str | None = None
    authors: str | None = None
    year: str | None = None
    research_question: str | None = None
    method: str | None = None
    materials_datasets: str | None = None
    metrics: str | None = None
    key_results: str | None = None
    innovations: str | None = None
    limitations: str | None = None
    relevance: str | None = None
    evidence_type: str = "neutral"
    evidence_snippets: list[EvidenceSnippet] | None = None

    @field_validator("title", "authors", "year", "research_question", "method",
                     "materials_datasets", "metrics", "key_results",
                     "innovations", "limitations", "relevance")
    @classmethod
    def check_text(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            return None
        if len(v) > 5000:
            raise ValueError("卡片字段不能超过 5000 个字符")
        return v

    @field_validator("evidence_type")
    @classmethod
    def check_evidence(cls, v: str) -> str:
        if v not in EVIDENCE_TYPES:
            raise ValueError("证据立场必须是 support（支持）/ against（反对）/ neutral（参考）之一")
        return v

    @field_validator("evidence_snippets")
    @classmethod
    def check_snippets(cls, v: list | None) -> list | None:
        return _check_evidence_snippets(v)


class CardUpdate(CamelModel):
    """人工修改卡片：所有字段可选。任何修改后 source 置为 manual。"""

    question_id: int | None = Field(default=None, gt=0)
    title: str | None = None
    authors: str | None = None
    year: str | None = None
    research_question: str | None = None
    method: str | None = None
    materials_datasets: str | None = None
    metrics: str | None = None
    key_results: str | None = None
    innovations: str | None = None
    limitations: str | None = None
    relevance: str | None = None
    evidence_type: str | None = None
    evidence_snippets: list[EvidenceSnippet] | None = None

    @field_validator("title", "authors", "year", "research_question", "method",
                     "materials_datasets", "metrics", "key_results",
                     "innovations", "limitations", "relevance")
    @classmethod
    def check_text(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            return None
        if len(v) > 5000:
            raise ValueError("卡片字段不能超过 5000 个字符")
        return v

    @field_validator("evidence_type")
    @classmethod
    def check_evidence(cls, v: str | None) -> str | None:
        if v is not None and v not in EVIDENCE_TYPES:
            raise ValueError("证据立场必须是 support（支持）/ against（反对）/ neutral（参考）之一")
        return v

    @field_validator("evidence_snippets")
    @classmethod
    def check_snippets(cls, v: list | None) -> list | None:
        return _check_evidence_snippets(v)


class CardOut(CamelModel):
    id: int
    project_id: int
    document_id: int | None
    question_id: int | None
    title: str | None
    authors: str | None
    year: str | None
    research_question: str | None
    method: str | None
    materials_datasets: str | None
    metrics: str | None
    key_results: str | None
    innovations: str | None
    limitations: str | None
    relevance: str | None
    evidence_type: str
    evidence_snippets: list[EvidenceSnippet]
    source: str
    created_at: datetime
    updated_at: datetime


class CardExtractOut(CamelModel):
    """AI 抽取卡片的结果：source=deepseek 真实抽取 / demo 演示模式（空模板）。"""

    card: CardOut
    warning: str = ""


class CardCompareOut(CamelModel):
    """卡片对比数据：按传入顺序返回的卡片列表（对比表由前端本地渲染）。"""

    cards: list[CardOut]


# ═══════════════════════════ v2：实验管理 ═══════════════════════════

EXPERIMENT_STATUSES = ("draft", "running", "done", "failed", "paused")


class MetricDef(CamelModel):
    """实验指标定义：名称 + 单位 + 方向（用于结果比较染色）。"""

    name: str
    unit: str = ""
    higher_is_better: bool = True

    @field_validator("name")
    @classmethod
    def check_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("指标名称不能为空")
        if len(v) > 100:
            raise ValueError("指标名称不能超过 100 个字符")
        return v


class ExperimentCreate(CamelModel):
    """创建实验（project_id 从路径获取）。"""

    project_id: int | None = Field(default=None, gt=0)
    question_id: int | None = Field(default=None, gt=0)
    title: str
    objective: str
    hypothesis: str | None = None
    variables: str | None = None
    control_conditions: str | None = None
    dataset: str | None = None
    model: str | None = None
    design: str | None = None
    config: dict | None = None
    metrics: list[MetricDef] | None = None
    status: str = "draft"

    @field_validator("title")
    @classmethod
    def check_title(cls, v: str) -> str:
        return _check_title(v)

    @field_validator("objective")
    @classmethod
    def check_objective(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("实验目的不能为空")
        if len(v) > 2000:
            raise ValueError("实验目的不能超过 2000 个字符")
        return v

    @field_validator("hypothesis")
    @classmethod
    def check_hypothesis(cls, v: str | None) -> str | None:
        return _check_optional_text(v, "假设", 2000)

    @field_validator("variables")
    @classmethod
    def check_variables(cls, v: str | None) -> str | None:
        return _check_optional_text(v, "实验变量", 5000)

    @field_validator("control_conditions")
    @classmethod
    def check_control(cls, v: str | None) -> str | None:
        return _check_optional_text(v, "对照条件", 5000)

    @field_validator("dataset")
    @classmethod
    def check_dataset(cls, v: str | None) -> str | None:
        return _check_optional_text(v, "数据集", 5000)

    @field_validator("model")
    @classmethod
    def check_model(cls, v: str | None) -> str | None:
        return _check_optional_text(v, "模型", 5000)

    @field_validator("design")
    @classmethod
    def check_design(cls, v: str | None) -> str | None:
        return _check_optional_text(v, "实验方案", 20000)

    @field_validator("config")
    @classmethod
    def check_config(cls, v: dict | None) -> dict | None:
        if v is None:
            return {}
        if len(str(v)) > 50000:
            raise ValueError("实验配置 JSON 不能超过 50000 个字符")
        return v

    @field_validator("status")
    @classmethod
    def check_status(cls, v: str) -> str:
        if v not in EXPERIMENT_STATUSES:
            raise ValueError("实验状态必须是 draft / running / done / failed / paused 之一")
        return v


class ExperimentUpdate(CamelModel):
    """更新实验：所有字段可选。"""

    question_id: int | None = Field(default=None, gt=0)
    title: str | None = None
    objective: str | None = None
    hypothesis: str | None = None
    variables: str | None = None
    control_conditions: str | None = None
    dataset: str | None = None
    model: str | None = None
    design: str | None = None
    config: dict | None = None
    metrics: list[MetricDef] | None = None
    status: str | None = None

    @field_validator("title")
    @classmethod
    def check_title(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return _check_title(v)

    @field_validator("objective")
    @classmethod
    def check_objective(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("实验目的不能为空")
        if len(v) > 2000:
            raise ValueError("实验目的不能超过 2000 个字符")
        return v

    @field_validator("hypothesis")
    @classmethod
    def check_hypothesis(cls, v: str | None) -> str | None:
        return _check_optional_text(v, "假设", 2000)

    @field_validator("variables")
    @classmethod
    def check_variables(cls, v: str | None) -> str | None:
        return _check_optional_text(v, "实验变量", 5000)

    @field_validator("control_conditions")
    @classmethod
    def check_control(cls, v: str | None) -> str | None:
        return _check_optional_text(v, "对照条件", 5000)

    @field_validator("dataset")
    @classmethod
    def check_dataset(cls, v: str | None) -> str | None:
        return _check_optional_text(v, "数据集", 5000)

    @field_validator("model")
    @classmethod
    def check_model(cls, v: str | None) -> str | None:
        return _check_optional_text(v, "模型", 5000)

    @field_validator("design")
    @classmethod
    def check_design(cls, v: str | None) -> str | None:
        return _check_optional_text(v, "实验方案", 20000)

    @field_validator("config")
    @classmethod
    def check_config(cls, v: dict | None) -> dict | None:
        if v is None:
            return None
        if len(str(v)) > 50000:
            raise ValueError("实验配置 JSON 不能超过 50000 个字符")
        return v

    @field_validator("status")
    @classmethod
    def check_status(cls, v: str | None) -> str | None:
        if v is not None and v not in EXPERIMENT_STATUSES:
            raise ValueError("实验状态必须是 draft / running / done / failed / paused 之一")
        return v


class ExperimentOut(CamelModel):
    id: int
    project_id: int
    question_id: int | None
    title: str
    objective: str
    hypothesis: str | None
    variables: str | None
    control_conditions: str | None
    dataset: str | None
    model: str | None
    design: str | None
    config: dict
    metrics: list[MetricDef]
    status: str
    run_count: int = 0
    last_run_at: datetime | None = None
    stalled: bool = False          # 进行中/设计中的实验超期无新记录（科研停滞提醒）
    created_at: datetime
    updated_at: datetime


class RunCreate(CamelModel):
    """新增实验运行记录（结构化结果 + 自由 JSON 兜底）。

    指标等结果由用户真实录入/上传，系统绝不生成虚假数值。
    config = 本次运行参数；results = 实际评价指标。
    """

    config: dict | None = None
    results: dict | None = None
    random_seed: int | None = None
    git_commit: str | None = None
    environment: dict | None = None
    log_path: str | None = None
    result_files: list[str] | None = None
    notes: str | None = None
    started_at: date | None = None
    finished_at: date | None = None

    @field_validator("config", "results", "environment")
    @classmethod
    def check_json(cls, v: dict | None) -> dict | None:
        if v is None:
            return {}
        if len(str(v)) > 50000:
            raise ValueError("运行记录 JSON 不能超过 50000 个字符")
        return v

    @field_validator("random_seed")
    @classmethod
    def check_seed(cls, v: int | None) -> int | None:
        if v is None:
            return v
        if v < 0 or v > 2**31 - 1:
            raise ValueError("随机种子必须是非负整数且不超过 2147483647")
        return v

    @field_validator("git_commit")
    @classmethod
    def check_commit(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            return None
        if len(v) > 64:
            raise ValueError("Git Commit 不能超过 64 个字符")
        return v

    @field_validator("log_path")
    @classmethod
    def check_log_path(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            return None
        if len(v) > 500:
            raise ValueError("日志路径不能超过 500 个字符")
        return v

    @field_validator("result_files")
    @classmethod
    def check_result_files(cls, v: list | None) -> list | None:
        if v is None:
            return []
        if len(v) > 50:
            raise ValueError("结果文件路径最多 50 条")
        cleaned: list[str] = []
        for item in v:
            if not isinstance(item, str):
                raise ValueError("结果文件路径必须是字符串列表")
            item = item.strip()
            if not item:
                continue
            if len(item) > 500:
                raise ValueError("结果文件路径不能超过 500 个字符")
            cleaned.append(item)
        return cleaned

    @field_validator("notes")
    @classmethod
    def check_notes(cls, v: str | None) -> str | None:
        return _check_optional_text(v, "运行备注", 10000)

    @model_validator(mode="after")
    def check_dates(self):
        if self.started_at and self.finished_at and self.finished_at < self.started_at:
            raise ValueError("结束日期不能早于开始日期")
        return self


class RunUpdate(CamelModel):
    """修改运行记录：所有字段可选。"""

    config: dict | None = None
    results: dict | None = None
    random_seed: int | None = None
    git_commit: str | None = None
    environment: dict | None = None
    log_path: str | None = None
    result_files: list[str] | None = None
    notes: str | None = None
    started_at: date | None = None
    finished_at: date | None = None

    @field_validator("config", "results", "environment")
    @classmethod
    def check_json(cls, v: dict | None) -> dict | None:
        if v is None:
            return None
        if len(str(v)) > 50000:
            raise ValueError("运行记录 JSON 不能超过 50000 个字符")
        return v

    @field_validator("random_seed")
    @classmethod
    def check_seed(cls, v: int | None) -> int | None:
        if v is None:
            return v
        if v < 0 or v > 2**31 - 1:
            raise ValueError("随机种子必须是非负整数且不超过 2147483647")
        return v

    @field_validator("git_commit")
    @classmethod
    def check_commit(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            return None
        if len(v) > 64:
            raise ValueError("Git Commit 不能超过 64 个字符")
        return v

    @field_validator("log_path")
    @classmethod
    def check_log_path(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            return None
        if len(v) > 500:
            raise ValueError("日志路径不能超过 500 个字符")
        return v

    @field_validator("result_files")
    @classmethod
    def check_result_files(cls, v: list | None) -> list | None:
        if v is None:
            return None
        if len(v) > 50:
            raise ValueError("结果文件路径最多 50 条")
        cleaned: list[str] = []
        for item in v:
            if not isinstance(item, str):
                raise ValueError("结果文件路径必须是字符串列表")
            item = item.strip()
            if not item:
                continue
            if len(item) > 500:
                raise ValueError("结果文件路径不能超过 500 个字符")
            cleaned.append(item)
        return cleaned

    @field_validator("notes")
    @classmethod
    def check_notes(cls, v: str | None) -> str | None:
        return _check_optional_text(v, "运行备注", 10000)


class RunOut(CamelModel):
    id: int
    experiment_id: int
    run_no: int
    config: dict
    results: dict
    random_seed: int | None
    git_commit: str | None
    environment: dict
    log_path: str | None
    result_files: list[str]
    notes: str | None
    attachments: list[str]
    started_at: date | None
    finished_at: date | None
    created_at: datetime


class ExperimentDetailOut(CamelModel):
    experiment: ExperimentOut
    runs: list[RunOut]


class CompareRow(CamelModel):
    """同实验 run 对比：一行 = 一次运行，values 按指标名对齐（缺失为 null）。"""

    run_id: int
    run_no: int
    started_at: date | None
    values: dict


class ExperimentCompareOut(CamelModel):
    experiment_id: int
    metric_names: list[str]
    rows: list[CompareRow]


class MetricPoint(CamelModel):
    """跨实验指标总览中的单个数据点。"""

    experiment_id: int
    experiment_title: str
    experiment_status: str
    run_id: int
    run_no: int
    value: float


class MetricOverviewItem(CamelModel):
    name: str
    unit: str
    higher_is_better: bool
    points: list[MetricPoint]


class MetricsOverviewOut(CamelModel):
    metrics: list[MetricOverviewItem]


# ═══════════════════════════ v2：AI 实验分析 ═══════════════════════════

SUGGESTION_TYPES = ("new_task", "new_experiment", "read_literature", "modify_design")


class SuggestionOut(CamelModel):
    """分析给出的下一步建议。"""

    type: str
    content: str
    reason: str
    converted: bool = False    # 是否已转为任务/实验（防重复转换）


class AnalysisOut(CamelModel):
    id: int
    project_id: int
    experiment_id: int
    question_id: int | None
    run_ids: list[int]
    content: str
    suggestions: list[SuggestionOut]
    source: str                # deepseek / manual
    created_at: datetime


class AnalysisNoteCreate(CamelModel):
    """手工分析笔记（无 Key 或用户自选时的人工替代，不伪装 AI）。"""

    content: str

    @field_validator("content")
    @classmethod
    def check_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("分析内容不能为空")
        if len(v) > 20000:
            raise ValueError("分析内容不能超过 20000 个字符")
        return v


# ═══════════════════════════ v2.1：科研决策记录 ═══════════════════════════

def _check_run_ids(v: list | None) -> list:
    """关联运行记录 id 列表校验：非空、去重、最多 100 个。"""
    if not v:
        raise ValueError("请至少选择一条关联的实验运行记录")
    if len(v) > 100:
        raise ValueError("关联运行记录最多 100 条")
    cleaned: list[int] = []
    for item in v:
        if isinstance(item, bool) or not isinstance(item, int):
            raise ValueError("关联运行记录必须是整数 id 列表")
        if item <= 0:
            raise ValueError("关联运行记录 id 必须大于 0")
        if item not in cleaned:
            cleaned.append(item)
    return cleaned


def _check_suggestion_list(v: list | None) -> list:
    """下一步建议列表校验：最多 10 条。"""
    if v is None:
        return []
    if len(v) > 10:
        raise ValueError("下一步研究建议最多 10 条")
    cleaned: list[str] = []
    for item in v:
        if not isinstance(item, str):
            raise ValueError("下一步研究建议必须是字符串列表")
        item = item.strip()
        if not item:
            continue
        if len(item) > 500:
            raise ValueError("单条建议不能超过 500 个字符")
        cleaned.append(item)
    return cleaned


class DecisionCreate(CamelModel):
    """创建科研决策记录：所有内容由研究者本人真实录入。"""

    run_ids: list[int]
    observations: str
    interpretation: str | None = None
    supports_hypothesis: bool | None = None   # None = 待定/无法判断
    unknowns: str | None = None
    next_suggestions: list[str] | None = None

    @field_validator("run_ids")
    @classmethod
    def check_run_ids(cls, v: list) -> list:
        return _check_run_ids(v)

    @field_validator("observations")
    @classmethod
    def check_observations(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("观察到的事实不能为空")
        if len(v) > 10000:
            raise ValueError("观察到的事实不能超过 10000 个字符")
        return v

    @field_validator("interpretation")
    @classmethod
    def check_interpretation(cls, v: str | None) -> str | None:
        return _check_optional_text(v, "分析解释", 10000)

    @field_validator("unknowns")
    @classmethod
    def check_unknowns(cls, v: str | None) -> str | None:
        return _check_optional_text(v, "未知因素", 5000)

    @field_validator("next_suggestions")
    @classmethod
    def check_suggestions(cls, v: list | None) -> list:
        return _check_suggestion_list(v)


class DecisionUpdate(CamelModel):
    """更新科研决策记录：所有字段可选。"""

    run_ids: list[int] | None = None
    observations: str | None = None
    interpretation: str | None = None
    supports_hypothesis: bool | None = None
    unknowns: str | None = None
    next_suggestions: list[str] | None = None

    @field_validator("run_ids")
    @classmethod
    def check_run_ids(cls, v: list | None) -> list | None:
        if v is None:
            return None
        return _check_run_ids(v)

    @field_validator("observations")
    @classmethod
    def check_observations(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("观察到的事实不能为空")
        if len(v) > 10000:
            raise ValueError("观察到的事实不能超过 10000 个字符")
        return v

    @field_validator("interpretation")
    @classmethod
    def check_interpretation(cls, v: str | None) -> str | None:
        return _check_optional_text(v, "分析解释", 10000)

    @field_validator("unknowns")
    @classmethod
    def check_unknowns(cls, v: str | None) -> str | None:
        return _check_optional_text(v, "未知因素", 5000)

    @field_validator("next_suggestions")
    @classmethod
    def check_suggestions(cls, v: list | None) -> list | None:
        if v is None:
            return None
        return _check_suggestion_list(v)


class DecisionOut(CamelModel):
    id: int
    project_id: int
    experiment_id: int
    run_ids: list[int]
    observations: str
    interpretation: str | None
    supports_hypothesis: bool | None
    unknowns: str | None
    next_suggestions: list[str]
    created_at: datetime
    updated_at: datetime


# ═══════════════════════════ v2.2：AI 研究分析 ═══════════════════════════

HYPOTHESIS_STATUSES = ("support", "not_support", "insufficient_evidence")


class ObservedFactOut(CamelModel):
    """实验事实：必须引用真实存在的运行记录 id（后端校验）。"""

    experiment_run_id: int
    content: str


class PaperEvidenceOut(CamelModel):
    """文献证据：必须引用真实存在的卡片与片段（后端校验），页码以数据库为准。"""

    paper_note_id: int
    snippet_id: str        # 形如 "卡片id-片段序号"
    page: str | None       # 数据库中的真实页码
    quote: str             # 片段原文（数据库中的真实摘录）
    statement: str         # 该证据说明了什么


class NextExperimentOut(CamelModel):
    """下一步实验建议（AI 提出，用户确认后才能转为任务）。"""

    objective: str
    hypothesis: str
    changed_variables: str = ""
    fixed_conditions: str = ""
    metrics: str = ""
    expected_observation: str = ""
    risks: str = ""
    estimated_effort: str = ""
    converted: bool = False
    rejected: bool = False   # 用户拒绝后置位，不再可采纳


class SuggestionAdoptRequest(CamelModel):
    """用户确认采纳建议（可先修改）：创建 Experiment 并生成关联 Task。

    科研决策与执行计划分层：本请求的全部字段由用户确认/修改后提交，
    AI 只负责给出初始建议；用户提交前系统不做任何创建或修改。
    """

    objective: str
    hypothesis: str
    variables: str | None = None
    required_data: str | None = None
    preconditions: str | None = None
    estimated_hours: float = Field(allow_inf_nan=False)
    planned_start_date: date
    planned_end_date: date
    dependencies: list[int] | None = None

    @field_validator("objective")
    @classmethod
    def check_objective(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("实验目的不能为空")
        if len(v) > 1000:
            raise ValueError("实验目的不能超过 1000 个字符")
        return v

    @field_validator("hypothesis")
    @classmethod
    def check_hypothesis(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("研究假设不能为空")
        if len(v) > 1000:
            raise ValueError("研究假设不能超过 1000 个字符")
        return v

    @field_validator("variables")
    @classmethod
    def check_variables(cls, v: str | None) -> str | None:
        return _check_optional_text(v, "实验变量", 2000)

    @field_validator("required_data")
    @classmethod
    def check_required_data(cls, v: str | None) -> str | None:
        return _check_optional_text(v, "所需数据", 2000)

    @field_validator("preconditions")
    @classmethod
    def check_preconditions(cls, v: str | None) -> str | None:
        return _check_optional_text(v, "前置条件", 2000)

    @field_validator("estimated_hours")
    @classmethod
    def check_hours(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("预计工时必须大于 0")
        if v > 1000:
            raise ValueError("预计工时不能超过 1000 小时")
        return v

    @field_validator("dependencies")
    @classmethod
    def check_dependencies(cls, v: list | None) -> list | None:
        if v is None:
            return []
        if len(v) > 20:
            raise ValueError("依赖任务最多 20 个")
        cleaned: list[int] = []
        for item in v:
            if isinstance(item, bool) or not isinstance(item, int) or item <= 0:
                raise ValueError("依赖任务必须是正整数 id 列表")
            if item not in cleaned:
                cleaned.append(item)
        return cleaned

    @model_validator(mode="after")
    def check_dates(self):
        if self.planned_end_date < self.planned_start_date:
            raise ValueError("计划截止日期不能早于计划开始日期")
        return self


class SuggestionRejectRequest(CamelModel):
    """用户拒绝建议（可选填写原因）。"""

    reason: str | None = None

    @field_validator("reason")
    @classmethod
    def check_reason(cls, v: str | None) -> str | None:
        return _check_optional_text(v, "拒绝原因", 2000)


class SuggestionModifyRequest(CamelModel):
    """用户修改建议（不采纳，仅保存修改并留档）。"""

    objective: str | None = None
    hypothesis: str | None = None
    changed_variables: str | None = None
    fixed_conditions: str | None = None
    metrics: str | None = None
    expected_observation: str | None = None
    risks: str | None = None
    estimated_effort: str | None = None

    @field_validator("objective", "hypothesis", "changed_variables", "fixed_conditions",
                     "metrics", "expected_observation", "risks", "estimated_effort")
    @classmethod
    def check_text(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            return None
        if len(v) > 1000:
            raise ValueError("建议字段不能超过 1000 个字符")
        return v


class ResearchActionLogOut(CamelModel):
    """科研决策操作历史。"""

    id: int
    project_id: int
    analysis_id: int | None
    suggestion_index: int
    action: str            # adopted / rejected / modified
    payload: dict
    task_id: int | None
    experiment_id: int | None
    created_at: datetime


class SuggestionAdoptOut(CamelModel):
    """采纳结果：创建的实验 + 关联任务 + 历史记录。"""

    experiment: ExperimentOut
    task: TaskOut
    log: ResearchActionLogOut


class ResearchAnalysisOut(CamelModel):
    id: int
    project_id: int
    question_id: int | None
    experiment_ids: list[int]
    run_ids: list[int]
    card_ids: list[int]
    observed_facts: list[ObservedFactOut]
    paper_evidence: list[PaperEvidenceOut]
    stats: dict                # Python 确定性计算的统计（min/max/mean/best/delta）
    interpretation: str
    hypothesis_status: str
    uncertainty: str
    next_experiments: list[NextExperimentOut]
    source: str                # deepseek / demo
    warning: str = ""          # 演示模式提示等
    created_at: datetime


class ResearchAnalysisToTaskOut(CamelModel):
    """分析建议转任务的响应。"""

    task: TaskOut
    analysis_id: int
