"""AI 实验分析接口（v2 核心模块，P4）：

- 生成分析：只基于真实运行记录 + 文献卡片参照（无运行记录 → 400，无 Key → 400）；
- 手工分析笔记：无 Key 或用户自选时的人工替代（source=manual，不伪装 AI）；
- 决策闭环：分析建议可一键转为科研任务（带来源标记）或实验草稿；
- 分析历史可回看、正文可人工编辑。
"""
import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai_client import DeepSeekError
from app.config import DEEPSEEK_API_KEY
from app.database import get_db
from app.models import (
    Experiment,
    ExperimentAnalysis,
    ExperimentRun,
    LiteratureCard,
    ResearchQuestion,
    Task,
)
from app.schemas import AnalysisNoteCreate, AnalysisOut, ExperimentOut, SuggestionOut, TaskOut
from app.services.experiment_analysis import generate_analysis
from app.services.serializers import build_task_out

router = APIRouter(tags=["实验分析"])


def _get_experiment_or_404(db: Session, experiment_id: int) -> Experiment:
    experiment = db.get(Experiment, experiment_id)
    if experiment is None:
        raise HTTPException(status_code=404, detail="实验不存在")
    return experiment


def _get_analysis_or_404(db: Session, analysis_id: int) -> ExperimentAnalysis:
    analysis = db.get(ExperimentAnalysis, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="分析记录不存在")
    return analysis


def _runs_of(db: Session, experiment_id: int) -> list[ExperimentRun]:
    return list(
        db.scalars(
            select(ExperimentRun)
            .where(ExperimentRun.experiment_id == experiment_id)
            .order_by(ExperimentRun.run_no)
        )
    )


def _analysis_out(analysis: ExperimentAnalysis) -> AnalysisOut:
    return AnalysisOut(
        id=analysis.id,
        project_id=analysis.project_id,
        experiment_id=analysis.experiment_id,
        question_id=analysis.question_id,
        run_ids=json.loads(analysis.run_ids_json or "[]"),
        content=analysis.content,
        suggestions=[
            SuggestionOut(**s) for s in json.loads(analysis.suggestions_json or "[]")
        ],
        source=analysis.source,
        created_at=analysis.created_at,
    )


def _save_suggestions(db: Session, analysis: ExperimentAnalysis, suggestions: list[dict]) -> None:
    analysis.suggestions_json = json.dumps(suggestions, ensure_ascii=False)
    db.commit()


# ═══════════════════════ 生成分析 ═══════════════════════

