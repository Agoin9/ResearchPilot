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
