"""周报生成：近 7 天科研活动聚合 + AI 周报正文（DeepSeek，无 Key 时用模板）。"""
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai_client import DeepSeekClient
from app.config import DEEPSEEK_API_KEY
from app.models import ProgressRecord, Project, Task
from app.schemas import (
    WeeklyCompletedTask,
    WeeklyProgressItem,
    WeeklyProjectReport,
    WeeklyReportOut,
    WeeklyStats,
)

WEEK_DAYS = 7


def get_weekly_report(db: Session, today: date | None = None) -> WeeklyReportOut:
    """聚合近 7 天（含今天）的科研活动：完成任务、进度记录、投入小时。"""
    today = today or date.today()
    week_start = today - timedelta(days=WEEK_DAYS - 1)

    projects = db.scalars(select(Project).order_by(Project.id)).all()
    tasks = db.scalars(select(Task)).all()
    records = db.scalars(select(ProgressRecord).order_by(ProgressRecord.created_at)).all()

    done_by_id = {
        t.id: t
        for t in tasks
        if t.status == "done" and t.updated_at and week_start <= t.updated_at.date() <= today
    }
    records_in_week = [r for r in records if week_start <= r.created_at.date() <= today]

    project_reports: list[WeeklyProjectReport] = []
    for project in projects:
        completed = [
            WeeklyCompletedTask(
                id=t.id, title=t.title, completed_at=t.updated_at
            )
            for t in done_by_id.values()
            if t.project_id == project.id
        ]
        progress = [
            WeeklyProgressItem(
                task_title=task_title(r.task_id, tasks),
                progress=r.progress,
                hours_spent=r.hours_spent,
                note=r.note,
                created_at=r.created_at,
            )
            for r in records_in_week
            if r.task_id in task_ids_of(project.id, tasks)
        ]
        if completed or progress:
            project_reports.append(
                WeeklyProjectReport(
                    project_id=project.id,
                    project_name=project.name,
                    completed_tasks=completed,
                    progress_records=progress,
                )
            )

    return WeeklyReportOut(
        week_start=week_start,
        week_end=today,
        stats=WeeklyStats(
            tasks_completed=len(done_by_id),
            hours_spent=round(sum(r.hours_spent or 0 for r in records_in_week), 1),
            progress_updates=len(records_in_week),
        ),
        projects=project_reports,
    )


def task_ids_of(project_id: int, tasks: list[Task]) -> set[int]:
    return {t.id for t in tasks if t.project_id == project_id}


def task_title(task_id: int, tasks: list[Task]) -> str:
    for t in tasks:
        if t.id == task_id:
            return t.title
    return f"任务#{task_id}"


# ═══════════════════════ AI 周报正文 ═══════════════════════

def build_report_messages(weekly: WeeklyReportOut) -> list[dict]:
    lines = [
        f"统计周期：{weekly.week_start.isoformat()} ~ {weekly.week_end.isoformat()}",
        f"本周完成任务数：{weekly.stats.tasks_completed}",
        f"本周投入小时数：{weekly.stats.hours_spent}",
        f"本周进度更新次数：{weekly.stats.progress_updates}",
        "",
        "各项目明细：",
    ]
    for p in weekly.projects:
        lines.append(f"- 项目「{p.project_name}」：")
        for t in p.completed_tasks:
            lines.append(f"  完成任务：{t.title}（完成于 {t.completed_at.date().isoformat()}）")
        for r in p.progress_records:
            note = f"，备注：{r.note}" if r.note else ""
            hours = f"，投入 {r.hours_spent} 小时" if r.hours_spent else ""
            lines.append(
                f"  进度更新：{r.task_title} 推进至 {r.progress}%{hours}{note}（{r.created_at.date().isoformat()}）"
            )
    return [
        {
            "role": "system",
            "content": (
                "你是研究生的科研助理。请根据下面的本周科研活动数据，写一份简洁、"
                "有条理的中文科研周报，内容包括：本周工作概述、主要进展（按项目）、"
                "投入时间统计、下周建议。语气客观、积极，篇幅 300~500 字。"
                "直接输出周报正文，不要输出与周报无关的解释。"
            ),
        },
        {"role": "user", "content": "\n".join(lines)},
    ]


def build_demo_report(weekly: WeeklyReportOut) -> str:
    """无 Key 时的模板周报（纯本地拼接）。"""
    stats = weekly.stats
    lines = [
        f"# 科研周报（{weekly.week_start.isoformat()} ~ {weekly.week_end.isoformat()}）",
        "",
        "## 本周工作概述",
        f"本周共完成 {stats.tasks_completed} 个任务，进行了 {stats.progress_updates} 次进度更新，"
        f"累计投入 {stats.hours_spent} 小时。",
    ]
    if weekly.projects:
        lines.append("")
        lines.append("## 主要进展")
        for p in weekly.projects:
            lines.append(f"### {p.project_name}")
            for t in p.completed_tasks:
                lines.append(f"- 完成「{t.title}」")
            for r in p.progress_records:
                note = f"：{r.note}" if r.note else ""
                lines.append(f"- 「{r.task_title}」推进至 {r.progress}%{note}")
    lines.append("")
    lines.append("## 下周建议")
    if weekly.projects:
        lines.append("保持当前节奏，优先推进进行中的任务，确保按计划完成各阶段目标。")
    else:
        lines.append("本周暂无科研记录，建议先制定计划并开始执行第一项任务。")
    return "\n".join(lines)


def generate_weekly_report(db: Session, today: date | None = None) -> tuple[str, str]:
    """返回 (source, content)。source: deepseek / demo。AI 失败抛 DeepSeekError。"""
    weekly = get_weekly_report(db, today)
    if not DEEPSEEK_API_KEY:
        return "demo", build_demo_report(weekly)
    client = DeepSeekClient()
    messages = build_report_messages(weekly)
    content = client.chat(messages)
    return "deepseek", content.strip()
