"""文献研究卡片接口（v2 核心模块，PaperNote）：

- 对已上传文献 AI 抽取结构化卡片（输入必须是真实存在的 document）；
- 卡片全部字段可人工修改（修改后 source=manual）；
- 卡片可关联研究问题、标记证据立场（support/against/neutral）；
- v2.1：支持创新点与原文证据片段（含页码）录入；
- 支持多卡片字段级对比（数据由后端返回，表格由前端渲染）。
"""
import json

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai_client import DeepSeekError
from app.database import get_db
from app.models import Document, LiteratureCard, Project, ResearchQuestion
from app.schemas import (
    CardCompareOut,
    CardCreate,
    CardExtractOut,
    CardOut,
    CardUpdate,
    EvidenceSnippet,
)
from app.services.literature_card import CardFormatError, extract_card

router = APIRouter(tags=["文献卡片"])


def _get_card_or_404(db: Session, card_id: int) -> LiteratureCard:
    card = db.get(LiteratureCard, card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="研究卡片不存在")
    return card


def _load_snippets(raw: str | None) -> list[EvidenceSnippet]:
    """证据片段 JSON → 模型列表（损坏数据安全降级为空列表）。"""
    try:
        items = json.loads(raw or "[]")
        return [EvidenceSnippet(**item) for item in items if isinstance(item, dict)]
    except (ValueError, TypeError):
        return []


def _card_out(card: LiteratureCard) -> CardOut:
    return CardOut(
        id=card.id,
        project_id=card.project_id,
        document_id=card.document_id,
        question_id=card.question_id,
        title=card.title,
        authors=card.authors,
        year=card.year,
        research_question=card.research_question,
        method=card.method,
        materials_datasets=card.materials_datasets,
        metrics=card.metrics,
        key_results=card.key_results,
        innovations=card.innovations,
        limitations=card.limitations,
        relevance=card.relevance,
        evidence_type=card.evidence_type,
        evidence_snippets=_load_snippets(card.evidence_snippets_json),
        source=card.source,
        created_at=card.created_at,
        updated_at=card.updated_at,
    )


# ═══════════════════════ AI 抽取 ═══════════════════════

