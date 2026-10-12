"""文献库接口（文献精读与引用溯源助手）：

上传 PDF → 提取文字 + 切块；对文献提问 → 关键词取 top5 片段 → DeepSeek
只依据片段回答并返回引用；答案可保存为笔记。Key 只在本后端使用。
"""
import json
from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai_client import DeepSeekError
from app.database import get_db
from app.models import DocChunk, DocQa, Document, Project
from app.schemas import (
    CitationOut,
    DocChunkOut,
    DocumentDetailOut,
    DocumentOut,
    QaCreate,
    QaOut,
)
from app.services.document_service import (
    DocumentServiceError,
    answer_question,
    chunk_text,
    extract_pdf_text,
)

router = APIRouter(tags=["文献库"])


def _get_project_or_404(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


def _get_document_or_404(db: Session, document_id: int) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="文献不存在")
    return document


def _qa_out(qa: DocQa) -> QaOut:
    try:
        citations = [CitationOut(**c) for c in json.loads(qa.citations_json or "[]")]
    except (ValueError, TypeError):
        citations = []
    return QaOut(
        id=qa.id,
        document_id=qa.document_id,
        project_id=qa.project_id,
        question=qa.question,
        answer=qa.answer,
        citations=citations,
        confidence=qa.confidence,
        source=qa.source,
        is_saved=bool(qa.is_saved),
        created_at=qa.created_at,
    )


@router.post(
    "/projects/{project_id}/documents",
    response_model=DocumentOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    project_id: int,
    file: UploadFile = File(...),
    title: str | None = Form(None),
    db: Session = Depends(get_db),
):
    """上传 PDF：提取文字并按 500~800 字切块保存。

    扫描版 PDF（无文字层）返回 400 + 明确提示。
    """
    _get_project_or_404(db, project_id)
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="只支持上传 PDF 文件")

    data = await file.read()
    try:
        full_text, scanned = extract_pdf_text(data)
    except DocumentServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if scanned:
        raise HTTPException(
            status_code=400,
            detail="该 PDF 可能是扫描版（没有文字层），暂不支持；请上传含文字的 PDF",
        )

    document = Document(
        project_id=project_id,
        title=(title or "").strip() or (file.filename or "未命名文献").rsplit(".", 1)[0],
        file_name=file.filename or "document.pdf",
        full_text=full_text,
    )
    db.add(document)
    db.flush()
    chunks = chunk_text(full_text)
    for index, content in enumerate(chunks, start=1):
        db.add(DocChunk(document_id=document.id, chunk_index=index, content=content))
    document.chunk_count = len(chunks)
    db.commit()
    db.refresh(document)
    return DocumentOut.model_validate(document)


@router.get("/projects/{project_id}/documents", response_model=list[DocumentOut])
def list_documents(project_id: int, db: Session = Depends(get_db)):
    """项目下的文献列表（新上传在前）。"""
    _get_project_or_404(db, project_id)
    documents = db.scalars(
        select(Document)
        .where(Document.project_id == project_id)
        .order_by(Document.created_at.desc())
    ).all()
    return [DocumentOut.model_validate(d) for d in documents]


@router.get("/documents/{document_id}", response_model=DocumentDetailOut)
def get_document(document_id: int, db: Session = Depends(get_db)):
    """文献详情：全文 + 全部切片（点击来源看原文用）。"""
    document = _get_document_or_404(db, document_id)
    chunks = db.scalars(
        select(DocChunk)
        .where(DocChunk.document_id == document_id)
        .order_by(DocChunk.chunk_index)
    ).all()
    return DocumentDetailOut(
        id=document.id,
        project_id=document.project_id,
        title=document.title,
        file_name=document.file_name,
        chunk_count=document.chunk_count,
        created_at=document.created_at,
        full_text=document.full_text,
        chunks=[DocChunkOut.model_validate(c) for c in chunks],
    )


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: int, db: Session = Depends(get_db)):
    """删除文献（级联删除其切片与问答记录）。"""
    document = _get_document_or_404(db, document_id)
    db.delete(document)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/documents/{document_id}/qa", response_model=QaOut)
def ask_document(document_id: int, data: QaCreate, db: Session = Depends(get_db)):
    """对文献提问：关键词检索 top5 片段 → DeepSeek 只依据片段回答（带引用）。

    无 Key → 演示模式（source=demo）；AI 失败 → 502 + 友好提示。
    """
    document = _get_document_or_404(db, document_id)
    chunks = db.scalars(
        select(DocChunk)
        .where(DocChunk.document_id == document_id)
        .order_by(DocChunk.chunk_index)
    ).all()
    if not chunks:
        raise HTTPException(status_code=400, detail="该文献没有可检索的文字内容")

    try:
        answer, citations, confidence, source = answer_question(data.question, chunks)
    except DeepSeekError as e:
        raise HTTPException(status_code=502, detail=str(e))

    qa = DocQa(
        project_id=document.project_id,
        document_id=document_id,
        question=data.question,
        answer=answer,
        citations_json=json.dumps([c.model_dump() for c in citations], ensure_ascii=False),
        confidence=confidence,
        source=source,
    )
    db.add(qa)
    db.commit()
    db.refresh(qa)
    return _qa_out(qa)


@router.get("/documents/{document_id}/qa", response_model=list[QaOut])
def list_document_qa(document_id: int, db: Session = Depends(get_db)):
    """该文献的问答历史（最新在前）。"""
    _get_document_or_404(db, document_id)
    qas = db.scalars(
        select(DocQa)
        .where(DocQa.document_id == document_id)
        .order_by(DocQa.created_at.desc())
    ).all()
    return [_qa_out(q) for q in qas]


@router.post("/qa/{qa_id}/save-note", response_model=QaOut)
def save_note(qa_id: int, db: Session = Depends(get_db)):
    """把问答结果保存为笔记（重复调用幂等）。"""
    qa = db.get(DocQa, qa_id)
    if qa is None:
        raise HTTPException(status_code=404, detail="问答记录不存在")
    qa.is_saved = True
    db.commit()
    db.refresh(qa)
    return _qa_out(qa)


@router.get("/projects/{project_id}/notes", response_model=list[QaOut])
def list_project_notes(project_id: int, db: Session = Depends(get_db)):
    """项目下已保存的笔记（最新在前）。"""
    _get_project_or_404(db, project_id)
    qas = db.scalars(
        select(DocQa)
        .where(DocQa.project_id == project_id, DocQa.is_saved.is_(True))
        .order_by(DocQa.created_at.desc())
    ).all()
    return [_qa_out(q) for q in qas]
