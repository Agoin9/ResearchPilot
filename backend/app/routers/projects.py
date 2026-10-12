"""项目 CRUD 接口（PRD §7.1）：创建 / 查询 / 修改 / 删除。"""
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project, Task
from app.schemas import ProjectCreate, ProjectDetailOut, ProjectSummary, ProjectUpdate
from app.services.serializers import build_project_summary, build_task_out

router = APIRouter(prefix="/projects", tags=["项目"])


def _get_project_or_404(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


def _project_tasks(db: Session, project_id: int) -> list[Task]:
    return list(
        db.scalars(
            select(Task)
            .where(Task.project_id == project_id)
            .order_by(Task.sort_order, Task.id)
        )
    )


@router.get("", response_model=list[ProjectSummary])
def list_projects(db: Session = Depends(get_db)):
    """项目列表（含整体进度、任务数、风险等级、剩余天数）。"""
    projects = db.scalars(
        select(Project).order_by(Project.created_at.desc())
    ).all()
    all_tasks = db.scalars(select(Task)).all()
    tasks_by_project: dict[int, list[Task]] = {}
    for task in all_tasks:
        tasks_by_project.setdefault(task.project_id, []).append(task)
    return [
        build_project_summary(p, tasks_by_project.get(p.id, []))
        for p in projects
    ]


@router.post("", response_model=ProjectSummary, status_code=status.HTTP_201_CREATED)
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    """创建项目。"""
    project = Project(
        name=data.name,
        goal=data.goal,
        deadline=data.deadline,
        weekly_hours=data.weekly_hours,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return build_project_summary(project, [])


@router.get("/{project_id}", response_model=ProjectDetailOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    """项目详情：项目信息 + 任务树（每个任务附带风险标记）。"""
    project = _get_project_or_404(db, project_id)
    tasks = _project_tasks(db, project_id)
    return ProjectDetailOut(
        project=build_project_summary(project, tasks),
        tasks=[build_task_out(t) for t in tasks],
    )


@router.put("/{project_id}", response_model=ProjectSummary)
def update_project(
    project_id: int, data: ProjectUpdate, db: Session = Depends(get_db)
):
    """更新项目：只更新提交的字段。"""
    project = _get_project_or_404(db, project_id)
    payload = data.model_dump(exclude_unset=True)
    for field, value in payload.items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return build_project_summary(project, _project_tasks(db, project_id))


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """删除项目（级联删除其任务、进度记录、重规划历史）。"""
    project = _get_project_or_404(db, project_id)
    db.delete(project)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