@router.post("/documents/{document_id}/card", response_model=CardExtractOut)
def extract_document_card(document_id: int, db: Session = Depends(get_db)):
    """对文献 AI 抽取研究卡片（无 Key 时演示模式返回空模板，手工填写）。

    - 文献不存在 → 404；该文献已有卡片 → 400（避免重复抽取覆盖人工修改）；
    - 抽取结果只来自该文献全文，字段缺失一律留空，不伪造。
    """
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="文献不存在")

    existing = db.scalar(
        select(LiteratureCard).where(LiteratureCard.document_id == document_id)
    )
    if existing is not None:
        raise HTTPException(
            status_code=400,
            detail="该文献已有研究卡片；如需重新抽取请先删除现有卡片",
        )

    try:
        fields, source, warning = extract_card(document.full_text)
    except CardFormatError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DeepSeekError as e:
        raise HTTPException(status_code=502, detail=str(e))

    card = LiteratureCard(
        project_id=document.project_id,
        document_id=document.id,
        title=fields["title"] or None,
        authors=fields["authors"] or None,
        year=fields["year"] or None,
        research_question=fields["research_question"] or None,
        method=fields["method"] or None,
        materials_datasets=fields["materials_datasets"] or None,
        metrics=fields["metrics"] or None,
        key_results=fields["key_results"] or None,
        limitations=fields["limitations"] or None,
        relevance=fields["relevance"] or None,
        source=source,
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    return CardExtractOut(card=_card_out(card), warning=warning)


# ═══════════════════════ 手工创建 / 查询 / 修改 / 删除 ═══════════════════════

@router.post(
    "/projects/{project_id}/cards",
    response_model=CardOut,
    status_code=status.HTTP_201_CREATED,
)
def create_card(project_id: int, data: CardCreate, db: Session = Depends(get_db)):
    """手工创建研究卡片（不经过 AI，字段可全部留空）。"""
    if db.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    if data.document_id is not None:
        document = db.get(Document, data.document_id)
        if document is None or document.project_id != project_id:
            raise HTTPException(status_code=400, detail="文献不存在或不属于该项目")
    if data.question_id is not None:
        question = db.get(ResearchQuestion, data.question_id)
        if question is None or question.project_id != project_id:
            raise HTTPException(status_code=400, detail="研究问题不存在或不属于该项目")

    card = LiteratureCard(
        project_id=project_id,
        document_id=data.document_id,
        question_id=data.question_id,
        title=data.title,
        authors=data.authors,
        year=data.year,
        research_question=data.research_question,
        method=data.method,
        materials_datasets=data.materials_datasets,
        metrics=data.metrics,
        key_results=data.key_results,
        innovations=data.innovations,
        limitations=data.limitations,
        relevance=data.relevance,
        evidence_type=data.evidence_type,
        evidence_snippets_json=json.dumps(
            [s.model_dump() for s in (data.evidence_snippets or [])],
            ensure_ascii=False,
        ),
        source="manual",
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    return _card_out(card)


@router.get("/documents/{document_id}/card", response_model=CardOut)
def get_document_card(document_id: int, db: Session = Depends(get_db)):
    """该文献的研究卡片（不存在 → 404）。"""
    if db.get(Document, document_id) is None:
        raise HTTPException(status_code=404, detail="文献不存在")
    card = db.scalar(
        select(LiteratureCard).where(LiteratureCard.document_id == document_id)
    )
    if card is None:
        raise HTTPException(status_code=404, detail="该文献还没有研究卡片")
    return _card_out(card)


@router.get("/projects/{project_id}/cards", response_model=list[CardOut])
def list_cards(
    project_id: int,
    question_id: int | None = None,
    evidence_type: str | None = None,
    db: Session = Depends(get_db),
):
    """项目下的卡片列表（可按研究问题、证据立场筛选；新卡片在前）。"""
    if db.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    stmt = select(LiteratureCard).where(LiteratureCard.project_id == project_id)
    if question_id is not None:
        stmt = stmt.where(LiteratureCard.question_id == question_id)
    if evidence_type is not None:
        stmt = stmt.where(LiteratureCard.evidence_type == evidence_type)
    stmt = stmt.order_by(LiteratureCard.created_at.desc())
    return [_card_out(c) for c in db.scalars(stmt).all()]


@router.get("/projects/{project_id}/cards/compare", response_model=CardCompareOut)
def compare_cards(
    project_id: int,
    card_ids: str,
    db: Session = Depends(get_db),
):
    """多卡片对比：card_ids 为逗号分隔的 id 列表（如 1,2,3），按传入顺序返回。"""
    if db.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    ids: list[int] = []
    for part in card_ids.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ids.append(int(part))
        except ValueError:
            raise HTTPException(status_code=400, detail="card_ids 必须是逗号分隔的数字")
    if not 2 <= len(ids) <= 8:
        raise HTTPException(status_code=400, detail="请选择 2~8 张卡片进行对比")
    ids = list(dict.fromkeys(ids))  # 去重保序

    cards = []
    for card_id in ids:
        card = db.get(LiteratureCard, card_id)
        if card is None or card.project_id != project_id:
            raise HTTPException(status_code=400, detail=f"卡片 {card_id} 不存在或不属于该项目")
        cards.append(_card_out(card))
    return CardCompareOut(cards=cards)


@router.put("/cards/{card_id}", response_model=CardOut)
def update_card(card_id: int, data: CardUpdate, db: Session = Depends(get_db)):
    """人工修改卡片字段；任何修改后 source 置为 manual（代表已人工确认）。"""
    card = _get_card_or_404(db, card_id)
    if data.question_id is not None:
        question = db.get(ResearchQuestion, data.question_id)
        if question is None or question.project_id != card.project_id:
            raise HTTPException(status_code=400, detail="研究问题不存在或不属于该项目")
    payload = data.model_dump(exclude_unset=True)
    if "evidence_snippets" in payload:
        snippets = payload.pop("evidence_snippets")
        if snippets is not None:
            # model_dump 后的片段已是可 JSON 序列化的 dict 列表
            card.evidence_snippets_json = json.dumps(snippets, ensure_ascii=False)
    for field, value in payload.items():
        setattr(card, field, value)
    card.source = "manual"
    db.commit()
    db.refresh(card)
    return _card_out(card)


@router.delete("/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(card_id: int, db: Session = Depends(get_db)):
    """删除研究卡片（不影响文献本体）。"""
    card = _get_card_or_404(db, card_id)
    db.delete(card)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
