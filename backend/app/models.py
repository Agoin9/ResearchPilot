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
    """任务表：两级结构（里程碑 + 普通任务），parent_id 为空表示里程碑。"""

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
