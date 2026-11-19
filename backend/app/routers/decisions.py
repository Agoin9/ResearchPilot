"""科研决策记录接口（v2.1 新增）：

研究者本人基于真实实验运行记录做出的判断：
观察到的事实、分析解释、是否支持假设、未知因素、下一步研究建议。
所有内容由用户真实录入，系统不做任何生成或填充。

关联校验：run_ids 必须属于该实验（防跨实验引用）；
删除决策不影响实验与运行记录。
"""
import json

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Experiment, ExperimentRun, Project, ResearchDecision
from app.schemas import DecisionCreate, DecisionOut, DecisionUpdate

router = APIRouter(tags=["科研决策"])


def _get_experiment_or_404(db: Session, experiment_id: int) -> Experiment:
    experiment = db.get(Experiment, experiment_id)
    if experiment is None:
        raise HTTPException(status_code=404, detail="实验不存在")
    return experiment


def _get_decision_or_404(db: Session, decision_id: int) -> ResearchDecision:
    decision = db.get(ResearchDecision, decision_id)
    if decision is None:
        raise HTTPException(status_code=404, detail="决策记录不存在")
    return decision


def _decision_out(decision: ResearchDecision) -> DecisionOut:
    return DecisionOut(
        id=decision.id,
        project_id=decision.project_id,
        experiment_id=decision.experiment_id,
        run_ids=json.loads(decision.run_ids_json or "[]"),
        observations=decision.observations,
        interpretation=decision.interpretation,
        supports_hypothesis=(
            bool(decision.supports_hypothesis)
            if decision.supports_hypothesis is not None
            else None
        ),
        unknowns=decision.unknowns,
        next_suggestions=json.loads(decision.next_suggestions_json or "[]"),
        created_at=decision.created_at,
        updated_at=decision.updated_at,
    )


def _validate_run_ids(db: Session, experiment_id: int, run_ids: list[int]) -> None:
    """校验关联运行记录：必须真实存在且属于该实验。"""
    if not run_ids:
        raise HTTPException(status_code=422, detail="请至少选择一条关联的实验运行记录")
    runs = db.scalars(
        select(ExperimentRun).where(ExperimentRun.id.in_(run_ids))
    ).all()
    found = {run.id for run in runs}
    missing = [rid for rid in run_ids if rid not in found]
    if missing:
        raise HTTPException(status_code=400, detail=f"运行记录不存在：{missing}")
    foreign = [run.id for run in runs if run.experiment_id != experiment_id]
    if foreign:
        raise HTTPException(
            status_code=400,
            detail=f"运行记录不属于该实验：{foreign}",
        )


@router.post(
    "/experiments/{experiment_id}/decisions",
    response_model=DecisionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_decision(experiment_id: int, data: DecisionCreate, db: Session = Depends(get_db)):
    """创建科研决策记录（内容全部来自研究者本人）。"""
    experiment = _get_experiment_or_404(db, experiment_id)
    _validate_run_ids(db, experiment_id, data.run_ids)

    decision = ResearchDecision(
        project_id=experiment.project_id,
        experiment_id=experiment.id,
        run_ids_json=json.dumps(data.run_ids, ensure_ascii=False),
        observations=data.observations,
        interpretation=data.interpretation,
        supports_hypothesis=(
            int(data.supports_hypothesis) if data.supports_hypothesis is not None else None
        ),
        unknowns=data.unknowns,
        next_suggestions_json=json.dumps(data.next_suggestions or [], ensure_ascii=False),
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return _decision_out(decision)


@router.get("/experiments/{experiment_id}/decisions", response_model=list[DecisionOut])
def list_experiment_decisions(experiment_id: int, db: Session = Depends(get_db)):
    """该实验的决策记录列表（最新在前）。"""
    _get_experiment_or_404(db, experiment_id)
    rows = db.scalars(
        select(ResearchDecision)
        .where(ResearchDecision.experiment_id == experiment_id)
        .order_by(ResearchDecision.created_at.desc())
    ).all()
    return [_decision_out(d) for d in rows]


@router.get("/projects/{project_id}/decisions", response_model=list[DecisionOut])
def list_project_decisions(project_id: int, db: Session = Depends(get_db)):
    """项目下全部决策记录（最新在前）。"""
    if db.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    rows = db.scalars(
        select(ResearchDecision)
        .where(ResearchDecision.project_id == project_id)
        .order_by(ResearchDecision.created_at.desc())
    ).all()
    return [_decision_out(d) for d in rows]


@router.get("/decisions/{decision_id}", response_model=DecisionOut)
def get_decision(decision_id: int, db: Session = Depends(get_db)):
    """决策记录详情。"""
    return _decision_out(_get_decision_or_404(db, decision_id))


@router.put("/decisions/{decision_id}", response_model=DecisionOut)
def update_decision(decision_id: int, data: DecisionUpdate, db: Session = Depends(get_db)):
    """更新决策记录（所有字段可选）。"""
    decision = _get_decision_or_404(db, decision_id)
    payload = data.model_dump(exclude_unset=True)
    if "run_ids" in payload and payload["run_ids"] is not None:
        _validate_run_ids(db, decision.experiment_id, payload.pop("run_ids"))
        decision.run_ids_json = json.dumps(data.run_ids, ensure_ascii=False)
    if "supports_hypothesis" in payload:
        value = payload.pop("supports_hypothesis")
        decision.supports_hypothesis = int(value) if value is not None else None
    if "next_suggestions" in payload:
        value = payload.pop("next_suggestions")
        if value is not None:
            decision.next_suggestions_json = json.dumps(value, ensure_ascii=False)
    for field, value in payload.items():
        setattr(decision, field, value)
    db.commit()
    db.refresh(decision)
    return _decision_out(decision)


@router.delete("/decisions/{decision_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_decision(decision_id: int, db: Session = Depends(get_db)):
    """删除决策记录（不影响实验与运行记录）。"""
    decision = _get_decision_or_404(db, decision_id)
    db.delete(decision)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
