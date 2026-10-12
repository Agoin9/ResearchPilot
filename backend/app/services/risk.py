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

# 风险等级排序（用于取最严重的一条）
_RISK_RANK = {RISK_NONE: 0, RISK_MEDIUM: 1, RISK_HIGH: 2}


def compute_task_risks(
    task: Task, today: date, weekly_hours: float | None = None
) -> list[dict]:
    """计算单个任务的全部风险（本地规则，可解释），每条含 type/level/reason。

    规则（PRD §9 + 增强）：
    1. 逾期：未完成且计划截止日期已过 → 高风险；
    2. 前置阻塞：父任务（前置）未完成 → 中风险；
    3. 进度落后：计划时间已过 >30% 且实际进度落后应达进度 >20 个百分点 → 中风险；
    4. 剩余工时不足：剩余工作量按每周可用小时折算，超出剩余天数容量 → 中风险。
    已完成任务无风险。
    """
    if task.status == "done":
        return []

    risks: list[dict] = []

    # 规则 1：逾期
    if task.planned_end_date and task.planned_end_date < today:
        days = (today - task.planned_end_date).days
        risks.append(
            {
                "type": "overdue",
                "level": RISK_HIGH,
                "reason": f"已逾期 {days} 天，进度仅 {task.progress}%",
            }
        )

    # 规则 2：前置任务阻塞（task 自关联 parent 表示前置）
    parent = task.parent
    if parent is not None and parent.status != "done":
        risks.append(
            {
                "type": "blocked",
                "level": RISK_MEDIUM,
                "reason": f"前置任务「{parent.title}」尚未完成，当前任务被阻塞",
            }
        )

    # 规则 3：进度落后（需要完整的计划起止日期）
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
                risks.append(
                    {
                        "type": "behind",
                        "level": RISK_MEDIUM,
                        "reason": (
                            f"进度落后计划 {expected - task.progress}%，"
                            f"当前进度 {task.progress}%"
                        ),
                    }
                )

    # 规则 4：剩余工时不足（需要项目每周可用小时与任务预计耗时）
    if (
        weekly_hours
        and task.estimated_hours
        and task.planned_end_date
        and task.planned_end_date >= today
    ):
        remaining_hours = task.estimated_hours * (1 - task.progress / 100)
        remaining_days = (task.planned_end_date - today).days
        available_hours = remaining_days / 7 * weekly_hours
        if remaining_hours > available_hours + 1e-6:
            risks.append(
                {
                    "type": "hours_insufficient",
                    "level": RISK_MEDIUM,
                    "reason": (
                        f"剩余约 {remaining_hours:.0f} 小时工作量，"
                        f"距计划截止还有 {remaining_days} 天"
                        f"（按每周 {weekly_hours:g} 小时约可用 {available_hours:.0f} 小时），可能不足"
                    ),
                }
            )

    return risks


def worst_risk_level(risks: list[dict]) -> str:
    """从风险列表中取最严重的等级（high > medium > none）。"""
    if not risks:
        return RISK_NONE
    return max(risks, key=lambda r: _RISK_RANK.get(r["level"], 0))["level"]


def compute_task_risk(
    task: Task, today: date, weekly_hours: float | None = None
) -> tuple[str, str]:
    """计算单个任务的风险等级与原因（取最严重的一条）。

    weekly_hours 为 None 时跳过"剩余工时不足"规则（兼容旧调用）。
    """
    risks = compute_task_risks(task, today, weekly_hours)
    if not risks:
        return RISK_NONE, ""
    worst = max(risks, key=lambda r: _RISK_RANK.get(r["level"], 0))
    return worst["level"], worst["reason"]


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
