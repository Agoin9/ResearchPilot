"""任务与进度记录接口（PRD §7.2）：新增 / 编辑 / 标记完成 / 删除 / 进度记录。"""
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ProgressRecord, Project, Task
from app.schemas import (
    ProgressCreate,
    ProgressRecordOut,
    ProgressUpdateOut,
    TaskCreate,
    TaskOut,
    TaskUpdate,
)
from app.services.serializers import build_task_out

router = APIRouter(prefix="/tasks", tags=["任务"])

# 不可为空的字段：显式传 null 视为"不修改"（防止把非空字段写成 NULL）
NON_NULLABLE_FIELDS = {"title", "status", "priority", "progress", "is_milestone", "sort_order"}


def _get_task_or_404(db: Session, task_id: int) -> Task:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


def _check_parent(db: Session, parent_id: int, project_id: int) -> None:
    """校验父任务：必须存在，且与任务属于同一项目。"""
    parent = db.get(Task, parent_id)
    if parent is None:
        raise HTTPException(status_code=404, detail="父任务不存在")
    if parent.project_id != project_id:
        raise HTTPException(status_code=400, detail="父任务必须与任务属于同一项目")


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(data: TaskCreate, db: Session = Depends(get_db)):
    """手动创建任务（可挂在某个里程碑 parent_id 下）。"""
    if db.get(Project, data.project_id) is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    if data.parent_id is not None:
        _check_parent(db, data.parent_id, data.project_id)

    task = Task(
        project_id=data.project_id,
        parent_id=data.parent_id,
        title=data.title,
        description=data.description,
        status=data.status,
        priority=data.priority,
        planned_start_date=data.planned_start_date,
        planned_end_date=data.planned_end_date,
        estimated_hours=data.estimated_hours,
        is_milestone=data.is_milestone,
        sort_order=data.sort_order,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return build_task_out(task)


@router.put("/{task_id}", response_model=TaskOut)
def update_task(task_id: int, data: TaskUpdate, db: Session = Depends(get_db)):
    """更新任务（改状态/日期/优先级/标题等）。

    约定：status=done 时进度自动置 100；progress=100 时自动标记完成。
    """
    task = _get_task_or_404(db, task_id)
    payload = data.model_dump(exclude_unset=True)

    if "parent_id" in payload:
        if payload["parent_id"] is not None:
            _check_parent(db, payload["parent_id"], task.project_id)
        task.parent_id = payload["parent_id"]

    for field, value in payload.items():
        if field == "parent_id":
            continue
        if field in NON_NULLABLE_FIELDS and value is None:
            continue  # 非空字段显式传 null → 视为不修改
        setattr(task, field, value)

    # 合并后的日期合法性
    if (
        task.planned_start_date
        and task.planned_end_date
        and task.planned_end_date < task.planned_start_date
    ):
        raise HTTPException(status_code=400, detail="计划截止日期不能早于计划开始日期")

    # 状态 ↔ 进度 联动：标记完成 → 进度 100；进度 100 → 完成；已完成任务回退进度 → 回到进行中
    status_was_set = "status" in payload and payload["status"] is not None
    progress_was_set = "progress" in payload and payload["progress"] is not None
    if status_was_set and task.status == "done":
        task.progress = 100
    elif progress_was_set:
        if task.progress == 100:
            task.status = "done"
        elif task.status == "done":
            task.status = "doing"

    db.commit()
    db.refresh(task)
    return build_task_out(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """删除任务（级联删除其进度记录和子任务）。"""
    task = _get_task_or_404(db, task_id)
    db.delete(task)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{task_id}/progress", response_model=ProgressUpdateOut)
def add_progress(task_id: int, data: ProgressCreate, db: Session = Depends(get_db)):
    """新增进度记录：写入 progress_record，并同步 task.progress。"""
    task = _get_task_or_404(db, task_id)
    record = ProgressRecord(
        task_id=task_id,
        progress=data.progress,
        hours_spent=data.hours_spent,
        note=data.note,
    )
    task.progress = data.progress
    if data.progress == 100:
        task.status = "done"
    elif task.status == "done":
        task.status = "doing"  # 已完成任务回退进度 → 回到进行中
    db.add(record)
    db.commit()
    db.refresh(record)
    db.refresh(task)
    return ProgressUpdateOut(
        record=ProgressRecordOut.model_validate(record),
        task=build_task_out(task),
    )


@router.get("/{task_id}/progress", response_model=list[ProgressRecordOut])
def list_progress(task_id: int, db: Session = Depends(get_db)):
    """进度记录列表（时间升序，画进度曲线用）。"""
    _get_task_or_404(db, task_id)
    records = db.scalars(
        select(ProgressRecord)
        .where(ProgressRecord.task_id == task_id)
        .order_by(ProgressRecord.created_at)
    ).all()
    return [ProgressRecordOut.model_validate(r) for r in records]
