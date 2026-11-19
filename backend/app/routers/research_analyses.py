"""AI 研究分析接口（v2.2）：

POST /questions/{id}/analysis    按研究问题聚合真实数据生成分析
GET  /questions/{id}/analyses    分析历史
GET  /research-analyses/{id}     分析详情
POST /research-analyses/{id}/suggestions/{i}/to-task   用户确认后转科研任务

严格约束：
- 前端不直接请求模型，全部经由本后端；
- 无运行记录 → 400 明确提示（不用虚构结果替代）；
- 无 Key → 演示模板（统计值真实、文字模板、source=demo、warning 提示）；
- 用户采纳建议之前不修改任何实验记录或任务计划（本接口只读真实数据并新增
  分析记录；转任务必须显式调用 to-task）。
"""
import json
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai_client import DeepSeekError
from app.database import get_db
from app.models import ResearchActionLog, ResearchAnalysis, ResearchQuestion, Task
from app.schemas import (
    NextExperimentOut,
    ObservedFactOut,
    PaperEvidenceOut,
    ResearchActionLogOut,
    ResearchAnalysisOut,
    ResearchAnalysisToTaskOut,
    SuggestionAdoptOut,
    SuggestionAdoptRequest,
    SuggestionModifyRequest,
    SuggestionRejectRequest,
)
from app.services.research_adoption import (
    adopt_suggestion,
    modify_suggestion,
    reject_suggestion,
)
from app.services.research_analysis import (
    DEMO_WARNING,
    ResearchAnalysisError,
    generate_analysis,
)
from app.services.serializers import build_task_out
from app.routers.experiments import _experiment_out

router = APIRouter(tags=["研究分析"])


def _get_question_or_404(db: Session, question_id: int) -> ResearchQuestion:
    question = db.get(ResearchQuestion, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="研究问题不存在")
    return question


def _get_analysis_or_404(db: Session, analysis_id: int) -> ResearchAnalysis:
    analysis = db.get(ResearchAnalysis, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="分析记录不存在")
    return analysis


def _analysis_out(analysis: ResearchAnalysis) -> ResearchAnalysisOut:
    return ResearchAnalysisOut(
        id=analysis.id,
        project_id=analysis.project_id,
        question_id=analysis.question_id,
        experiment_ids=json.loads(analysis.experiment_ids_json or "[]"),
        run_ids=json.loads(analysis.run_ids_json or "[]"),
        card_ids=json.loads(analysis.card_ids_json or "[]"),
        observed_facts=[ObservedFactOut(**f) for f in json.loads(analysis.observed_facts_json or "[]")],
        paper_evidence=[PaperEvidenceOut(**e) for e in json.loads(analysis.paper_evidence_json or "[]")],
        stats=json.loads(analysis.stats_json or "{}"),
        interpretation=analysis.interpretation,
        hypothesis_status=analysis.hypothesis_status,
        uncertainty=analysis.uncertainty,
        next_experiments=[
            NextExperimentOut(**{k: v for k, v in n.items() if k != "reject_reason"})
            for n in json.loads(analysis.next_experiments_json or "[]")
        ],
        source=analysis.source,
        warning=DEMO_WARNING if analysis.source == "demo" else "",
        created_at=analysis.created_at,
    )


