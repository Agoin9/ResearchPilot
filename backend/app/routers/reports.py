"""组会周报与导师汇报接口：生成 / 查询 / 编辑 / 导出 Markdown。

生成时从数据库读取项目、任务、进度记录、风险（实时计算）、重规划历史，
组装成 JSON 交给 DeepSeek；无 Key 时进入演示模式（模板生成，明确标记）。
"""
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai_client import DeepSeekError
from app.database import get_db
from app.models import Project, Report
from app.schemas import ReportCreate, ReportOut, ReportUpdate
from app.services.meeting_report import DEFAULT_RANGE_DAYS, generate_report

router = APIRouter(tags=["汇报中心"])


def _get_project_or_404(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


def _get_report_or_404(db: Session, report_id: int) -> Report:
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="汇报不存在")
    return report


@router.post("/projects/{project_id}/reports", response_model=ReportOut)
def create_report(project_id: int, data: ReportCreate, db: Session = Depends(get_db)):
    """生成汇报：默认时间范围为近 7 天。AI 失败 → 502 + 友好提示。"""
    project = _get_project_or_404(db, project_id)
    today = date.today()
    week_end = data.week_end or today
    week_start = data.week_start or (week_end - timedelta(days=DEFAULT_RANGE_DAYS - 1))

    try:
        title, content, source = generate_report(
            db, project, data.report_type, week_start, week_end, today
        )
    except DeepSeekError as e:
        raise HTTPException(status_code=502, detail=str(e))

    report = Report(
        project_id=project_id,
        title=title,
        report_type=data.report_type,
        week_start=week_start,
        week_end=week_end,
        content=content,
        source=source,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return ReportOut.model_validate(report)


@router.get("/projects/{project_id}/reports", response_model=list[ReportOut])
def list_reports(project_id: int, db: Session = Depends(get_db)):
    """该项目汇报历史（最新在前）。"""
    _get_project_or_404(db, project_id)
    reports = db.scalars(
        select(Report)
        .where(Report.project_id == project_id)
        .order_by(Report.created_at.desc())
    ).all()
    return [ReportOut.model_validate(r) for r in reports]


@router.get("/reports/{report_id}", response_model=ReportOut)
def get_report(report_id: int, db: Session = Depends(get_db)):
    """汇报详情。"""
    return ReportOut.model_validate(_get_report_or_404(db, report_id))


@router.put("/reports/{report_id}", response_model=ReportOut)
def update_report(report_id: int, data: ReportUpdate, db: Session = Depends(get_db)):
    """编辑后保存汇报正文。"""
    report = _get_report_or_404(db, report_id)
    report.content = data.content
    db.commit()
    db.refresh(report)
    return ReportOut.model_validate(report)


@router.get("/reports/{report_id}/export")
def export_report(report_id: int, db: Session = Depends(get_db)):
    """导出为 .md 文件（浏览器直接下载）。"""
    report = _get_report_or_404(db, report_id)
    return Response(
        content=report.content.encode("utf-8"),
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="report-{report.id}.md"'
        },
    )
