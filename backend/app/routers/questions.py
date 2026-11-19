"""研究问题接口（v2 科研闭环起点）：

问题可关联文献卡片（证据）与实验；列表附带证据立场计数，
让用户一眼看到每个研究问题目前的证据分布。
"""
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Experiment, LiteratureCard, Project, ResearchQuestion
from app.schemas import (
    QuestionCreate,
    QuestionSummary,
    QuestionUpdate,
)

router = APIRouter(tags=["研究问题"])


def _get_question_or_404(db: Session, question_id: int) -> ResearchQuestion:
    question = db.get(ResearchQuestion, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="研究问题不存在")
    return question


def _build_summary(db: Session, question: ResearchQuestion) -> QuestionSummary:
    """问题 + 证据计数（卡片立场分布 + 实验数）。"""
    evidence = {
        row[0]: row[1]
        for row in db.execute(
            select(LiteratureCard.evidence_type, func.count(LiteratureCard.id))
            .where(LiteratureCard.question_id == question.id)
            .group_by(LiteratureCard.evidence_type)
        )
    }
    experiments_count = db.scalar(
        select(func.count(Experiment.id)).where(Experiment.question_id == question.id)
    ) or 0
    return QuestionSummary(
        id=question.id,
        project_id=question.project_id,
        content=question.content,
        objective=question.objective,
        hypothesis=question.hypothesis,
        answer_summary=question.answer_summary,
        status=question.status,
        created_at=question.created_at,
        updated_at=question.updated_at,
        evidence_support=evidence.get("support", 0),
        evidence_against=evidence.get("against", 0),
        evidence_neutral=evidence.get("neutral", 0),
        experiments_count=experiments_count,
    )


@router.get("/projects/{project_id}/questions", response_model=list[QuestionSummary])
def list_questions(project_id: int, db: Session = Depends(get_db)):
    """项目下的研究问题列表（最新在前，附带证据计数）。"""
    if db.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    questions = db.scalars(
        select(ResearchQuestion)
        .where(ResearchQuestion.project_id == project_id)
        .order_by(ResearchQuestion.created_at.desc())
    ).all()
    return [_build_summary(db, q) for q in questions]


@router.post(
    "/projects/{project_id}/questions",
    response_model=QuestionSummary,
    status_code=status.HTTP_201_CREATED,
)
def create_question(project_id: int, data: QuestionCreate, db: Session = Depends(get_db)):
    """创建研究问题。"""
    if db.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    question = ResearchQuestion(
        project_id=project_id,
        content=data.content,
        objective=data.objective,
        hypothesis=data.hypothesis,
        status=data.status,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return _build_summary(db, question)


@router.get("/questions/{question_id}", response_model=QuestionSummary)
def get_question(question_id: int, db: Session = Depends(get_db)):
    """问题详情（含证据计数）。"""
    return _build_summary(db, _get_question_or_404(db, question_id))


@router.put("/questions/{question_id}", response_model=QuestionSummary)
def update_question(question_id: int, data: QuestionUpdate, db: Session = Depends(get_db)):
    """更新问题（内容/状态/解答摘要）。"""
    question = _get_question_or_404(db, question_id)
    payload = data.model_dump(exclude_unset=True)
    for field, value in payload.items():
        setattr(question, field, value)
    db.commit()
    db.refresh(question)
    return _build_summary(db, question)


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(question_id: int, db: Session = Depends(get_db)):
    """删除问题（关联卡片/实验的 question_id 由数据库置空，不级联删除）。"""
    question = _get_question_or_404(db, question_id)
    db.delete(question)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
