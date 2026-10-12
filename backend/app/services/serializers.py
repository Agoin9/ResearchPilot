"""ORM 对象 → 响应模型 的序列化助手（附带实时计算的进度 / 风险字段）。"""
from datetime import date

from app.models import Project, Task
from app.schemas import ProjectSummary, TaskOut
from app.services.risk import compute_project_risk, compute_task_risk


def build_task_out(task: Task, today: date | None = None) -> TaskOut:
    today = today or date.today()
    risk, risk_reason = compute_task_risk(task, today)
    return TaskOut(
        id=task.id,
        project_id=task.project_id,
        parent_id=task.parent_id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        planned_start_date=task.planned_start_date,
        planned_end_date=task.planned_end_date,
        estimated_hours=task.estimated_hours,
        progress=task.progress,
        is_milestone=bool(task.is_milestone),
        sort_order=task.sort_order,
        created_at=task.created_at,
        updated_at=task.updated_at,
        risk=risk,
        risk_reason=risk_reason,
    )


def build_project_summary(
    project: Project, tasks: list[Task], today: date | None = None
) -> ProjectSummary:
    today = today or date.today()
    total = len(tasks)
    done = sum(1 for t in tasks if t.status == "done")
    progress = round(sum(t.progress for t in tasks) / total) if total else 0
    risk, _ = compute_project_risk(project, tasks, today)
    return ProjectSummary(
        id=project.id,
        name=project.name,
        goal=project.goal,
        deadline=project.deadline,
        weekly_hours=project.weekly_hours,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
        progress=progress,
        tasks_total=total,
        tasks_done=done,
        risk=risk,
        days_left=(project.deadline - today).days,
    )
