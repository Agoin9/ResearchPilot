"""周报接口：近 7 天活动聚合 + AI 周报正文（DeepSeek，无 Key 时模板降级）。"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai_client import DeepSeekError
from app.database import get_db
from app.schemas import AiWeeklyReportOut, WeeklyReportOut
from app.services.report import generate_weekly_report, get_weekly_report

router = APIRouter(prefix="/report", tags=["周报"])


@router.get("/weekly", response_model=WeeklyReportOut)
def weekly_data(db: Session = Depends(get_db)):
    """近 7 天科研活动聚合（纯本地统计，不依赖 AI）。"""
    return get_weekly_report(db, date.today())


@router.post("/weekly/generate", response_model=AiWeeklyReportOut)
def weekly_generate(db: Session = Depends(get_db)):
    """生成 AI 周报正文：后端自动收集本周数据交给 DeepSeek。

    无 Key → 模板周报（source=demo）；AI 超时/失败 → 502 + 友好提示。
    """
    try:
        source, content = generate_weekly_report(db, date.today())
    except DeepSeekError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return AiWeeklyReportOut(source=source, content=content)
