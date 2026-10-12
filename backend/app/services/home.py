"""首页聚合数据：统计卡片、项目列表、风险任务、趋势图、状态分布。"""
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ProgressRecord, Project, Task
from app.schemas import (
    HomeOut,
    HomeStats,
    RiskTaskItem,
    StatusSlice,
    TrendPoint,
)
from app.services.risk import RISK_HIGH, RISK_MEDIUM, RISK_NONE, compute_task_risk
from app.services.serializers import build_project_summary

STATUS_LABELS = ("已完成", "进行中", "待开始")


def get_home(db: Session, today: date | None = None) -> HomeOut:
    today = today or date.today()

    projects = db.scalars(
        select(Project).order_by(Project.created_at.desc())
    ).all()
    all_tasks = db.scalars(select(Task).order_by(Task.id)).all()
    tasks_by_project: dict[int, list[Task]] = {}
    for task in all_tasks:
        tasks_by_project.setdefault(task.project_id, []).append(task)

    summaries = [
        build_project_summary(p, tasks_by_project.get(p.id, []), today)
        for p in projects
    ]

    # 风险任务列表（高风险在前）
    risk_items: list[RiskTaskItem] = []
    for task in all_tasks:
        level, reason = compute_task_risk(task, today)
        if level == RISK_NONE:
            continue
        project = next(p for p in projects if p.id == task.project_id)
        risk_items.append(
            RiskTaskItem(
                id=task.id,
                project_id=task.project_id,
                task_title=task.title,
                project_name=project.name,
                level=level,
                reason=reason,
            )
        )
    risk_items.sort(key=lambda item: 0 if item.level == RISK_HIGH else 1)

    # 近 7 天投入时间 vs 上 7 天（基于进度记录）
    week_start = today - timedelta(days=6)
    prev_start = week_start - timedelta(days=7)
    records = db.scalars(select(ProgressRecord)).all()
    weekly_spent = sum(
        r.hours_spent or 0 for r in records if r.created_at.date() >= week_start
    )
    prev_spent = sum(
        r.hours_spent or 0
        for r in records
        if prev_start <= r.created_at.date() < week_start
    )

    # 近 7 天每日完成任务数（按任务完成时的 updated_at 归日）
    done_dates: list[date] = []
    for task in all_tasks:
        if task.status == "done" and task.updated_at:
            done_dates.append(task.updated_at.date())
    trend = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        trend.append(
            TrendPoint(
                date=day.strftime("%m-%d"),
                completed=sum(1 for d in done_dates if d == day),
            )
        )

    # 任务状态分布
    done_count = sum(1 for t in all_tasks if t.status == "done")
    doing_count = sum(1 for t in all_tasks if t.status == "doing")
    todo_count = sum(1 for t in all_tasks if t.status == "todo")

    return HomeOut(
        stats=HomeStats(
            active_projects=sum(1 for p in projects if p.status == "active"),
            todo_tasks=todo_count + doing_count,
            weekly_hours_spent=round(weekly_spent, 1),
            weekly_hours_delta=round(weekly_spent - prev_spent, 1),
            risk_task_count=len(risk_items),
        ),
        projects=summaries,
        risk_tasks=risk_items,
        trend=trend,
        distribution=[
            StatusSlice(name=STATUS_LABELS[0], value=done_count),
            StatusSlice(name=STATUS_LABELS[1], value=doing_count),
            StatusSlice(name=STATUS_LABELS[2], value=todo_count),
        ],
    )
