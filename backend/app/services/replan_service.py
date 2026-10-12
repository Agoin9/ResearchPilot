"""重规划编排（核心创新功能）：

1. 风险在本地规则引擎计算（不依赖大模型），输出可解释原因；
2. 把全部任务状态 + 剩余时间 + 每周可用工时打包成 JSON 上下文发给 DeepSeek；
3. DeepSeek 只负责给出调整建议（JSON：plan_content / impact_summary / changes）；
4. 无 Key 时用本地规则模拟调整（演示模式）。
"""
import json
import re
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai_client import DeepSeekClient, DeepSeekError
from app.config import AI_FORMAT_RETRY_TIMES, DEEPSEEK_API_KEY
from app.models import Project, Task
from app.schemas import ReplanChange, ReplanTaskSnapshot
from app.services.risk import RISK_HIGH, RISK_MEDIUM, RISK_NONE, compute_task_risks, worst_risk_level

VALID_ACTIONS = ("reschedule", "reprioritize")
PRIORITIES = ("high", "medium", "low")


class PlanFormatError(Exception):
    """DeepSeek 输出格式错误（触发重试）。"""


# ═══════════════════════ 快照组装（上下文数据） ═══════════════════════

def build_snapshot(db: Session, project: Project, today: date) -> list[ReplanTaskSnapshot]:
    """打包全部任务状态 + 风险（本地计算），作为发给 DeepSeek 的上下文。"""
    tasks = db.scalars(
        select(Task)
        .where(Task.project_id == project.id)
        .order_by(Task.sort_order, Task.id)
    ).all()
    snapshots: list[ReplanTaskSnapshot] = []
    for task in tasks:
        risks = compute_task_risks(task, today, project.weekly_hours)
        snapshots.append(
            ReplanTaskSnapshot(
                task_id=task.id,
                title=task.title,
                status=task.status,
                progress=task.progress,
                priority=task.priority,
                planned_start_date=task.planned_start_date,
                planned_end_date=task.planned_end_date,
                estimated_hours=task.estimated_hours,
                risk_level=worst_risk_level(risks),
                risk_reasons=[r["reason"] for r in risks],
            )
        )
    return snapshots


def build_messages(project: Project, snapshots: list[ReplanTaskSnapshot], today: date) -> list[dict]:
    days_left = max((project.deadline - today).days, 0)
    system = (
        "你是科研项目管理专家，负责对延期的科研任务计划做重规划。\n"
        "用户会提供项目信息与全部任务的当前状态（含本地规则引擎计算出的风险与原因）。\n"
        "你的任务：只对需要调整的任务给出调整建议，输出严格 JSON（不要任何解释文字）：\n"
        '{"plan_content": "给用户看的整体调整说明", '
        '"impact_summary": "对项目整体进度的影响评估", '
        '"changes": [{"task_id": 数字, "action": "reschedule 或 reprioritize", '
        '"title": "任务标题", "planned_start_date": "YYYY-MM-DD", '
        '"planned_end_date": "YYYY-MM-DD", "priority": "high/medium/low", '
        '"estimated_hours": 数字, "reason": "这条调整的理由"}]}\n'
        "约束：\n"
        "1. task_id 必须是输入数据中已有的任务 id，不要编造新任务；\n"
        "2. action 只能是 reschedule（改起止日期/工时）或 reprioritize（改优先级），"
        "可同时给出两个 action 对应不同任务；\n"
        "3. 所有日期必须在今天到项目截止日期之间，planned_end_date 不得早于 planned_start_date；\n"
        "4. 优先调整有风险的任务（逾期/阻塞/进度落后/工时不足），正常任务尽量不改；\n"
        "5. 阻塞类任务优先建议先解决前置任务，必要时顺延后续任务日期；\n"
        "6. reason 用中文写清楚为什么这样调；\n"
        "7. 如果没有任务需要调整，changes 为空数组，plan_content 说明当前计划健康。"
    )
    user_lines = [
        f"项目：{project.name}",
        f"项目截止日期：{project.deadline.isoformat()}（还剩 {days_left} 天）",
        f"每周可用工时：{project.weekly_hours:g} 小时",
        f"今天：{today.isoformat()}",
        "全部任务：",
        json.dumps([s.model_dump(mode="json") for s in snapshots], ensure_ascii=False, indent=2),
    ]
    return [{"role": "system", "content": system}, {"role": "user", "content": "\n".join(user_lines)}]


# ═══════════════════════ 解析与校验 ═══════════════════════

def _extract_json(text: str) -> dict:
    raw = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL)
    if fence:
        raw = fence.group(1).strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}")
        if start == -1 or end <= start:
            raise PlanFormatError("输出中找不到 JSON 对象")
        try:
            data = json.loads(raw[start : end + 1])
        except json.JSONDecodeError as e:
            raise PlanFormatError(f"JSON 解析失败：{e.msg}")
    if not isinstance(data, dict):
        raise PlanFormatError("顶层结构不是 JSON 对象")
    return data