@router.post("/questions/{question_id}/analysis", response_model=ResearchAnalysisOut)
def create_analysis(question_id: int, db: Session = Depends(get_db)):
    """按研究问题生成 AI 研究分析（只读真实数据，不修改任何实验/任务）。"""
    question = _get_question_or_404(db, question_id)
    try:
        sections, source, context = generate_analysis(db, question)
    except ResearchAnalysisError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DeepSeekError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # 数据快照：覆盖本次分析实际读取的全部数据（统计基于全部运行记录）
    run_ids = sorted(context["valid_run_ids"])
    card_ids = sorted({c["id"] for c in context["cards"]})
    experiment_ids = sorted({e["id"] for e in context["experiments"]})

    analysis = ResearchAnalysis(
        project_id=question.project_id,
        question_id=question.id,
        experiment_ids_json=json.dumps(experiment_ids, ensure_ascii=False),
        run_ids_json=json.dumps(run_ids, ensure_ascii=False),
        card_ids_json=json.dumps(card_ids, ensure_ascii=False),
        observed_facts_json=json.dumps(sections["observed_facts"], ensure_ascii=False),
        paper_evidence_json=json.dumps(sections["paper_evidence"], ensure_ascii=False),
        stats_json=json.dumps(context["stats"], ensure_ascii=False),
        interpretation=sections["interpretation"],
        hypothesis_status=sections["hypothesis_status"],
        uncertainty=sections["uncertainty"],
        next_experiments_json=json.dumps(sections["next_experiments"], ensure_ascii=False),
        source=source,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return _analysis_out(analysis)


@router.get("/questions/{question_id}/analyses", response_model=list[ResearchAnalysisOut])
def list_question_analyses(question_id: int, db: Session = Depends(get_db)):
    """该研究问题的分析历史（最新在前）。"""
    _get_question_or_404(db, question_id)
    rows = db.scalars(
        select(ResearchAnalysis)
        .where(ResearchAnalysis.question_id == question_id)
        .order_by(ResearchAnalysis.created_at.desc())
    ).all()
    return [_analysis_out(a) for a in rows]


@router.get("/research-analyses/{analysis_id}", response_model=ResearchAnalysisOut)
def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """分析详情。"""
    return _analysis_out(_get_analysis_or_404(db, analysis_id))


@router.post(
    "/research-analyses/{analysis_id}/suggestions/{suggestion_index}/to-task",
    response_model=ResearchAnalysisToTaskOut,
    status_code=status.HTTP_201_CREATED,
)
def suggestion_to_task(analysis_id: int, suggestion_index: int, db: Session = Depends(get_db)):
    """用户确认：把分析建议转为科研任务（带来源标记，防重复转换）。

    在用户调用本接口之前，不会修改任何实验记录或任务计划。
    """
    analysis = _get_analysis_or_404(db, analysis_id)
    suggestions = json.loads(analysis.next_experiments_json or "[]")
    if not 0 <= suggestion_index < len(suggestions):
        raise HTTPException(status_code=404, detail="建议不存在")
    suggestion = suggestions[suggestion_index]
    if suggestion.get("converted"):
        raise HTTPException(status_code=400, detail="该建议已转换过，不能重复转换")

    title = suggestion["objective"][:200]
    description = (
        f"实验目的：{suggestion['objective']}\n"
        f"待验证假设：{suggestion['hypothesis']}\n"
        f"改变变量：{suggestion.get('changed_variables') or '—'}\n"
        f"保持不变：{suggestion.get('fixed_conditions') or '—'}\n"
        f"评价指标：{suggestion.get('metrics') or '—'}\n"
        f"预期观察：{suggestion.get('expected_observation') or '—'}\n"
        f"风险：{suggestion.get('risks') or '—'}\n"
        f"估计工作量：{suggestion.get('estimated_effort') or '—'}\n\n"
        f"来源：研究分析 #{analysis.id}"
    )
    task = Task(
        project_id=analysis.project_id,
        title=title,
        description=description,
        status="todo",
        priority="medium",
        source_type="research_analysis",
        source_id=analysis.id,
    )
    db.add(task)
    suggestion["converted"] = True
    suggestions[suggestion_index] = suggestion
    analysis.next_experiments_json = json.dumps(suggestions, ensure_ascii=False)
    db.commit()
    db.refresh(task)
    return ResearchAnalysisToTaskOut(task=build_task_out(task), analysis_id=analysis.id)


# ═══════════════════════ v2.3：科研决策 → 执行计划 ═══════════════════════

def _log_out(log: ResearchActionLog) -> ResearchActionLogOut:
    return ResearchActionLogOut(
        id=log.id,
        project_id=log.project_id,
        analysis_id=log.analysis_id,
        suggestion_index=log.suggestion_index,
        action=log.action,
        payload=json.loads(log.payload_json or "{}"),
        task_id=log.task_id,
        experiment_id=log.experiment_id,
        created_at=log.created_at,
    )


@router.post(
    "/research-analyses/{analysis_id}/suggestions/{suggestion_index}/adopt",
    response_model=SuggestionAdoptOut,
    status_code=status.HTTP_201_CREATED,
)
def adopt_analysis_suggestion(
    analysis_id: int,
    suggestion_index: int,
    data: SuggestionAdoptRequest,
    db: Session = Depends(get_db),
):
    """用户确认采纳建议（可先修改字段）：创建 Experiment + 关联 Task。

    科研决策与执行计划分层：AI 建议只是起点；本接口收到的全部字段
    均为用户确认/修改后的内容，提交前系统不做任何创建或修改。
    """
    analysis = _get_analysis_or_404(db, analysis_id)
    payload = {
        "objective": data.objective,
        "hypothesis": data.hypothesis,
        "variables": data.variables,
        "required_data": data.required_data,
        "preconditions": data.preconditions,
        "estimated_hours": data.estimated_hours,
        "planned_start_date": data.planned_start_date.isoformat(),
        "planned_end_date": data.planned_end_date.isoformat(),
        "dependencies": data.dependencies or [],
    }
    try:
        experiment, task, log = adopt_suggestion(
            db, analysis, suggestion_index, payload, date.today()
        )
    except HTTPException:
        raise
    return SuggestionAdoptOut(
        experiment=_experiment_out(db, experiment, []),
        task=build_task_out(task),
        log=_log_out(log),
    )


@router.post(
    "/research-analyses/{analysis_id}/suggestions/{suggestion_index}/reject",
    response_model=ResearchActionLogOut,
)
def reject_analysis_suggestion(
    analysis_id: int,
    suggestion_index: int,
    data: SuggestionRejectRequest | None = None,
    db: Session = Depends(get_db),
):
    """用户拒绝建议：标记 rejected，写入历史（不创建任何实验/任务）。"""
    analysis = _get_analysis_or_404(db, analysis_id)
    try:
        _, log = reject_suggestion(
            db, analysis, suggestion_index, data.reason if data else None
        )
    except HTTPException:
        raise
    return _log_out(log)


@router.put(
    "/research-analyses/{analysis_id}/suggestions/{suggestion_index}",
    response_model=NextExperimentOut,
)
def modify_analysis_suggestion(
    analysis_id: int,
    suggestion_index: int,
    data: SuggestionModifyRequest,
    db: Session = Depends(get_db),
):
    """用户修改建议（不采纳）：保存修改并留档。"""
    analysis = _get_analysis_or_404(db, analysis_id)
    fields = data.model_dump(exclude_unset=True)
    try:
        suggestion, _ = modify_suggestion(db, analysis, suggestion_index, fields)
    except HTTPException:
        raise
    return NextExperimentOut(
        **{k: v for k, v in suggestion.items() if k != "reject_reason"}
    )


@router.get("/research-analyses/{analysis_id}/actions", response_model=list[ResearchActionLogOut])
def list_analysis_actions(analysis_id: int, db: Session = Depends(get_db)):
    """该分析的采纳/拒绝/修改历史（最新在前）。"""
    _get_analysis_or_404(db, analysis_id)
    rows = db.scalars(
        select(ResearchActionLog)
        .where(ResearchActionLog.analysis_id == analysis_id)
        .order_by(ResearchActionLog.created_at.desc())
    ).all()
    return [_log_out(r) for r in rows]
