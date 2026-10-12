"""组会周报与导师汇报生成（PRD §14 提前实现）：

1. 按时间范围聚合项目数据：任务完成情况、未完成及原因、进度记录、风险、重规划历史；
2. 组装成 JSON 放进 Prompt，调用 DeepSeek 生成 Markdown（固定五章节）；
3. 无 Key 时用同一份数据拼模板（演示模式）。
"""
import json
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai_client import DeepSeekClient, DeepSeekError
from app.config import DEEPSEEK_API_KEY
from app.models import ProgressRecord, Project, ReplanHistory, Task
from app.services.risk import (
    RISK_HIGH,
    RISK_MEDIUM,
    RISK_NONE,
    compute_project_risk,
    compute_task_risk,
)

REPORT_TYPES = ("meeting", "supervisor")
TYPE_LABELS = {"meeting": "组会周报", "supervisor": "导师汇报"}
DEFAULT_RANGE_DAYS = 7


def collect_project_data(
    db: Session,
    project: Project,
    week_start: date,
    week_end: date,
    today: date,
) -> dict:
    """聚合项目在时间窗口内的结构化数据（给 Prompt 用）。"""
    tasks = list(
        db.scalars(
            select(Task)
            .where(Task.project_id == project.id)
            .order_by(Task.sort_order, Task.id)
        )
    )
    records = db.scalars(
        select(ProgressRecord)
        .where(ProgressRecord.task_id.in_([t.id for t in tasks] or [0]))
        .order_by(ProgressRecord.created_at)
    ).all()
    replans = db.scalars(
        select(ReplanHistory)
        .where(ReplanHistory.project_id == project.id)
        .order_by(ReplanHistory.created_at.desc())
    ).all()

    done_in_range = [
        t
        for t in tasks
        if t.status == "done" and t.updated_at and week_start <= t.updated_at.date() <= week_end
    ]
    incomplete_in_range = [
        t
        for t in tasks
        if t.status != "done"
        and t.planned_end_date
        and t.planned_end_date <= week_end
        and (t.planned_start_date is None or t.planned_start_date <= week_end)
    ]
    next_end = week_end + timedelta(days=7)
    upcoming = [
        t
        for t in tasks
        if t.status != "done"
        and t.planned_start_date
        and week_end < t.planned_start_date <= next_end
    ]
    records_in_range = [
        r for r in records if week_start <= r.created_at.date() <= week_end
    ]

    def task_brief(t: Task) -> dict:
        risk, risk_reason = compute_task_risk(t, today)
        return {
            "title": t.title,
            "status": t.status,
            "priority": t.priority,
            "progress": t.progress,
            "planned_start": t.planned_start_date.isoformat() if t.planned_start_date else None,
            "planned_end": t.planned_end_date.isoformat() if t.planned_end_date else None,
            "risk": risk,
            "risk_reason": risk_reason if risk != RISK_NONE else "",
        }

    project_risk, _ = compute_project_risk(project, tasks, today)
    return {
        "project": {
            "name": project.name,
            "goal": project.goal,
            "deadline": project.deadline.isoformat(),
            "status": project.status,
            "weekly_hours": project.weekly_hours,
            "progress": round(sum(t.progress for t in tasks) / len(tasks)) if tasks else 0,
            "risk": project_risk,
        },
        "week_range": {"start": week_start.isoformat(), "end": week_end.isoformat()},
        "completed_tasks": [
            {
                "title": t.title,
                "completed_at": t.updated_at.date().isoformat() if t.updated_at else None,
                "priority": t.priority,
            }
            for t in done_in_range
        ],
        "incomplete_tasks": [task_brief(t) for t in incomplete_in_range],
        "upcoming_tasks": [
            {
                "title": t.title,
                "priority": t.priority,
                "planned_start": t.planned_start_date.isoformat(),
                "planned_end": t.planned_end_date.isoformat() if t.planned_end_date else None,
                "estimated_hours": t.estimated_hours,
            }
            for t in upcoming
        ],
        "progress_records": [
            {
                "task_title": next((t.title for t in tasks if t.id == r.task_id), f"任务#{r.task_id}"),
                "progress": r.progress,
                "hours_spent": r.hours_spent,
                "note": r.note,
                "created_at": r.created_at.date().isoformat(),
            }
            for r in records_in_range
        ],
        "replan_history": [
            {
                "trigger_type": r.trigger_type,
                "status": r.status,
                "summary": (r.plan_content or "")[:200],
                "created_at": r.created_at.date().isoformat(),
            }
            for r in replans
        ],
    }