def validate_changes(
    data: dict, snapshots: list[ReplanTaskSnapshot], deadline: date, today: date
) -> tuple[str, str, list[ReplanChange]]:
    """校验 DeepSeek 输出：返回 (plan_content, impact_summary, changes)。"""
    plan_content = str(data.get("plan_content") or "").strip()
    if not plan_content:
        raise PlanFormatError("缺少 plan_content 字段")
    impact_summary = str(data.get("impact_summary") or "").strip()

    raw_changes = data.get("changes")
    if not isinstance(raw_changes, list):
        raise PlanFormatError("changes 必须是数组")

    snapshot_by_id = {s.task_id: s for s in snapshots}
    changes: list[ReplanChange] = []
    for item in raw_changes:
        if not isinstance(item, dict):
            continue
        try:
            task_id = int(item.get("task_id"))
        except (TypeError, ValueError):
            continue
        snapshot = snapshot_by_id.get(task_id)
        if snapshot is None:
            continue  # 引用不存在的任务 → 丢弃
        action = str(item.get("action") or "")
        if action not in VALID_ACTIONS:
            continue

        def parse_date(value, field):
            if value in (None, ""):
                return None
            try:
                return date.fromisoformat(str(value))
            except ValueError:
                raise PlanFormatError(f"任务 {task_id} 的 {field} 不是合法日期")

        start = parse_date(item.get("planned_start_date"), "planned_start_date")
        end = parse_date(item.get("planned_end_date"), "planned_end_date")
        if end is not None and start is not None and end < start:
            continue  # 日期倒挂的调整丢弃
        if end is not None and end > deadline:
            end = deadline  # 收敛到项目截止日期内

        priority = str(item.get("priority") or "")
        if priority not in PRIORITIES:
            priority = None
        try:
            hours = float(item.get("estimated_hours")) if item.get("estimated_hours") not in (None, "") else None
        except (TypeError, ValueError):
            hours = None
        if hours is not None and hours <= 0:
            hours = None

        changes.append(
            ReplanChange(
                task_id=task_id,
                action=action,
                title=str(item.get("title") or snapshot.title),
                planned_start_date=start,
                planned_end_date=end,
                priority=priority,
                estimated_hours=hours,
                reason=str(item.get("reason") or "").strip(),
            )
        )

    if not changes and any(s.risk_level != RISK_NONE for s in snapshots):
        # 有风险任务却没有任何可应用的调整 → 视为格式问题重试
        raise PlanFormatError("存在风险任务但 changes 中没有可应用的调整")
    return plan_content, impact_summary, changes


# ═══════════════════════ 演示模式：本地规则模拟调整 ═══════════════════════

def build_demo_replan(
    project: Project, snapshots: list[ReplanTaskSnapshot], today: date
) -> tuple[str, str, list[ReplanChange]]:
    """无 Key 时用本地规则生成调整建议：逾期/工时不足 → 顺延；逾期 → 提高优先级。"""
    changes: list[ReplanChange] = []
    for s in snapshots:
        if s.status == "done":
            continue
        # 只调整高风险任务，或原因中提到剩余工时不足的任务（中风险）
        has_hours_issue = any("小时工作量" in r for r in s.risk_reasons)
        if s.risk_level != RISK_HIGH and not has_hours_issue:
            continue
        remaining_hours = (s.estimated_hours or 8) * (1 - s.progress / 100)
        extend_days = max(int(remaining_hours / max(project.weekly_hours, 1) * 7) + 1, 3)
        new_end = min(today + timedelta(days=extend_days), project.deadline)
        new_start = today
        reason = (
            f"演示模式规则：该任务存在风险（{'；'.join(s.risk_reasons)}），"
            f"将计划截止顺延至 {new_end.isoformat()}，优先级提高为 high"
        )
        changes.append(
            ReplanChange(
                task_id=s.task_id,
                action="reschedule",
                title=s.title,
                planned_start_date=new_start,
                planned_end_date=new_end,
                priority="high" if s.risk_level == RISK_HIGH else None,
                reason=reason,
            )
        )
    plan_content = (
        "（演示模式）基于本地风险规则生成调整建议：对存在风险的任务顺延计划截止日期"
        f"（不超过项目截止日期 {project.deadline.isoformat()}），逾期任务优先级提高。"
        "配置 DeepSeek API Key 后可获得更智能的调整方案。"
    )
    impact_summary = (
        f"共调整 {len(changes)} 个任务。顺延后各任务仍落在项目截止日期内，"
        "但缓冲时间减少，建议优先推进高风险任务。"
    )
    return plan_content, impact_summary, changes


# ═══════════════════════ 生成重规划方案 ═══════════════════════

def generate_replan(
    db: Session, project: Project, today: date
) -> tuple[str, str, list[ReplanChange], str, list[ReplanTaskSnapshot]]:
    """返回 (plan_content, impact_summary, changes, source, snapshots)。

    AI 失败抛 DeepSeekError；格式错误自动重试 AI_FORMAT_RETRY_TIMES 次。
    """
    snapshots = build_snapshot(db, project, today)

    if not DEEPSEEK_API_KEY:
        plan_content, impact_summary, changes = build_demo_replan(project, snapshots, today)
        return plan_content, impact_summary, changes, "demo", snapshots

    client = DeepSeekClient()
    messages = build_messages(project, snapshots, today)
    for attempt in range(1 + AI_FORMAT_RETRY_TIMES):
        content = client.chat(messages)
        try:
            data = _extract_json(content)
            plan_content, impact_summary, changes = validate_changes(
                data, snapshots, project.deadline, today
            )
            return plan_content, impact_summary, changes, "deepseek", snapshots
        except PlanFormatError as e:
            if attempt >= AI_FORMAT_RETRY_TIMES:
                raise DeepSeekError(
                    "AI 返回的重规划方案格式多次校验失败，请稍后重试；"
                    "也可以删除 .env 中的密钥使用演示模式"
                ) from e
            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"上一次输出格式不正确（{e}）。请严格只输出 JSON 对象，"
                        "task_id 必须是输入数据中的任务 id，日期在合理范围内，"
                        "不要输出任何解释文字。"
                    ),
                }
            )
    raise DeepSeekError("重规划失败，请稍后重试")  # 理论不可达
