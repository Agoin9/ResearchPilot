"""SQLAlchemy 表模型：严格沿用 PRD §5 确定的 4 张表结构。

关系：project 1─N task 1─N progress_record，project 1─N replan_history，
task 自关联（parent_id 表示所属里程碑）。
"""
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Project(Base):
    """项目表：科研目标 + 截止时间 + 每周可用时间。"""

    __tablename__ = "project"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)          # 项目名称
    goal: Mapped[str] = mapped_column(Text, nullable=False)                 # 科研目标描述
    deadline: Mapped[date] = mapped_column(Date, nullable=False)            # 截止日期
    weekly_hours: Mapped[float] = mapped_column(Float, nullable=False)      # 每周可用小时数
    status: Mapped[str] = mapped_column(                                   # active/completed/paused
        String(20), nullable=False, default="active"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

    tasks: Mapped[list["Task"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    replan_histories: Mapped[list["ReplanHistory"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Task(Base):
    """任务表：两级结构（里程碑 + 普通任务），parent_id 为空表示里程碑。

    v2 新增 source_type / source_id：任务可来自研究问题、文献卡片、
    实验分析建议等科研实体（null = 手工创建），形成"决策 → 任务"闭环。
    """

    __tablename__ = "task"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("task.id", ondelete="CASCADE"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(                                   # todo/doing/done
        String(20), nullable=False, default="todo"
    )
    priority: Mapped[str] = mapped_column(                                 # high/medium/low
        String(20), nullable=False, default="medium"
    )
    planned_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    planned_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    estimated_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 0~100
    is_milestone: Mapped[bool] = mapped_column(Integer, nullable=False, default=0)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # v2 任务来源：question / literature_card / experiment_analysis / manual（null 视为手工）
    source_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    source_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # v2.3 科研任务关联：所属实验 / 所属研究问题 / 依赖关系
    experiment_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("experiment.id", ondelete="SET NULL"), nullable=True
    )
    question_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("research_question.id", ondelete="SET NULL"), nullable=True
    )
    dependencies_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # 依赖任务 id 列表
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

    project: Mapped["Project"] = relationship(back_populates="tasks")
    parent: Mapped["Task | None"] = relationship(
        back_populates="children", remote_side="Task.id", passive_deletes=True
    )
    children: Mapped[list["Task"]] = relationship(
        back_populates="parent",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    progress_records: Mapped[list["ProgressRecord"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ProgressRecord(Base):
    """进度记录表：每次更新进度写一条，历史记录永不删除（画进度曲线用）。"""

    __tablename__ = "progress_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("task.id", ondelete="CASCADE"), nullable=False
    )
    progress: Mapped[int] = mapped_column(Integer, nullable=False)          # 本次更新后的累计进度 0~100
    hours_spent: Mapped[float | None] = mapped_column(Float, nullable=True)  # 本次投入小时数
    note: Mapped[str | None] = mapped_column(Text, nullable=True)           # 备注
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    task: Mapped["Task"] = relationship(back_populates="progress_records")


class ReplanHistory(Base):
    """重规划历史表：AI 重规划方案留档（暂未接入 DeepSeek，先建表）。"""

    __tablename__ = "replan_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    trigger_type: Mapped[str] = mapped_column(String(20), nullable=False)   # manual/risk
    risk_tasks_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    plan_content: Mapped[str] = mapped_column(Text, nullable=False)
    changes_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(                                   # pending/adopted/rejected
        String(20), nullable=False, default="pending"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="replan_histories")


class Document(Base):
    """文献表：上传的 PDF（提取全文后按段切块存入 doc_chunk）。"""

    __tablename__ = "document"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    project: Mapped["Project"] = relationship()
    chunks: Mapped[list["DocChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", passive_deletes=True
    )
    qas: Mapped[list["DocQa"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", passive_deletes=True
    )


class DocChunk(Base):
    """文献切片表：每段约 500~800 字，问答检索的最小单元。"""

    __tablename__ = "doc_chunk"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("document.id", ondelete="CASCADE"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)  # 从 1 开始
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    document: Mapped["Document"] = relationship(back_populates="chunks")


class DocQa(Base):
    """文献问答表：问题、答案、引用片段、置信度；is_saved 标记保存为笔记。"""

    __tablename__ = "doc_qa"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    document_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("document.id", ondelete="CASCADE"), nullable=False
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    citations_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="demo")  # deepseek/demo
    is_saved: Mapped[bool] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    project: Mapped["Project"] = relationship()
    document: Mapped["Document"] = relationship(back_populates="qas")


class Report(Base):
    """组会周报与导师汇报表：Markdown 内容，可编辑保存、导出。"""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    report_type: Mapped[str] = mapped_column(String(20), nullable=False, default="meeting")  # meeting/supervisor
    week_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    week_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="demo")  # deepseek/demo
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

    project: Mapped["Project"] = relationship()


# ══════════════════════════ v2：科研工作台实体 ══════════════════════════
# 科研闭环：研究问题 → 文献证据(卡片) → 实验设计 → 实验运行记录 → 结果分析 → 决策转任务


class ResearchQuestion(Base):
    """研究问题表：科研闭环的起点，可关联证据卡片与实验。

    v2.1 新增 objective（研究目标）与 hypothesis（研究假设），
    与问题描述共同构成完整的研究问题定义。
    """

    __tablename__ = "research_question"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)              # 问题描述
    objective: Mapped[str | None] = mapped_column(Text, nullable=True)      # 研究目标（v2.1）
    hypothesis: Mapped[str | None] = mapped_column(Text, nullable=True)     # 研究假设（v2.1）
    answer_summary: Mapped[str | None] = mapped_column(Text, nullable=True)  # 解答摘要（人工填写）
    status: Mapped[str] = mapped_column(                                   # open/answered/suspended
        String(20), nullable=False, default="open"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

    project: Mapped["Project"] = relationship()


class LiteratureCard(Base):
    """文献研究卡片表（即 PaperNote）：从已上传 PDF 结构化抽取的证据，可人工修正、可横向对比。

    文献被删除时卡片保留（document_id 置空），保护用户整理成果。
    v2.1 新增 innovations（创新点）与 evidence_snippets_json（原文证据片段及页码，
    由用户从原文中摘录，支持溯源核对）。
    """

    __tablename__ = "literature_card"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    document_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("document.id", ondelete="SET NULL"), nullable=True
    )
    question_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("research_question.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)          # 论文标题
    authors: Mapped[str | None] = mapped_column(String(500), nullable=True)        # 作者（抽取不到留空）
    year: Mapped[str | None] = mapped_column(String(10), nullable=True)            # 年份
    research_question: Mapped[str | None] = mapped_column(Text, nullable=True)     # 该文研究的问题
    method: Mapped[str | None] = mapped_column(Text, nullable=True)                # 方法简述
    materials_datasets: Mapped[str | None] = mapped_column(Text, nullable=True)    # 数据集/材料/对象
    metrics: Mapped[str | None] = mapped_column(Text, nullable=True)               # 评价指标
    key_results: Mapped[str | None] = mapped_column(Text, nullable=True)           # 主要结果（可多条）
    innovations: Mapped[str | None] = mapped_column(Text, nullable=True)           # 创新点（v2.1）
    limitations: Mapped[str | None] = mapped_column(Text, nullable=True)           # 局限
    relevance: Mapped[str | None] = mapped_column(Text, nullable=True)             # 与研究的关联
    evidence_type: Mapped[str] = mapped_column(                                   # support/against/neutral
        String(20), nullable=False, default="neutral"                              # 立场由用户人工标记
    )
    evidence_snippets_json: Mapped[str] = mapped_column(                           # 原文证据片段及页码（v2.1）
        Text, nullable=False, default="[]"
    )
    source: Mapped[str] = mapped_column(                                          # deepseek/demo/manual
        String(20), nullable=False, default="manual"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

    project: Mapped["Project"] = relationship()


class Experiment(Base):
    """实验表：目标/假设/方案/指标定义。执行发生在用户的实验室/服务器上，
    系统只负责设计管理、结果记录与比较（不集成训练执行平台）。

    v2.1 新增 variables（实验变量）/ control_conditions（对照条件）/
    dataset（数据集）/ model（模型）/ config_json（实验配置），
    与 design（方案 Markdown）共同完整描述实验设计。
    """

    __tablename__ = "experiment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("research_question.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)           # 实验目的
    hypothesis: Mapped[str | None] = mapped_column(Text, nullable=True)    # 待验证假设（可空）
    variables: Mapped[str | None] = mapped_column(Text, nullable=True)     # 实验变量（v2.1）
    control_conditions: Mapped[str | None] = mapped_column(Text, nullable=True)  # 对照条件（v2.1）
    dataset: Mapped[str | None] = mapped_column(Text, nullable=True)       # 数据集（v2.1）
    model: Mapped[str | None] = mapped_column(Text, nullable=True)         # 模型（v2.1）
    design: Mapped[str | None] = mapped_column(Text, nullable=True)        # 方案（Markdown）
    config_json: Mapped[str] = mapped_column(                              # 实验配置（v2.1）
        Text, nullable=False, default="{}"
    )
    metrics_json: Mapped[str] = mapped_column(                             # 指标定义列表
        Text, nullable=False, default="[]"
    )
    status: Mapped[str] = mapped_column(                                   # draft/running/done/failed/paused
        String(20), nullable=False, default="draft"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

    project: Mapped["Project"] = relationship()
    runs: Mapped[list["ExperimentRun"]] = relationship(
        back_populates="experiment",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ExperimentRun(Base):
    """实验运行记录表：一次实验的每次真实执行（条件/结果/备注/附件）。

    v2.1 新增 random_seed（随机种子）/ git_commit（代码提交）/
    environment_json（环境信息）/ log_path（日志路径）/
    result_files_json（结果文件路径）。字段映射：
    config_json = 本次运行参数，results_json = 实际评价指标（均为用户真实录入）。
    """

    __tablename__ = "experiment_run"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    experiment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("experiment.id", ondelete="CASCADE"), nullable=False
    )
    run_no: Mapped[int] = mapped_column(Integer, nullable=False)          # 第几次运行（同实验内自增）
    random_seed: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 随机种子（v2.1）
    git_commit: Mapped[str | None] = mapped_column(String(64), nullable=True)  # 代码 Git Commit（v2.1）
    environment_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")  # 环境信息（v2.1）
    config_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")   # 本次运行参数
    results_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")  # 实际评价指标
    log_path: Mapped[str | None] = mapped_column(String(500), nullable=True)   # 日志路径（v2.1）
    result_files_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # 结果文件路径（v2.1）
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)        # 现象/问题/观察
    attachments_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # 附件文件名列表
    started_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    finished_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    experiment: Mapped["Experiment"] = relationship(back_populates="runs")


class ExperimentAnalysis(Base):
    """AI 分析记录表：只基于真实录入的运行记录生成，分析与建议可人工修正。"""

    __tablename__ = "experiment_analysis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    experiment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("experiment.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("research_question.id", ondelete="SET NULL"), nullable=True
    )
    run_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # 依据哪些真实 run
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")         # 分析正文（Markdown）
    suggestions_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # 结构化建议
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="manual")  # deepseek/manual
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    project: Mapped["Project"] = relationship()


class ResearchAnalysis(Base):
    """AI 研究分析表（v2.2）：按研究问题聚合真实数据（文献卡片/实验/运行记录）后，
    由 DeepSeek 生成结构化分析。所有引用（run id / 卡片 id / 片段 id）均经后端校验，
    统计数值由 Python 确定性计算，AI 只负责解释与建议。
    无 Key 时生成演示模板（source=demo，统计值仍为真实计算）。
    """

    __tablename__ = "research_analysis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("research_question.id", ondelete="SET NULL"), nullable=True
    )
    # 分析时的数据快照（溯源：哪些实验/运行记录/文献卡片参与了本次分析）
    experiment_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    run_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    card_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    observed_facts_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")    # 实验事实（带 run id）
    paper_evidence_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")    # 文献证据（带卡片/片段 id）
    stats_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")             # 后端确定性计算的统计
    interpretation: Mapped[str] = mapped_column(Text, nullable=False, default="")           # 解释（标注为推测）
    hypothesis_status: Mapped[str] = mapped_column(String(30), nullable=False, default="insufficient_evidence")  # support/not_support/insufficient_evidence
    uncertainty: Mapped[str] = mapped_column(Text, nullable=False, default="")              # 不确定性与数据不足
    next_experiments_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # 下一步实验建议（≤3）
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="manual")       # deepseek/demo
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    project: Mapped["Project"] = relationship()


class ResearchActionLog(Base):
    """科研决策操作历史表（v2.3）：记录对分析建议的采纳 / 拒绝 / 修改。

    科研决策与执行计划分层：AI 建议只是起点，用户的每次操作（含修改后的
    采纳内容）都留档，可回溯"当时为什么这样决定"。
    """

    __tablename__ = "research_action_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    analysis_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("research_analysis.id", ondelete="SET NULL"), nullable=True
    )
    suggestion_index: Mapped[int] = mapped_column(Integer, nullable=False)  # 建议序号
    action: Mapped[str] = mapped_column(String(20), nullable=False)         # adopted / rejected / modified
    payload_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")  # 操作内容快照
    task_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("task.id", ondelete="SET NULL"), nullable=True
    )
    experiment_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("experiment.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    project: Mapped["Project"] = relationship()


class ResearchDecision(Base):
    """科研决策记录表（v2.1 新增）：研究者本人基于真实实验记录做出的判断。

    与 experiment_analysis（AI 生成的分析）不同，本表记录的是人做出的决策：
    观察到的事实、分析解释、是否支持假设、未知因素、下一步研究建议。
    所有内容由用户真实录入，系统不做任何生成或填充。
    """

    __tablename__ = "research_decision"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    experiment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("experiment.id", ondelete="CASCADE"), nullable=False
    )
    run_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # 关联的实验记录 id
    observations: Mapped[str] = mapped_column(Text, nullable=False)       # 观察到的事实
    interpretation: Mapped[str | None] = mapped_column(Text, nullable=True)  # 分析解释
    supports_hypothesis: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 是否支持假设：1 支持 / 0 不支持 / NULL 待定
    unknowns: Mapped[str | None] = mapped_column(Text, nullable=True)      # 未知因素
    next_suggestions_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # 下一步研究建议
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

    project: Mapped["Project"] = relationship()
