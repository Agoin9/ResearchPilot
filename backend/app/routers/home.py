"""首页聚合接口：一次请求返回仪表盘所需的全部数据。"""
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import HomeOut
from app.services.home import get_home

router = APIRouter(tags=["首页"])


@router.get("/home", response_model=HomeOut)
def home_data(db: Session = Depends(get_db)):
    """首页聚合数据：统计卡片 + 项目列表 + 风险任务 + 趋势图 + 状态分布。"""
    return get_home(db, date.today())
