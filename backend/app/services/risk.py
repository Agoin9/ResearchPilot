"""风险识别引擎（PRD §9）：纯本地规则计算，不调 AI、不落库。

- 高风险：任务未完成且计划截止日期已过（逾期）
- 中风险：计划时间已过 >30%，且实际进度落后应达进度超过 20 个百分点
- 项目级：任一任务高风险 → 高风险；≥3 个任务中风险或整体进度落后 20% → 中风险
"""
from datetime import date

from app.config import (
    BEHIND_PROGRESS_THRESHOLD,
    ELAPSED_RATIO_THRESHOLD,
    MEDIUM_TASK_COUNT_THRESHOLD,
    PROJECT_BEHIND_THRESHOLD,
)
from app.models import Project, Task

RISK_NONE = "none"
RISK_MEDIUM = "medium"
RISK_HIGH = "high"


def compute_task_risk(task: Task, today: date) -> tuple[str, str]:
    """计算单个任务的风险等级与原因。已完成任务无风险。"""
    if task.status == "done":
        return RISK_NONE, ""

    # 规则 1：逾期
    if task.planned_end_date and task.planned_end_date < today:
        days = (today - task.planned_end_date).days
        return RISK_HIGH, f"已逾期 {days} 天，进度仅 {task.progress}%"

    # 规则 2：进度落后（需要完整的计划起止日期）
    if (
        task.planned_start_date
        and task.planned_end_date
        and task.planned_end_date > task.planned_start_date
    ):
        total_days = (task.planned_end_date - task.planned_start_date).days + 1
        elapsed = max((today - task.planned_start_date).days + 1, 0)
        elapsed = min(elapsed, total_days)
        elapsed_ratio = elapsed / total_days
        if elapsed_ratio > ELAPSED_RATIO_THRESHOLD:
            expected = round(elapsed_ratio * 100)
            if expected - task.progress > BEHIND_PROGRESS_THRESHOLD:
                return (
                    RISK_MEDIUM,
                    f"进度落后计划 {expected - task.progress}%，当前进度 {task.progress}%",
                )

    return RISK_NONE, ""


def compute_project_risk(
    project: Project, tasks: list[Task], today: date
) -> tuple[str, str]:
    """计算项目级风险等级（取风险最高的原因）。"""
    # 项目已过截止日期且未完成 → 直接高风险
    if project.status == "active" and project.deadline < today:
        days = (today - project.deadline).days
        return RISK_HIGH, f"项目已逾期 {days} 天"

    task_risks = [compute_task_risk(t, today) for t in tasks]
    high_count = sum(1 for level, _ in task_risks if level == RISK_HIGH)
    if high_count > 0:
        return RISK_HIGH, f"{high_count} 个任务已逾期"
    medium_count = sum(1 for level, _ in task_risks if level == RISK_MEDIUM)
    if medium_count >= MEDIUM_TASK_COUNT_THRESHOLD:
        return RISK_MEDIUM, f"{medium_count} 个任务进度落后"

    # 项目整体进度落后判断
    created_date = project.created_at.date() if project.created_at else today
    total_days = (project.deadline - created_date).days + 1
    if total_days > 0 and tasks:
        elapsed = max((today - created_date).days + 1, 0)
        elapsed = min(elapsed, total_days)
        elapsed_ratio = elapsed / total_days
        if elapsed_ratio > ELAPSED_RATIO_THRESHOLD:
            expected = round(elapsed_ratio * 100)
            actual = round(sum(t.progress for t in tasks) / len(tasks))
            if expected - actual > PROJECT_BEHIND_THRESHOLD:
                return RISK_MEDIUM, f"项目整体进度落后计划 {expected - actual}%"

    return RISK_NONE, ""
