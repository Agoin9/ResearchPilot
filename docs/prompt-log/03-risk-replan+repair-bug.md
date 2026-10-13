我的开发核心创新功能：科研进度风险预警 + DeepSeek动态重规划，后端./backend。
流程：
1. 后端本地计算风险（不依赖大模型）：判断任务是否逾期、剩余工时是否不足、前置任务未完成阻塞后续任务。输出风险原因，可解释。
2. 用户点击【重新规划】，后端把当前项目全部任务状态、剩余时间、每周可用工时打包，作为上下文发给DeepSeek API。
3. DeepSeek输出新的任务计划JSON，附带调整理由、对项目整体进度的影响。
4. 前端展示：原计划 vs 新计划对比表格，高亮改动内容。
5. 用户点击【接受调整】，数据库更新任务，同时保存本次重规划记录（原计划、新计划、时间、理由），支持查看历史重规划记录。
6. 同样支持演示模式，无DeepSeek密钥时使用模拟重规划结果。
7. 风险判断逻辑写在后端代码，不要交给大模型做基础计算；大模型只负责给出调整建议。
8. 不改动已有任务生成和CRUD代码。

完成后给我测试流程：创建项目，标记部分任务延期，触发风险预警，执行重规划，查看新旧对比和历史记录。
Show more
6:21 PM
我先看一眼你打开的 prompt-log（了解你期望的 Prompt 形态），然后实现核心功能：



Read E:\ResearchPilot\docs\prompt-log\02-deepseek-task-generate.md
6:22 PM
prompt-log 只是我们之前会话的记录，无需继续读。当前任务明确：风险预警 + 动态重规划，直接实现。先扩展风险引擎（新增"前置阻塞"和"剩余工时不足"两条规则，纯本地计算）：



Edit E:\ResearchPilot\backend\app\services\risk.py
Added 75 lines
Edit E:\ResearchPilot\backend\app\services\serializers.py
Added 2 lines
Edit E:\ResearchPilot\backend\app\schemas.py
Added 49 lines
Write E:\ResearchPilot\backend\app\services\replan_service.py
273 lines
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
from app.services.risk import RISK_HIGH, RISK_MEDIUM, RISK_NONE, compute_task_risks

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
                risk_level=max((r["level"] for r in risks), default=RISK_NONE),
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
        if s.risk_level != RISK_HIGH and "hours_insufficient" not in s.risk_reasons and not any(
            "工时" in r for r in s.risk_reasons
        ):
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
Write E:\ResearchPilot\backend\app\routers\replans.py
167 lines
"""重规划接口（核心创新功能）：

POST /api/projects/{id}/replan    生成重规划方案（风险本地计算 + DeepSeek 建议，不写任务表）
POST /api/replans/{id}/adopt      用户接受 → 应用调整到任务表 + 记录状态 adopted
POST /api/replans/{id}/reject     用户放弃 → 状态 rejected
GET  /api/projects/{id}/replans   历史记录列表（含原计划/新计划/时间/理由）
"""
import json
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai_client import DeepSeekError
from app.database import get_db
from app.models import Project, ReplanHistory, Task
from app.schemas import ReplanAdoptOut, ReplanChange, ReplanOut, ReplanTaskSnapshot
from app.services.replan_service import generate_replan

router = APIRouter(tags=["重规划"])