@router.post("/experiments/{experiment_id}/analysis", response_model=AnalysisOut)
def create_analysis(experiment_id: int, db: Session = Depends(get_db)):
    """基于真实运行记录生成 AI 分析。

    - 实验没有任何运行记录 → 400（拒绝"无米之炊"）；
    - 未配置 DeepSeek Key → 400（提示使用手工分析笔记，不伪造 AI 结论）。
    """
    experiment = _get_experiment_or_404(db, experiment_id)
    runs = _runs_of(db, experiment_id)
    if not runs:
        raise HTTPException(
            status_code=400,
            detail="该实验还没有任何运行记录；AI 分析只基于真实数据，请先录入至少一条运行记录",
        )
    if not DEEPSEEK_API_KEY:
        raise HTTPException(
            status_code=400,
            detail="未配置 DeepSeek API Key，无法生成 AI 分析；请改用「手工分析笔记」，"
            "或在 backend/.env 配置 DEEPSEEK_API_KEY",
        )

    question_content = None
    card_summaries: list[str] = []
    if experiment.question_id is not None:
        question = db.get(ResearchQuestion, experiment.question_id)
        question_content = question.content if question else None
        cards = db.scalars(
            select(LiteratureCard).where(LiteratureCard.question_id == experiment.question_id)
        ).all()
        for card in cards:
            if card.key_results:
                label = card.title or "未命名卡片"
                card_summaries.append(f"「{label}」结论：{card.key_results[:300]}")

    try:
        content, suggestions = generate_analysis(
            experiment, runs, question_content, card_summaries
        )
    except DeepSeekError as e:
        raise HTTPException(status_code=502, detail=str(e))

    analysis = ExperimentAnalysis(
        project_id=experiment.project_id,
        experiment_id=experiment.id,
        question_id=experiment.question_id,
        run_ids_json=json.dumps([r.id for r in runs], ensure_ascii=False),
        content=content,
        suggestions_json=json.dumps(suggestions, ensure_ascii=False),
        source="deepseek",
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return _analysis_out(analysis)


@router.post(
    "/experiments/{experiment_id}/analysis/notes",
    response_model=AnalysisOut,
    status_code=status.HTTP_201_CREATED,
)
def create_analysis_note(experiment_id: int, data: AnalysisNoteCreate, db: Session = Depends(get_db)):
    """手工分析笔记：无 Key 或用户自选时的人工分析记录（source=manual）。"""
    experiment = _get_experiment_or_404(db, experiment_id)
    runs = _runs_of(db, experiment_id)
    analysis = ExperimentAnalysis(
        project_id=experiment.project_id,
        experiment_id=experiment.id,
        question_id=experiment.question_id,
        run_ids_json=json.dumps([r.id for r in runs], ensure_ascii=False),
        content=data.content,
        suggestions_json="[]",
        source="manual",
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return _analysis_out(analysis)


@router.get("/experiments/{experiment_id}/analyses", response_model=list[AnalysisOut])
def list_analyses(experiment_id: int, db: Session = Depends(get_db)):
    """该实验的分析历史（最新在前）。"""
    _get_experiment_or_404(db, experiment_id)
    rows = db.scalars(
        select(ExperimentAnalysis)
        .where(ExperimentAnalysis.experiment_id == experiment_id)
        .order_by(ExperimentAnalysis.created_at.desc())
    ).all()
    return [_analysis_out(a) for a in rows]


@router.get("/analyses/{analysis_id}", response_model=AnalysisOut)
def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """分析详情。"""
    return _analysis_out(_get_analysis_or_404(db, analysis_id))


@router.put("/analyses/{analysis_id}", response_model=AnalysisOut)
def update_analysis(analysis_id: int, data: AnalysisNoteCreate, db: Session = Depends(get_db)):
    """人工编辑分析正文（建议列表保持原样）。"""
    analysis = _get_analysis_or_404(db, analysis_id)
    analysis.content = data.content
    db.commit()
    db.refresh(analysis)
    return _analysis_out(analysis)


# ═══════════════════════ 决策闭环：建议 → 任务 / 实验草稿 ═══════════════════════

@router.post(
    "/analyses/{analysis_id}/suggestions/{suggestion_index}/to-task",
    response_model=TaskOut,
    status_code=status.HTTP_201_CREATED,
)
def suggestion_to_task(analysis_id: int, suggestion_index: int, db: Session = Depends(get_db)):
    """把分析建议转为科研任务（带来源标记，防重复转换）。"""
    analysis = _get_analysis_or_404(db, analysis_id)
    suggestions = json.loads(analysis.suggestions_json or "[]")
    if not 0 <= suggestion_index < len(suggestions):
        raise HTTPException(status_code=404, detail="建议不存在")
    suggestion = suggestions[suggestion_index]
    if suggestion.get("converted"):
        raise HTTPException(status_code=400, detail="该建议已转换过，不能重复转换")

    experiment = db.get(Experiment, analysis.experiment_id)
    title = suggestion["content"][:200]
    description = (
        f"{suggestion['content']}\n\n"
        f"理由：{suggestion.get('reason') or '—'}\n\n"
        f"来源：实验分析 #{analysis.id}（实验「{experiment.title if experiment else '已删除'}」）"
    )
    task = Task(
        project_id=analysis.project_id,
        title=title,
        description=description,
        status="todo",
        priority="medium",
        source_type="experiment_analysis",
        source_id=analysis.id,
    )
    db.add(task)
    suggestion["converted"] = True
    suggestions[suggestion_index] = suggestion
    _save_suggestions(db, analysis, suggestions)
    db.commit()
    db.refresh(task)
    return build_task_out(task)


@router.post(
    "/analyses/{analysis_id}/suggestions/{suggestion_index}/to-experiment",
    response_model=ExperimentOut,
    status_code=status.HTTP_201_CREATED,
)
def suggestion_to_experiment(analysis_id: int, suggestion_index: int, db: Session = Depends(get_db)):
    """把分析建议转为实验草稿（预填目的/假设，用户补充方案后保存）。"""
    analysis = _get_analysis_or_404(db, analysis_id)
    suggestions = json.loads(analysis.suggestions_json or "[]")
    if not 0 <= suggestion_index < len(suggestions):
        raise HTTPException(status_code=404, detail="建议不存在")
    suggestion = suggestions[suggestion_index]
    if suggestion.get("converted"):
        raise HTTPException(status_code=400, detail="该建议已转换过，不能重复转换")

    content = suggestion["content"]
    experiment = Experiment(
        project_id=analysis.project_id,
        question_id=analysis.question_id,
        title=f"实验草稿：{content[:80]}",
        objective=content,
        hypothesis=None,
        design=f"来源：实验分析 #{analysis.id} 的建议\n理由：{suggestion.get('reason') or '—'}",
        status="draft",
    )
    db.add(experiment)
    suggestion["converted"] = True
    suggestions[suggestion_index] = suggestion
    _save_suggestions(db, analysis, suggestions)
    db.commit()
    db.refresh(experiment)
    # 用 runs=[] 序列化，避免递归加载
    from app.routers.experiments import _experiment_out
    return _experiment_out(db, experiment, [])