def build_messages(data: dict, report_type: str) -> list[dict]:
    style = (
        "简洁要点式，适合组会上快速口头汇报，每条一到两句话"
        if report_type == "meeting"
        else "正式书面语，结构完整、分析详细，适合直接发给导师阅读"
    )
    system = (
        "你是研究生的科研助理，负责撰写科研汇报。请根据用户提供的结构化项目数据，"
        "撰写一份 Markdown 格式的汇报。\n"
        "输出要求（必须严格遵守）：\n"
        "1. 必须包含以下五个章节，使用二级标题（## ）：\n"
        "   ## 本周完成、## 未完成及原因、## 当前风险、## 下周计划、## 需要导师支持\n"
        "2. 严格依据给定数据撰写，不得编造数据中没有的内容；数据不足的章节写「无」；\n"
        "3. 未完成及原因要结合任务的 risk_reason 和进度记录的 note 分析；\n"
        "4. 需要导师支持一节根据当前风险与未完成任务推断（如：需导师帮忙协调资源、"
        "审阅方案、提供数据等），没有需要就写「无」；\n"
        f"5. 风格：{style}；\n"
        "6. 只输出 Markdown 正文，不要输出任何解释性文字。"
    )
    user = f"项目数据（JSON）：\n{json.dumps(data, ensure_ascii=False, indent=2)}"
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def build_demo_report(data: dict, report_type: str) -> str:
    """无 Key 时的模板汇报：用真实聚合数据拼接（演示模式）。"""
    project = data["project"]
    week = data["week_range"]
    label = TYPE_LABELS.get(report_type, "汇报")
    lines = [f"# {label}（{week['start']} ~ {week['end']}）", "", f"项目：{project['name']}", ""]

    lines.append("## 本周完成")
    if data["completed_tasks"]:
        for t in data["completed_tasks"]:
            lines.append(f"- {t['title']}")
    else:
        lines.append("无")
    lines.append("")

    lines.append("## 未完成及原因")
    if data["incomplete_tasks"]:
        for t in data["incomplete_tasks"]:
            reason = f"：{t['risk_reason']}" if t["risk_reason"] else ""
            lines.append(f"- {t['title']}（进度 {t['progress']}%）{reason}")
    else:
        lines.append("无")
    lines.append("")

    lines.append("## 当前风险")
    if data["project"]["risk"] != RISK_NONE:
        for t in data["incomplete_tasks"]:
            if t["risk"] != RISK_NONE:
                lines.append(f"- {t['title']}：{t['risk_reason']}")
        if data["project"]["risk"] == RISK_HIGH and not data["incomplete_tasks"]:
            lines.append("- 项目存在延期风险（见任务风险详情）")
    else:
        lines.append("无")
    lines.append("")

    lines.append("## 下周计划")
    if data["upcoming_tasks"]:
        for t in data["upcoming_tasks"]:
            lines.append(f"- {t['title']}（{t['planned_start']} ~ {t['planned_end'] or '—'}）")
    else:
        lines.append("无")
    lines.append("")

    lines.append("## 需要导师支持")
    if data["incomplete_tasks"]:
        lines.append("- 请导师协助梳理未完成任务的推进方案（结合上述风险）")
    else:
        lines.append("无")
    lines.append("")
    lines.append("> （演示模式）未配置 DeepSeek API Key，本汇报由模板自动生成。")
    return "\n".join(lines)


def generate_report(
    db: Session,
    project: Project,
    report_type: str,
    week_start: date,
    week_end: date,
    today: date,
) -> tuple[str, str, str]:
    """返回 (title, content, source)。AI 失败抛 DeepSeekError（路由转 502）。"""
    label = TYPE_LABELS.get(report_type, "汇报")
    title = f"{label}（{week_start.isoformat()} ~ {week_end.isoformat()}）"
    data = collect_project_data(db, project, week_start, week_end, today)

    if not DEEPSEEK_API_KEY:
        return title, build_demo_report(data, report_type), "demo"

    client = DeepSeekClient()
    messages = build_messages(data, report_type)
    content = client.chat(messages)
    return title, content.strip(), "deepseek"