def _get_project_or_404(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


def _get_replan_or_404(db: Session, replan_id: int) -> ReplanHistory:
    replan = db.get(ReplanHistory, replan_id)
    if replan is None:
        raise HTTPException(status_code=404, detail="重规划记录不存在")
    return replan


def _replan_out(row: ReplanHistory) -> ReplanOut:
    payload = json.loads(row.changes_json or "{}")
    changes = [ReplanChange(**c) for c in payload.get("changes") or []]
    original = [ReplanTaskSnapshot(**t) for t in payload.get("original_tasks") or []]
    return ReplanOut(
        id=row.id,
        project_id=row.project_id,
        trigger_type=row.trigger_type,
        plan_content=row.plan_content,
        impact_summary=payload.get("impact_summary") or "",
        changes=changes,
        original_tasks=original,
        source=payload.get("source") or "demo",
        status=row.status,
        created_at=row.created_at,
        decided_at=row.decided_at,
    )


@router.post("/projects/{project_id}/replan", response_model=ReplanOut)
def create_replan(project_id: int, db: Session = Depends(get_db)):
    """生成重规划方案（状态 pending，不修改任务表）。

    风险由本地规则引擎计算；DeepSeek 只负责给出调整建议。
    """
    project = _get_project_or_404(db, project_id)
    today = date.today()
    try:
        plan_content, impact_summary, changes, source, snapshots = generate_replan(
            db, project, today
        )
    except DeepSeekError as e:
        raise HTTPException(status_code=502, detail=str(e))

    risky = [s for s in snapshots if s.risk_level != "none"]
    row = ReplanHistory(
        project_id=project_id,
        trigger_type="manual",
        risk_tasks_json=json.dumps(
            [
                {"task_id": s.task_id, "title": s.title, "risk_reasons": s.risk_reasons}
                for s in risky
            ],
            ensure_ascii=False,
        ),
        plan_content=plan_content,
        changes_json=json.dumps(
            {
                "changes": [c.model_dump(mode="json") for c in changes],
                "original_tasks": [s.model_dump(mode="json") for s in snapshots],
                "impact_summary": impact_summary,
                "source": source,
            },
            ensure_ascii=False,
        ),
        status="pending",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _replan_out(row)


@router.post("/replans/{replan_id}/adopt", response_model=ReplanAdoptOut)
def adopt_replan(replan_id: int, db: Session = Depends(get_db)):
    """接受调整：把 changes 应用到任务表（改起止日期/优先级/预计工时），状态置 adopted。"""
    replan = _get_replan_or_404(db, replan_id)
    if replan.status != "pending":
        raise HTTPException(status_code=400, detail="该方案已处理过，不能重复采纳")
    project = _get_project_or_404(db, replan.project_id)
    payload = json.loads(replan.changes_json or "{}")
    applied = 0

    for item in payload.get("changes") or []:
        task = db.get(Task, item.get("task_id"))
        if task is None or task.project_id != replan.project_id:
            continue
        action = item.get("action")
        if action == "reschedule":
            if item.get("planned_start_date"):
                task.planned_start_date = date.fromisoformat(item["planned_start_date"])
            if item.get("planned_end_date"):
                task.planned_end_date = date.fromisoformat(item["planned_end_date"])
            if item.get("estimated_hours"):
                task.estimated_hours = float(item["estimated_hours"])
        if action == "reprioritize" or item.get("priority"):
            if item.get("priority") in ("high", "medium", "low"):
                task.priority = item["priority"]
        # 合并后的日期合法性：截止不早于开始、不超过项目截止日期
        if (
            task.planned_start_date
            and task.planned_end_date
            and task.planned_end_date < task.planned_start_date
        ):
            task.planned_end_date = task.planned_start_date
        if task.planned_end_date and task.planned_end_date > project.deadline:
            task.planned_end_date = project.deadline
        applied += 1

    replan.status = "adopted"
    replan.decided_at = datetime.now()
    db.commit()
    db.refresh(replan)
    return ReplanAdoptOut(replan=_replan_out(replan), applied_count=applied)


@router.post("/replans/{replan_id}/reject", response_model=ReplanOut)
def reject_replan(replan_id: int, db: Session = Depends(get_db)):
    """放弃方案：状态置 rejected，不改任务表。"""
    replan = _get_replan_or_404(db, replan_id)
    if replan.status != "pending":
        raise HTTPException(status_code=400, detail="该方案已处理过")
    replan.status = "rejected"
    replan.decided_at = datetime.now()
    db.commit()
    db.refresh(replan)
    return _replan_out(replan)


@router.get("/projects/{project_id}/replans", response_model=list[ReplanOut])
def list_replans(project_id: int, db: Session = Depends(get_db)):
    """重规划历史（最新在前），支持查看原计划、新计划、时间与理由。"""
    _get_project_or_404(db, project_id)
    rows = db.scalars(
        select(ReplanHistory)
        .where(ReplanHistory.project_id == project_id)
        .order_by(ReplanHistory.created_at.desc())
    ).all()
    return [_replan_out(r) for r in rows]
Edit E:\ResearchPilot\backend\app\main.py
Modified
Edit E:\ResearchPilot\backend\app\main.py
Added 1 line
6:24 PM
后端完成。写前端：类型、API、重规划 Tab 组件：



Edit E:\ResearchPilot\frontend\src\types\index.ts
Added 41 lines
Edit E:\ResearchPilot\frontend\src\services\api.ts
Added 1 line
Edit E:\ResearchPilot\frontend\src\services\api.ts
Added 22 lines
Write E:\ResearchPilot\frontend\src\components\replan\ReplanTab.tsx
380 lines
import {
  AlertOctagon,
  AlertTriangle,
  Check,
  History,
  Loader2,
  RefreshCw,
  X,
} from 'lucide-react'
import { useCallback, useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { toast } from '@/components/ui/toast'
import { useAsyncData } from '@/hooks/useAsyncData'
import {
  adoptReplan,
  fetchProjectDetail,
  fetchReplans,
  generateReplan,
  rejectReplan,
} from '@/services/api'
import type { ReplanInfo, ReplanTaskSnapshot, Task } from '@/types'

const STATUS_LABELS: Record<ReplanInfo['status'], string> = {
  pending: '待处理',
  adopted: '已采纳',
  rejected: '已放弃',
}

const STATUS_BADGE_CLASSES: Record<ReplanInfo['status'], string> = {
  pending: 'border-sky-300 bg-sky-50 text-sky-700 dark:border-sky-500/40 dark:bg-sky-500/10 dark:text-sky-400',
  adopted: 'border-emerald-300 bg-emerald-50 text-emerald-700 dark:border-emerald-500/40 dark:bg-emerald-500/10 dark:text-emerald-400',
  rejected: 'border-border bg-muted text-muted-foreground',
}

const PRIORITY_LABELS: Record<string, string> = { high: '高', medium: '中', low: '低' }

/** 重规划 Tab：风险预警列表 + 生成调整方案 + 原计划 vs 新计划对比 + 历史记录 */
export function ReplanTab({ projectId }: { projectId: number }) {
  const loadDetail = useCallback(() => fetchProjectDetail(projectId), [projectId])
  const { data, reload } = useAsyncData(loadDetail)
  const loadReplans = useCallback(() => fetchReplans(projectId), [projectId])
  const { data: history, reload: reloadHistory } = useAsyncData(loadReplans)
  const [generating, setGenerating] = useState(false)
  const [current, setCurrent] = useState<ReplanInfo | null>(null)
  const [processing, setProcessing] = useState(false)

  const riskyTasks = (data?.tasks ?? []).filter((task) => task.risk !== 'none')

  const handleGenerate = async () => {
    setGenerating(true)
    setCurrent(null)
    try {
      const replan = await generateReplan(projectId)
      setCurrent(replan)
      void reloadHistory()
      if (replan.source === 'demo') {
        toast.add({ title: '演示模式', description: '未配置 DeepSeek Key，使用本地规则模拟调整', type: 'info' })
      } else {
        toast.add({ title: '重规划方案已生成', description: '请对比新旧计划后决定是否采纳', type: 'success' })
      }
    } catch {
      // 错误提示已由 api 层统一 toast 展示
    } finally {
      setGenerating(false)
    }
  }

  const handleAdopt = async () => {
    if (!current) return
    setProcessing(true)
    try {
      const result = await adoptReplan(current.id)
      setCurrent(result.replan)
      toast.add({ title: '已采纳调整', description: `共调整 ${result.appliedCount} 个任务，看板已更新`, type: 'success' })
      void reload()
      void reloadHistory()
    } catch {
      // 错误提示已由 api 层统一 toast 展示
    } finally {
      setProcessing(false)
    }
  }

  const handleReject = async () => {
    if (!current) return
    setProcessing(true)
    try {
      const updated = await rejectReplan(current.id)
      setCurrent(updated)
      toast.add({ title: '已放弃该方案', description: '任务计划保持不变', type: 'info' })
      void reloadHistory()
    } catch {
      // 错误提示已由 api 层统一 toast 展示
    } finally {
      setProcessing(false)
    }
  }

  return (
    <div className="flex flex-col gap-4">
      {/* 风险预警 */}
      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <div>
            <CardTitle className="text-base">风险预警</CardTitle>
            <CardDescription>本地规则引擎实时计算：逾期 / 前置阻塞 / 进度落后 / 剩余工时不足</CardDescription>
          </div>
          <Badge variant={riskyTasks.length > 0 ? 'destructive' : 'secondary'}>
            {riskyTasks.length} 个风险任务
          </Badge>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          {riskyTasks.length === 0 ? (
            <p className="py-3 text-center text-sm text-muted-foreground">
              当前所有任务都在计划内正常推进
            </p>
          ) : (
            riskyTasks.map((task) => (
              <div
                key={task.id}
                className={`flex items-start gap-2 rounded-lg border px-3 py-2 text-sm ${
                  task.risk === 'high'
                    ? 'border-red-200 bg-red-50 text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-400'
                    : 'border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-400'
                }`}
              >
                {task.risk === 'high' ? (
                  <AlertOctagon className="mt-0.5 size-4 shrink-0" />
                ) : (
                  <AlertTriangle className="mt-0.5 size-4 shrink-0" />
                )}
                <div className="min-w-0">
                  <p className="font-medium">{task.title}</p>
                  <p className="mt-0.5 text-xs opacity-90">{task.riskReason}</p>
                </div>
              </div>
            ))
          )}
          <div className="flex justify-end pt-2">
            <Button disabled={generating} onClick={() => void handleGenerate()}>
              {generating ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  正在生成重规划方案…
                </>
              ) : (
                <>
                  <RefreshCw className="size-4" />
                  重新规划
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 当前方案：对比 + 采纳/放弃 */}
      {current && current.status === 'pending' && (
        <ReplanView
          replan={current}
          processing={processing}
          onAdopt={() => void handleAdopt()}
          onReject={() => void handleReject()}
        />
      )}

      {/* 历史记录 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <History className="size-4" />
            重规划历史
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {!history || history.length === 0 ? (
            <p className="py-3 text-center text-sm text-muted-foreground">还没有重规划记录</p>
          ) : (
            history.map((replan) => (
              <div key={replan.id} className="rounded-xl border border-border p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-medium">
                    {replan.createdAt.slice(0, 16).replace('T', ' ')} · {replan.changes.length} 条调整
                  </p>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className={STATUS_BADGE_CLASSES[replan.status]}>
                      {STATUS_LABELS[replan.status]}
                    </Badge>
                    <Badge variant={replan.source === 'demo' ? 'secondary' : 'default'}>
                      {replan.source === 'demo' ? '演示模式' : 'DeepSeek'}
                    </Badge>
                  </div>
                </div>
                <p className="mt-1.5 text-xs text-muted-foreground line-clamp-2">
                  {replan.planContent}
                </p>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  )
}

/** 单个方案视图：文字说明 + 影响评估 + 原计划 vs 新计划对比表 + 操作按钮 */
function ReplanView({
  replan,
  processing,
  onAdopt,
  onReject,
}: {
  replan: ReplanInfo
  processing: boolean
  onAdopt: () => void
  onReject: () => void
}) {
  const changeByTask = new Map(replan.changes.map((c) => [c.taskId, c]))
  const hasChanges = replan.changes.length > 0

  return (
    <Card className="border-primary/40">
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <CardTitle className="text-base">重规划方案</CardTitle>
          <Badge variant={replan.source === 'demo' ? 'secondary' : 'default'}>
            {replan.source === 'demo' ? '演示模式' : 'DeepSeek 生成'}
          </Badge>
        </div>
        <CardDescription>{replan.planContent}</CardDescription>
        {replan.impactSummary && (
          <p className="rounded-lg bg-muted px-3 py-2 text-xs text-muted-foreground">
            影响评估：{replan.impactSummary}
          </p>
        )}
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <CompareTable tasks={replan.originalTasks} changeByTask={changeByTask} />

        {replan.changes.length > 0 && (
          <div>
            <p className="mb-1.5 text-xs font-medium text-muted-foreground">调整理由</p>
            <ul className="flex flex-col gap-1.5">
              {replan.changes.map((change) => (
                <li key={change.taskId} className="text-xs text-muted-foreground">
                  <span className="font-medium text-foreground">「{change.title}」：</span>
                  {change.reason || (change.action === 'reprioritize' ? '调整优先级' : '调整计划日期')}
                </li>
              ))}
            </ul>
          </div>
        )}

        {hasChanges && (
          <div className="flex justify-end gap-2 border-t border-border pt-3">
            <Button variant="outline" disabled={processing} onClick={onReject}>
              <X className="size-4" />
              放弃
            </Button>
            <Button disabled={processing} onClick={onAdopt}>
              {processing ? <Loader2 className="size-4 animate-spin" /> : <Check className="size-4" />}
              接受调整
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

const fmtDate = (iso: string | null) => (iso ? iso.slice(5).replace('-', '-') : '—')

/** 原计划 vs 新计划对比表：高亮改动内容 */
function CompareTable({
  tasks,
  changeByTask,
}: {
  tasks: ReplanTaskSnapshot[]
  changeByTask: Map<number, ReplanInfo['changes'][number]>
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs text-muted-foreground">
            <th className="py-2 pr-3 font-medium">任务</th>
            <th className="py-2 pr-3 font-medium">计划日期</th>
            <th className="py-2 pr-3 font-medium">优先级</th>
            <th className="py-2 pr-3 font-medium">预计工时</th>
            <th className="py-2 font-medium">状态</th>
          </tr>
        </thead>
        <tbody>
          {tasks.map((task) => {
            const change = changeByTask.get(task.taskId)
            const newStart = change?.plannedStartDate ?? task.plannedStartDate
            const newEnd = change?.plannedEndDate ?? task.plannedEndDate
            const newPriority = change?.priority ?? task.priority
            const newHours = change?.estimatedHours ?? task.estimatedHours
            const dateChanged =
              newStart !== task.plannedStartDate || newEnd !== task.plannedEndDate
            const priorityChanged = newPriority !== task.priority
            const hoursChanged = newHours !== task.estimatedHours
            const isChanged = Boolean(change)

            return (
              <tr
                key={task.taskId}
                className={`border-b border-border/60 ${isChanged ? 'bg-primary/5' : ''}`}
              >
                <td className="py-2 pr-3">
                  <span className="min-w-0 break-words">
                    {task.title}
                    {isChanged && (
                      <Badge variant="outline" className="ml-1.5 border-primary/40 text-primary">
                        调整
                      </Badge>
                    )}
                  </span>
                </td>
                <td className="py-2 pr-3 tabular-nums">
                  {dateChanged ? (
                    <span>
                      <span className="text-muted-foreground line-through">
                        {fmtDate(task.plannedStartDate)}~{fmtDate(task.plannedEndDate)}
                      </span>
                      <span className="ml-1.5 font-medium text-primary">
                        → {fmtDate(newStart)}~{fmtDate(newEnd)}
                      </span>
                    </span>
                  ) : (
                    <span className="text-muted-foreground">
                      {fmtDate(task.plannedStartDate)}~{fmtDate(task.plannedEndDate)}
                    </span>
                  )}
                </td>
                <td className="py-2 pr-3">
                  {priorityChanged ? (
                    <span>
                      <span className="text-muted-foreground line-through">
                        {PRIORITY_LABELS[task.priority]}
                      </span>
                      <span className="ml-1.5 font-medium text-primary">
                        → {PRIORITY_LABELS[newPriority]}
                      </span>
                    </span>
                  ) : (
                    <span className="text-muted-foreground">{PRIORITY_LABELS[task.priority]}</span>
                  )}
                </td>
                <td className="py-2 pr-3 tabular-nums">
                  {hoursChanged ? (
                    <span>
                      <span className="text-muted-foreground line-through">
                        {task.estimatedHours ?? '—'}
                      </span>
                      <span className="ml-1.5 font-medium text-primary">→ {newHours}</span>
                    </span>
                  ) : (
                    <span className="text-muted-foreground">{task.estimatedHours ?? '—'}</span>
                  )}
                </td>
                <td className="py-2">
                  <span className="text-muted-foreground">
                    {task.status === 'done' ? '已完成' : task.status === 'doing' ? `进行中 ${task.progress}%` : '待开始'}
                  </span>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

export type { Task }
Edit E:\ResearchPilot\frontend\src\components\replan\ReplanTab.tsx
Modified
Edit E:\ResearchPilot\frontend\src\components\replan\ReplanTab.tsx
Removed 2 lines
Edit E:\ResearchPilot\frontend\src\pages\ProjectDashboardPage.tsx
Added 1 line
Edit E:\ResearchPilot\frontend\src\pages\ProjectDashboardPage.tsx
Added 4 lines
Bash Build frontend with replan feature
IN
cd E:/ResearchPilot/frontend && npm run build 2>&1 | tail -2

OUT
- Adjust chunk size limit for this warning via build.chunkSizeWarningLimit.
✓ built in 14.98s
6:26 PM
构建通过。启动测试实例，按你的验收流程完整测试：



Bash Start demo-mode backend on 8001
IN
cd E:/ResearchPilot/backend && DEEPSEEK_API_KEY= venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001

OUT
Command running in background with ID: bhksi2cce. Output is being written to: C:\Users\86198\AppData\Local\Temp\claude\e--ResearchPilot\2116447b-6bbd-4fce-8d5e-e14ee02533b8\tasks\bhksi2cce.output. You will be notified when it completes. To check interim output, use Read on that file path.
Session cwd remains E:\ResearchPilot\frontend; directory changes made by the backgrounded command do not apply to subsequent commands.
Bash Test risk engine and demo replan
IN
sleep 3 && cd E:/ResearchPilot/backend && PYTHONIOENCODING=utf-8 venv/Scripts/python -c "
import json, urllib.request
from datetime import date, timedelta

today = date.today()
def call(method, path, body=None, port=8001):
    req = urllib.request.Request(f'http://127.0.0.1:{port}/api' + path, method=method)
    req.add_header('Content-Type', 'application/json')
    data = json.dumps(body).encode('utf-8') if body is not None else None
    try:
        with urllib.request.urlopen(req, data, timeout=120) as resp:
            raw = resp.read(); return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raw = e.read(); return e.code, json.loads(raw) if raw else None

print('=== 1. 创建项目 + 延期任务（构造风险场景） ===')
code, proj = call('POST', '/projects', {'name': '【重规划测试】项目', 'goal': '验证风险预警与重规划', 'deadline': (today + timedelta(days=30)).isoformat(), 'weeklyHours': 10})
pid = proj['id']
code, t_done = call('POST', '/tasks', {'projectId': pid, 'title': '文献综述（已完成）'})
call('PUT', f\"/tasks/{t_done['id']}\", {'status': 'done'})
code, t_overdue = call('POST', '/tasks', {'projectId': pid, 'title': '核心实验（已逾期）',
    'plannedStartDate': (today - timedelta(days=14)).isoformat(), 'plannedEndDate': (today - timedelta(days=2)).isoformat(),
    'estimatedHours': 30, 'priority': 'medium'})
call('PUT', f\"/tasks/{t_overdue['id']}\", {'progress': 40})
code, t_blocked = call('POST', '/tasks', {'projectId': pid, 'title': '论文撰写（被前置阻塞）',
    'parentId': t_overdue['id'], 'plannedStartDate': (today + timedelta(days=1)).isoformat(),
    'plannedEndDate': (today + timedelta(days=10)).isoformat(), 'estimatedHours': 20})
code, t_normal = call('POST', '/tasks', {'projectId': pid, 'title': '答辩准备（正常）',
    'plannedStartDate': (today + timedelta(days=15)).isoformat(), 'plannedEndDate': (today + timedelta(days=25)).isoformat(), 'estimatedHours': 8})
print('项目 id =', pid, '| 任务 id:', t_done['id'], t_overdue['id'], t_blocked['id'], t_normal['id'])
json.dump({'pid': pid, 'ids': [t_done['id'], t_overdue['id'], t_blocked['id'], t_normal['id']]}, open('_test_replan_state.json', 'w'))

print()
print('=== 2. 风险预警：本地规则引擎输出（可解释） ===')
code, detail = call('GET', f'/projects/{pid}')
for t in detail['tasks']:
    print(f\"  任务 {t['id']}「{t['title']}」risk={t['risk']} | {t['riskReason']}\")
print('项目级风险:', detail['project']['risk'])

print()
print('=== 3. 演示模式重规划 ===')
code, replan = call('POST', f'/projects/{pid}/replan')
print('状态码:', code, '| source:', replan['source'], '| status:', replan['status'])
print('方案说明:', replan['planContent'][:150])
print('影响评估:', replan['impactSummary'][:100])
print('调整:')
for c in replan['changes']:
    print(f\"  [{c['taskId']}] {c['title']} → {c['plannedStartDate']}~{c['plannedEndDate']} 优先级={c['priority']} | {c['reason'][:50]}\")
print('原计划快照任务数:', len(replan['originalTasks']))
json.dump({'replan_id': replan['id']}, open('_test_replan_state.json', 'w', encoding='utf-8'))
"

OUT
=== 1. 创建项目 + 延期任务（构造风险场景） ===
项目 id = 5 | 任务 id: 17 18 19 20

=== 2. 风险预警：本地规则引擎输出（可解释） ===
  任务 17「文献综述（已完成）」risk=none | 
  任务 18「核心实验（已逾期）」risk=high | 已逾期 2 天，进度仅 40%
  任务 19「论文撰写（被前置阻塞）」risk=medium | 前置任务「核心实验（已逾期）」尚未完成，当前任务被阻塞
  任务 20「答辩准备（正常）」risk=none | 
项目级风险: high

=== 3. 演示模式重规划 ===
状态码: 200 | source: demo | status: pending
方案说明: （演示模式）基于本地风险规则生成调整建议：对存在风险的任务顺延计划截止日期（不超过项目截止日期 2026-11-11），逾期任务优先级提高。配置 DeepSeek API Key 后可获得更智能的调整方案。
影响评估: 共调整 0 个任务。顺延后各任务仍落在项目截止日期内，但缓冲时间减少，建议优先推进高风险任务。
调整:
原计划快照任务数: 4
6:29 PM
风险引擎全对（逾期/前置阻塞/项目级 high）。但演示模式有个 bug：我把风险类型名和中文原因列表搞混了，导致 0 条调整。修复：



Edit E:\ResearchPilot\backend\app\services\replan_service.py
Modified
TaskStop
IN
{
  "task_id": "bhksi2cce"
}
OUT
{"message":"Successfully stopped task: bhksi2cce (cd E:/ResearchPilot/backend && DEEPSEEK_API_KEY= venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001)","task_id":"bhksi2cce","task_type":"local_bash","command":"cd E:/ResearchPilot/backend && DEEPSEEK_API_KEY= venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001"}
Bash Restart demo backend on 8001 with fix
IN
cd E:/ResearchPilot/backend && DEEPSEEK_API_KEY= venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001

OUT
Command running in background with ID: bwe4xrjn4. Output is being written to: C:\Users\86198\AppData\Local\Temp\claude\e--ResearchPilot\2116447b-6bbd-4fce-8d5e-e14ee02533b8\tasks\bwe4xrjn4.output. You will be notified when it completes. To check interim output, use Read on that file path.
Session cwd remains E:\ResearchPilot\backend; directory changes made by the backgrounded command do not apply to subsequent commands.
Bash Test demo replan, adopt, reject and history
IN
sleep 3 && cd E:/ResearchPilot/backend && PYTHONIOENCODING=utf-8 venv/Scripts/python -c "
import json, urllib.request
state = json.load(open('_test_replan_state.json'))
pid = state['pid']

def call(method, path, body=None, port=8001):
    req = urllib.request.Request(f'http://127.0.0.1:{port}/api' + path, method=method)
    req.add_header('Content-Type', 'application/json')
    data = json.dumps(body).encode('utf-8') if body is not None else None
    try:
        with urllib.request.urlopen(req, data, timeout=120) as resp:
            raw = resp.read(); return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raw = e.read(); return e.code, json.loads(raw) if raw else None

print('=== 3(重试). 演示模式重规划 ===')
code, replan = call('POST', f'/projects/{pid}/replan')
print('状态码:', code, '| source:', replan['source'], '| 调整数:', len(replan['changes']))
for c in replan['changes']:
    print(f\"  [{c['taskId']}] {c['title']} → {c['plannedStartDate']}~{c['plannedEndDate']} 优先级={c['priority']}\")
    print(f\"    理由: {c['reason'][:70]}\")
replan_id = replan['id']

print()
print('=== 4. 接受调整 → 任务表更新 ===')
code, result = call('POST', f'/replans/{replan_id}/adopt')
print('状态码:', code, '| applied:', result['appliedCount'], '| status:', result['replan']['status'])
code, detail = call('GET', f'/projects/{pid}')
for t in detail['tasks']:
    if t['id'] == state['ids'][1]:
        print(f\"  逾期任务更新后: {t['plannedStartDate']}~{t['plannedEndDate']} 优先级={t['priority']}\")

print()
print('=== 5. 放弃路径 ===')
code, replan2 = call('POST', f'/projects/{pid}/replan')
code, rejected = call('POST', f\"/replans/{replan2['id']}/reject\")
print('状态码:', code, '| status:', rejected['status'], '| decidedAt:', rejected['decidedAt'][:16])

print()
print('=== 6. 历史记录 ===')
code, history = call('GET', f'/projects/{pid}/replans')
print('状态码:', code, '| 数量:', len(history))
for h in history:
    print(f\"  #{h['id']} status={h['status']} source={h['source']} changes={len(h['changes'])} created={h['createdAt'][:16]}\")
json.dump({'pid': pid, 'replan_id': replan_id}, open('_test_replan_state.json', 'w'))
"

OUT
Exit code 1
Traceback (most recent call last):
  File "<string>", line 4, in <module>
KeyError: 'pid'
6:29 PM
状态文件被上个脚本覆盖了（项目 id 其实是 5）。重写状态后继续：



Bash Test demo replan adopt reject and history
IN
cd E:/ResearchPilot/backend && PYTHONIOENCODING=utf-8 venv/Scripts/python -c "
import json
json.dump({'pid': 5, 'ids': [17, 18, 19, 20]}, open('_test_replan_state.json', 'w'))
print('状态已重建: pid=5, 任务 17/18/19/20')
" && PYTHONIOENCODING=utf-8 venv/Scripts/python -c "
import json, urllib.request
state = json.load(open('_test_replan_state.json'))
pid = state['pid']

def call(method, path, body=None, port=8001):
    req = urllib.request.Request(f'http://127.0.0.1:{port}/api' + path, method=method)
    req.add_header('Content-Type', 'application/json')
    data = json.dumps(body).encode('utf-8') if body is not None else None
    try:
        with urllib.request.urlopen(req, data, timeout=120) as resp:
            raw = resp.read(); return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raw = e.read(); return e.code, json.loads(raw) if raw else None

print('=== 3(重试). 演示模式重规划 ===')
code, replan = call('POST', f'/projects/{pid}/replan')
print('状态码:', code, '| source:', replan['source'], '| 调整数:', len(replan['changes']))
for c in replan['changes']:
    print(f\"  [{c['taskId']}] {c['title']} → {c['plannedStartDate']}~{c['plannedEndDate']} 优先级={c['priority']}\")
    print(f\"    理由: {c['reason'][:70]}\")
replan_id = replan['id']

print()
print('=== 4. 接受调整 → 任务表更新 ===')
code, result = call('POST', f'/replans/{replan_id}/adopt')
print('状态码:', code, '| applied:', result['appliedCount'], '| status:', result['replan']['status'])
code, detail = call('GET', f'/projects/{pid}')
for t in detail['tasks']:
    if t['id'] == 18:
        print(f\"  逾期任务更新后: {t['plannedStartDate']}~{t['plannedEndDate']} 优先级={t['priority']}\")

print()
print('=== 5. 放弃路径 ===')
code, replan2 = call('POST', f'/projects/{pid}/replan')
code, rejected = call('POST', f\"/replans/{replan2['id']}/reject\")
print('状态码:', code, '| status:', rejected['status'], '| decidedAt:', rejected['decidedAt'][:16])

print()
print('=== 6. 历史记录 ===')
code, history = call('GET', f'/projects/{pid}/replans')
print('状态码:', code, '| 数量:', len(history))
for h in history:
    print(f\"  #{h['id']} status={h['status']} source={h['source']} changes={len(h['changes'])} created={h['createdAt'][:16]}\")
"

OUT
状态已重建: pid=5, 任务 17/18/19/20
=== 3(重试). 演示模式重规划 ===
状态码: 200 | source: demo | 调整数: 1
  [19] 论文撰写（被前置阻塞） → 2026-10-12~2026-10-27 优先级=None
    理由: 演示模式规则：该任务存在风险（前置任务「核心实验（已逾期）」尚未完成，当前任务被阻塞；剩余约 20 小时工作量，距计划截止还有 10 天（按

=== 4. 接受调整 → 任务表更新 ===
状态码: 200 | applied: 1 | status: adopted
  逾期任务更新后: 2026-09-28~2026-10-10 优先级=medium

=== 5. 放弃路径 ===
状态码: 200 | status: rejected | decidedAt: 2026-10-12T18:30

=== 6. 历史记录 ===
状态码: 200 | 数量: 3
  #3 status=rejected source=demo changes=0 created=2026-10-12T18:30
  #2 status=adopted source=demo changes=1 created=2026-10-12T18:30
  #1 status=pending source=demo changes=0 created=2026-10-12T18:28
6:30 PM
又抓到一个 bug：max() 对字符串 "high"/"medium" 按字典序比较，"medium" > "high"，导致快照里逾期任务的风险等级被算成 medium、演示模式跳过了它。在 risk.py 加一个正确的等级比较函数：



Edit E:\ResearchPilot\backend\app\services\risk.py
Added 7 lines
Edit E:\ResearchPilot\backend\app\services\replan_service.py
Modified
Edit E:\ResearchPilot\backend\app\services\replan_service.py
Modified
TaskStop
IN
{
  "task_id": "bwe4xrjn4"
}
OUT
{"message":"Successfully stopped task: bwe4xrjn4 (cd E:/ResearchPilot/backend && DEEPSEEK_API_KEY= venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001)","task_id":"bwe4xrjn4","task_type":"local_bash","command":"cd E:/ResearchPilot/backend && DEEPSEEK_API_KEY= venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001"}
Bash Restart demo backend with level fix
IN
cd E:/ResearchPilot/backend && DEEPSEEK_API_KEY= venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001

OUT
Command running in background with ID: bmzx7kjez. Output is being written to: C:\Users\86198\AppData\Local\Temp\claude\e--ResearchPilot\2116447b-6bbd-4fce-8d5e-e14ee02533b8\tasks\bmzx7kjez.output. You will be notified when it completes. To check interim output, use Read on that file path.
Session cwd remains E:\ResearchPilot\backend; directory changes made by the backgrounded command do not apply to subsequent commands.
Bash Retest demo replan with level fix
IN
sleep 3 && cd E:/ResearchPilot/backend && PYTHONIOENCODING=utf-8 venv/Scripts/python -c "
import json, urllib.request
pid = 5
def call(method, path, body=None, port=8001):
    req = urllib.request.Request(f'http://127.0.0.1:{port}/api' + path, method=method)
    req.add_header('Content-Type', 'application/json')
    data = json.dumps(body).encode('utf-8') if body is not None else None
    try:
        with urllib.request.urlopen(req, data, timeout=120) as resp:
            raw = resp.read(); return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raw = e.read(); return e.code, json.loads(raw) if raw else None

print('=== 3(再测). 演示模式重规划：应调整逾期任务 18 ===')
code, replan = call('POST', f'/projects/{pid}/replan')
print('状态码:', code, '| 调整数:', len(replan['changes']))
for c in replan['changes']:
    print(f\"  [{c['taskId']}] {c['title']} → {c['plannedStartDate']}~{c['plannedEndDate']} 优先级={c['priority']}\")

print()
print('=== 4. 接受调整 ===')
code, result = call('POST', f\"/replans/{replan['id']}/adopt\")
print('状态码:', code, '| applied:', result['appliedCount'], '| status:', result['replan']['status'])
code, detail = call('GET', f'/projects/{pid}')
for t in detail['tasks']:
    if t['id'] == 18:
        print(f\"  逾期任务更新后: {t['plannedStartDate']}~{t['plannedEndDate']} 优先级={t['priority']}\")
"

OUT
=== 3(再测). 演示模式重规划：应调整逾期任务 18 ===
状态码: 200 | 调整数: 1
  [18] 核心实验（已逾期） → 2026-10-12~2026-10-25 优先级=high

=== 4. 接受调整 ===
状态码: 200 | applied: 1 | status: adopted
  逾期任务更新后: 2026-10-12~2026-10-25 优先级=high
6:31 PM
演示模式修复完成，采纳后任务表正确更新。现在测真实 DeepSeek 重规划：



Bash Start real-key backend on 8002
IN
cd E:/ResearchPilot/backend && venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8002

OUT
Command running in background with ID: bk2e6w2j1. Output is being written to: C:\Users\86198\AppData\Local\Temp\claude\e--ResearchPilot\2116447b-6bbd-4fce-8d5e-e14ee02533b8\tasks\bk2e6w2j1.output. You will be notified when it completes. To check interim output, use Read on that file path.
Session cwd remains E:\ResearchPilot\backend; directory changes made by the backgrounded command do not apply to subsequent commands.
Bash Test real DeepSeek replan generation
IN
sleep 3 && cd E:/ResearchPilot/backend && PYTHONIOENCODING=utf-8 venv/Scripts/python -c "
import json, urllib.request
pid = 5
def call(method, path, body=None, port=8002):
    req = urllib.request.Request(f'http://127.0.0.1:{port}/api' + path, method=method)
    req.add_header('Content-Type', 'application/json')
    data = json.dumps(body).encode('utf-8') if body is not None else None
    try:
        with urllib.request.urlopen(req, data, timeout=120) as resp:
            raw = resp.read(); return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raw = e.read(); return e.code, json.loads(raw) if raw else None

print('=== 5. 真实 DeepSeek 重规划 ===')
code, replan = call('POST', f'/projects/{pid}/replan')
print('状态码:', code, '| source:', replan['source'], '| status:', replan['status'])
print('方案说明:', replan['planContent'][:250])
print()
print('影响评估:', replan['impactSummary'][:150])
print()
print('调整建议:')
for c in replan['changes']:
    print(f\"  [任务{c['taskId']}] {c['title']} action={c['action']}\")
    print(f\"    → {c['plannedStartDate']}~{c['plannedEndDate']} 优先级={c['priority']} 工时={c['estimatedHours']}\")
    print(f\"    理由: {c['reason'][:80]}\")
print()
print('原计划快照（前2条）:', json.dumps(replan['originalTasks'][:2], ensure_ascii=False)[:300])
"

OUT
=== 5. 真实 DeepSeek 重规划 ===
状态码: 200 | source: deepseek | status: pending
方案说明: 当前项目剩余 30 天、每周可用 10 小时（合计约 40 小时可用工时）。核心实验（任务18）已逾期且仅完成 40%，原计划 10-25 结束偏紧，需顺延至 10-31 以保证 30 小时投入；论文撰写（任务19）被任务18阻塞，需在核心实验完成后启动，顺延至 11-01 至 11-08；答辩准备（任务20）原计划 10-27 开始，与顺延后的论文撰写冲突，调整为 11-08 至 11-11。文献综述已完成，不做调整。

影响评估: 整体项目仍可在 2026-11-11 截止日期前完成，但关键路径后移：核心实验延至 10-31，论文撰写 11-01 至 11-08，答辩准备压缩至 11-08 至 11-11（3 天，8 小时）。总工时需求约 58 小时，超出剩余可用工时约 18 小时，存在工时不足风险，建议提高每周投入或压缩论文

调整建议:
  [任务18] 核心实验（已逾期） action=reschedule
    → 2026-10-12~2026-10-31 优先级=high 工时=30.0
    理由: 任务已逾期且仅完成 40%，原计划 10-25 结束过于紧张，顺延至 10-31 以留出足够时间完成剩余 60% 工作量，并保持高优先级。
  [任务19] 论文撰写（被前置阻塞） action=reschedule
    → 2026-11-01~2026-11-08 优先级=medium 工时=20.0
    理由: 该任务被前置任务「核心实验」阻塞，需待核心实验 10-31 完成后再启动，故顺延至 11-01 开始，11-08 结束。
  [任务20] 答辩准备（正常） action=reschedule
    → 2026-11-08~2026-11-11 优先级=medium 工时=8.0
    理由: 原计划 10-27 开始与顺延后的论文撰写时间冲突，调整为 11-08 至 11-11，确保论文完成后进行答辩准备，并赶在项目截止日期前完成。

原计划快照（前2条）: [{"taskId": 17, "title": "文献综述（已完成）", "status": "done", "progress": 100, "priority": "medium", "plannedStartDate": null, "plannedEndDate": null, "estimatedHours": null, "riskLevel": "none", "riskReasons": []}, {"taskId": 18, "title": "核心实验（已逾期）", "status": "todo", "progress": 40, "priority": "high",
6:31 PM
真实 DeepSeek 方案质量很高（顺延关键路径、识别出 18 小时工时缺口）。采纳并完成最后验证与清理：



Bash Adopt real replan, verify, cleanup and regression
IN
cd E:/ResearchPilot/backend && PYTHONIOENCODING=utf-8 venv/Scripts/python -c "
import json, urllib.request
pid = 5
def call(method, path, body=None, port=8002):
    req = urllib.request.Request(f'http://127.0.0.1:{port}/api' + path, method=method)
    req.add_header('Content-Type', 'application/json')
    data = json.dumps(body).encode('utf-8') if body is not None else None
    try:
        with urllib.request.urlopen(req, data, timeout=120) as resp:
            raw = resp.read(); return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raw = e.read(); return e.code, json.loads(raw) if raw else None

# 采纳最新的 pending 方案
code, history = call('GET', f'/projects/{pid}/replans')
pending = next(h for h in history if h['status'] == 'pending')
code, result = call('POST', f\"/replans/{pending['id']}/adopt\")
print('采纳真实方案:', code, '| applied:', result['appliedCount'])
code, detail = call('GET', f'/projects/{pid}')
for t in detail['tasks']:
    print(f\"  任务 {t['id']}「{t['title']}」: {t['plannedStartDate']}~{t['plannedEndDate']} 优先级={t['priority']}\")
print()
print('=== 历史记录（含原计划/新计划/时间/状态） ===')
code, history = call('GET', f'/projects/{pid}/replans')
for h in history:
    print(f\"  #{h['id']} [{h['source']}] status={h['status']} created={h['createdAt'][:16]} changes={len(h['changes'])}\")
print()
print('=== 清理测试数据 ===')
call('DELETE', f'/projects/{pid}')
print('已删除项目 5（级联清理重规划历史）')
" && rm -f _test_replan_state.json && curl -s -m 5 -o /dev/null -w "8000 health: %{http_code}\n" http://127.0.0.1:8000/api/health && curl -s http://127.0.0.1:8000/openapi.json | PYTHONIOENCODING=utf-8 venv/Scripts/python -c "import json,sys; d=json.load(sys.stdin); print('重规划路由:', [p for p in d['paths'] if 'replan' in p])" && PYTHONIOENCODING=utf-8 venv/Scripts/python smoke_test.py http://127.0.0.1:8000 2>&1 | tail -2

OUT
采纳真实方案: 200 | applied: 3
  任务 17「文献综述（已完成）」: None~None 优先级=medium
  任务 18「核心实验（已逾期）」: 2026-10-12~2026-10-31 优先级=high
  任务 19「论文撰写（被前置阻塞）」: 2026-11-01~2026-11-08 优先级=medium
  任务 20「答辩准备（正常）」: 2026-11-08~2026-11-11 优先级=medium

=== 历史记录（含原计划/新计划/时间/状态） ===
  #5 [deepseek] status=adopted created=2026-10-12T18:31 changes=3
  #4 [demo] status=adopted created=2026-10-12T18:30 changes=1
  #3 [demo] status=rejected created=2026-10-12T18:30 changes=0
  #2 [demo] status=adopted created=2026-10-12T18:30 changes=1
  #1 [demo] status=pending created=2026-10-12T18:28 changes=0

=== 清理测试数据 ===
已删除项目 5（级联清理重规划历史）
8000 health: 200
重规划路由: ['/api/projects/{project_id}/replan', '/api/replans/{replan_id}/adopt', '/api/replans/{replan_id}/reject', '/api/projects/{project_id}/replans']

===== 通过 36 项，失败 0 项 =====
TaskStop
IN
{
  "task_id": "bmzx7kjez"
}
OUT
{"message":"Successfully stopped task: bmzx7kjez (cd E:/ResearchPilot/backend && DEEPSEEK_API_KEY= venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001)","task_id":"bmzx7kjez","task_type":"local_bash","command":"cd E:/ResearchPilot/backend && DEEPSEEK_API_KEY= venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001"}
TaskStop
IN
{
  "task_id": "bk2e6w2j1"
}
OUT
{"message":"Successfully stopped task: bk2e6w2j1 (cd E:/ResearchPilot/backend && venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8002)","task_id":"bk2e6w2j1","task_type":"local_bash","command":"cd E:/ResearchPilot/backend && venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8002"}
6:32 PM
核心功能「风险预警 + DeepSeek 动态重规划」开发完成，全部实测通过。

实现内容
风险引擎升级（services/risk.py，纯本地规则、不调大模型）：

规则	等级	示例输出（可解释）
逾期	🔴 高	已逾期 2 天，进度仅 40%
前置任务阻塞（新增）	🟡 中	前置任务「核心实验」尚未完成，当前任务被阻塞
进度落后	🟡 中	进度落后计划 25%，当前进度 40%
剩余工时不足（新增）	🟡 中	剩余约 20 小时工作量，距计划截止还有 10 天（约 14 小时可用），可能不足
任务卡、项目详情、风险横幅自动展示这些原因。

重规划（services/replan_service.py + routers/replans.py）：

POST /api/projects/{id}/replan：后端打包全部任务状态 + 剩余时间 + 每周可用工时 + 本地风险原因作上下文 → DeepSeek 输出严格 JSON（plan_content 方案说明 / impact_summary 进度影响 / changes 调整列表，含逐条理由）；格式错误自动重试 2 次；无 Key 时本地规则模拟调整（演示模式）；生成时写入 replan_history（原计划快照 + 新计划 + 时间 + 理由），状态 pending
POST /api/replans/{id}/adopt：应用调整到任务表（改起止日期/优先级/工时，日期自动收敛在项目截止日内），状态 adopted
POST /api/replans/{id}/reject：放弃，状态 rejected
GET /api/projects/{id}/replans：历史记录
前端（ReplanTab.tsx，项目详情页第 4 个 Tab）：

风险预警列表（红色/黄色卡片 + 可解释原因 + 风险任务计数徽章）
【重新规划】按钮（加载动画；失败 toast）
原计划 vs 新计划对比表格：改动行高亮 + "调整"徽章，改动字段显示删除线旧值 → 高亮新值
调整理由逐条列出 + 方案说明 + 影响评估
【接受调整】/【放弃】按钮；接受后看板自动刷新
重规划历史列表（状态徽章：待处理/已采纳/已放弃 + 演示模式标记 + 时间 + 方案摘要）
原有任务生成与 CRUD 代码零改动。

实测结果
测试	结果
风险引擎	逾期→high、前置阻塞→medium（新规则）、正常→none、项目级 high，原因全部可解释 ✓
演示模式重规划	本地规则把逾期任务顺延至截止日内 + 优先级提为 high ✓
真实 DeepSeek 重规划	3 条调整全部引用真实任务 id：核心实验顺延 10-31、被阻塞的论文撰写顺延 11-0108、答辩准备压缩到 11-0811；影响评估还算出总工时缺口约 18 小时并建议提高投入 ✓
接受调整	任务表日期/优先级实际更新（applied=3），状态 adopted ✓
放弃	状态 rejected，任务表不变 ✓
历史记录	5 条记录含原计划/新计划/时间/状态/来源 ✓
回归	冒烟 36/36 ✓；前端构建 ✓；你的 8000 已自动加载 4 条新路由 ✓
测试流程（浏览器操作）
后端运行中（--reload 已自动加载），刷新前端
打开任意项目 → 「项目仪表盘」→ 顶部**「重规划」**Tab
构造延期（若项目还没有风险任务）：切到「任务看板」→ 新增任务时把"计划截止日期"设为过去，或把某任务的前置设为未完成任务
回到「重规划」Tab → 「风险预警」区显示风险任务和具体原因
点【重新规划】→ 约 10~30 秒 → 出现方案说明、影响评估和新旧对比表（改动行高亮、旧值删除线→新值）
点【接受调整】→ toast 提示调整了几个任务 → 切回「任务看板」确认任务日期/优先级已变
再生成一次点【放弃】→ 任务保持不变
「重规划历史」里查看所有记录（含已采纳/已放弃状态、时间、方案摘要）
演示模式：删掉 .env 的 Key 重启后端 → 生成时徽章显示"演示模式"，使用本地规则模拟调整
开发中修复的两个 bug（已回归验证）：演示模式的风险筛选条件写反（类型名和中文原因混用）；快照风险等级用字符串 max() 导致 "medium" > "high" 字典序错误。



现在后端开始报错(.venv) PS E:\ResearchPilot\backend> uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
>> 
INFO:     Will watch for changes in these directories: ['E:\\ResearchPilot\\backend']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [23696] using WatchFiles
Process SpawnProcess-1:
Traceback (most recent call last):
  File "E:\python\Lib\multiprocessing\process.py", line 314, in _bootstrap
    self.run()
  File "E:\python\Lib\multiprocessing\process.py", line 108, in run
    self._target(*self._args, **self._kwargs)
  File "e:\ResearchPilot\.venv\Lib\site-packages\uvicorn\_subprocess.py", line 80, in subprocess_started
    target(sockets=sockets)
  File "e:\ResearchPilot\.venv\Lib\site-packages\uvicorn\server.py", line 86, in run
    return asyncio_run(self.serve(sockets=sockets), loop_factory=self.config.get_loop_factory())
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "E:\python\Lib\asyncio\runners.py", line 194, in run
    return runner.run(main)
           ^^^^^^^^^^^^^^^^
  File "E:\python\Lib\asyncio\runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "E:\python\Lib\asyncio\base_events.py", line 687, in run_until_complete
    return future.result()
           ^^^^^^^^^^^^^^^
  File "e:\ResearchPilot\.venv\Lib\site-packages\uvicorn\server.py", line 90, in serve
    await self._serve(sockets)
  File "e:\ResearchPilot\.venv\Lib\site-packages\uvicorn\server.py", line 97, in _serve
    config.load()
  File "e:\ResearchPilot\.venv\Lib\site-packages\uvicorn\config.py", line 511, in load
    self.loaded_app = self.load_app()
                      ^^^^^^^^^^^^^^^
  File "e:\ResearchPilot\.venv\Lib\site-packages\uvicorn\config.py", line 434, in load_app
    return import_from_string(self.app)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "e:\ResearchPilot\.venv\Lib\site-packages\uvicorn\importer.py", line 22, in import_from_string
    raise exc from None
  File "e:\ResearchPilot\.venv\Lib\site-packages\uvicorn\importer.py", line 19, in import_from_string
    module = importlib.import_module(module_str)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "E:\python\Lib\importlib\__init__.py", line 90, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<frozen importlib._bootstrap>", line 1387, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1360, in _find_and_load
  File "<frozen importlib._bootstrap>", line 1331, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 935, in _load_unlocked
  File "<frozen importlib._bootstrap_external>", line 995, in exec_module
  File "<frozen importlib._bootstrap>", line 488, in _call_with_frames_removed
  File "E:\ResearchPilot\backend\app\main.py", line 12, in <module>
    from app.routers import ai, documents, home, projects, replans, report, reports, tasks
  File "E:\ResearchPilot\backend\app\routers\ai.py", line 13, in <module>
    from app.ai_client import DeepSeekError
  File "E:\ResearchPilot\backend\app\ai_client.py", line 5, in <module>
    import httpx
ModuleNotFoundError: No module named 'httpx'
INFO:     Stopping reloader process [23696]
(.venv) PS E:\ResearchPilot\backend> uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
INFO:     Will watch for changes in these directories: ['E:\\ResearchPilot\\backend']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [29832] using WatchFiles
Process SpawnProcess-1:
Traceback (most recent call last):
  File "E:\python\Lib\multiprocessing\process.py", line 314, in _bootstrap
    self.run()
  File "E:\python\Lib\multiprocessing\process.py", line 108, in run
    self._target(*self._args, **self._kwargs)
  File "e:\ResearchPilot\.venv\Lib\site-packages\uvicorn\_subprocess.py", line 80, in subprocess_started
    target(sockets=sockets)
  File "e:\ResearchPilot\.venv\Lib\site-packages\uvicorn\server.py", line 86, in run
    return asyncio_run(self.serve(sockets=sockets), loop_factory=self.config.get_loop_factory())
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "E:\python\Lib\asyncio\runners.py", line 194, in run
    return runner.run(main)
           ^^^^^^^^^^^^^^^^
  File "E:\python\Lib\asyncio\runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "E:\python\Lib\asyncio\base_events.py", line 687, in run_until_complete
    return future.result()
           ^^^^^^^^^^^^^^^
  File "e:\ResearchPilot\.venv\Lib\site-packages\uvicorn\server.py", line 90, in serve
    await self._serve(sockets)
  File "e:\ResearchPilot\.venv\Lib\site-packages\uvicorn\server.py", line 97, in _serve
    config.load()
  File "e:\ResearchPilot\.venv\Lib\site-packages\uvicorn\config.py", line 511, in load
    self.loaded_app = self.load_app()
                      ^^^^^^^^^^^^^^^
  File "e:\ResearchPilot\.venv\Lib\site-packages\uvicorn\config.py", line 434, in load_app
    return import_from_string(self.app)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "e:\ResearchPilot\.venv\Lib\site-packages\uvicorn\importer.py", line 22, in import_from_string
    raise exc from None
  File "e:\ResearchPilot\.venv\Lib\site-packages\uvicorn\importer.py", line 19, in import_from_string
    module = importlib.import_module(module_str)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "E:\python\Lib\importlib\__init__.py", line 90, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<frozen importlib._bootstrap>", line 1387, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1360, in _find_and_load
  File "<frozen importlib._bootstrap>", line 1331, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 935, in _load_unlocked
  File "<frozen importlib._bootstrap_external>", line 995, in exec_module
  File "<frozen importlib._bootstrap>", line 488, in _call_with_frames_removed
  File "E:\ResearchPilot\backend\app\main.py", line 12, in <module>
    from app.routers import ai, documents, home, projects, replans, report, reports, tasks
  File "E:\ResearchPilot\backend\app\routers\ai.py", line 13, in <module>
    from app.ai_client import DeepSeekError
  File "E:\ResearchPilot\backend\app\ai_client.py", line 5, in <module>
    import httpx
运行之后的所有界面都显示加载失败，请求失败，请帮我修改
Show more
6:40 PM
问题很明确：你现在激活的是仓库根目录下的 .venv（E:\ResearchPilot\.venv），它里面只装了 uvicorn 等基础包，没有 httpx（还有 pypdf、jieba、python-dotenv 等后来加的依赖也没装）。所以后端一启动就 ModuleNotFoundError: No module named 'httpx'，前端自然全部"加载失败"。

修复：把完整依赖装进这个 .venv：



Bash Install all backend requirements into root .venv
IN
ls E:/ResearchPilot/.venv/Scripts/python.exe 2>/dev/null && E:/ResearchPilot/.venv/Scripts/python -m pip install -r E:/ResearchPilot/backend/requirements.txt --quiet 2>&1 | tail -2; E:/ResearchPilot/.venv/Scripts/python -m pip list 2>/dev/null | grep -iE "httpx|pypdf|jieba|multipart|dotenv|fastapi|sqlalchemy"

OUT
E:/ResearchPilot/.venv/Scripts/python.exe
[notice] A new release of pip is available: 24.0 -> 26.2.1
[notice] To update, run: E:\ResearchPilot\.venv\Scripts\python.exe -m pip install --upgrade pip
fastapi           0.143.0
httpx             0.28.1
jieba             0.42.1
pypdf             6.20.0
python-dotenv     1.2.4
python-multipart  0.0.32
SQLAlchemy        2.1.4
6:40 PM
依赖装齐了。用这个 .venv 验证后端能正常启动：



Bash Test boot backend with root .venv on 8001
IN
cd E:/ResearchPilot/backend && E:/ResearchPilot/.venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001

OUT
Command running in background with ID: b460ltsz5. Output is being written to: C:\Users\86198\AppData\Local\Temp\claude\e--ResearchPilot\2116447b-6bbd-4fce-8d5e-e14ee02533b8\tasks\b460ltsz5.output. You will be notified when it completes. To check interim output, use Read on that file path.
Session cwd remains E:\ResearchPilot\backend; directory changes made by the backgrounded command do not apply to subsequent commands.
Bash Verify backend boots with all routes
IN
sleep 4 && curl -s -m 5 -o /dev/null -w "health: %{http_code}\n" http://127.0.0.1:8001/api/health && curl -s -m 5 -o /dev/null -w "home: %{http_code}\n" http://127.0.0.1:8001/api/home && curl -s -m 5 -o /dev/null -w "projects: %{http_code}\n" http://127.0.0.1:8001/api/projects && curl -s http://127.0.0.1:8001/openapi.json | E:/ResearchPilot/.venv/Scripts/python -c "import json,sys; d=json.load(sys.stdin); print('路由总数:', len(d['paths']), '| 分组:', sorted({v.get('tags',[''])[0] for v in d['paths'].values()}))"

OUT
health: 200
home: 200
projects: 200
·������: 23 | ����: ['']
6:41 PM
后端用新 .venv 启动正常，全部路由注册成功。跑一遍冒烟测试确认无回归：



Bash Run smoke test against .venv-backed instance
IN
cd E:/ResearchPilot/backend && PYTHONIOENCODING=utf-8 E:/ResearchPilot/.venv/Scripts/python smoke_test.py http://127.0.0.1:8001 2>&1 | tail -2

OUT
===== 通过 36 项，失败 0 项 =====
TaskStop
IN
{
  "task_id": "b460ltsz5"
}
OUT
{"message":"Successfully stopped task: b460ltsz5 (cd E:/ResearchPilot/backend && E:/ResearchPilot/.venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001)","task_id":"b460ltsz5","task_type":"local_bash","command":"cd E:/ResearchPilot/backend && E:/ResearchPilot/.venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001"}
6:41 PM
修好了。

问题原因
报错不是代码问题，是虚拟环境用错了：

你激活的是仓库根目录的 .venv（E:\ResearchPilot\.venv，报错堆栈里能看到 e:\ResearchPilot\.venv\Lib\...）
这个 .venv 里只有 uvicorn 等基础包，没有 httpx（也没有 pypdf、jieba、python-dotenv、python-multipart）
所以后端 import httpx 直接崩 → 后端没起来 → 前端所有请求失败，显示"加载失败"
之前开发时用的完整依赖环境是 backend\venv，你这次换成了根目录的 .venv。

已做的修复
把 requirements.txt 的完整依赖装进了你正在用的 E:\ResearchPilot\.venv：


fastapi / httpx / jieba / pypdf / python-dotenv / python-multipart / sqlalchemy / starlette / uvicorn ✓
并用这个 .venv 实测：后端启动成功、23 条路由全部注册、health/home/projects 全 200、冒烟测试 36/36 通过 ✓

你现在要做的
回到你的 PowerShell 终端，重新执行启动命令即可（你之前的进程已经因报错退出了）：


uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
看到 Application startup complete 后，刷新前端页面（Ctrl+F5），所有界面恢复。

补充建议：以后启动前先确认激活的是哪个环境——推荐统一用依赖最全的 backend\venv（执行 E:\ResearchPilot\backend\venv\Scripts\activate），或者就保持现在的根目录 .venv 也行，我刚已把它补全了。两边现在依赖一致，用哪个都不会再报缺包。
