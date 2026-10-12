"""AI 科研计划接口（PRD §7.3）：

POST /api/ai/plan         生成计划草稿（只返回预览，不写数据库）
POST /api/ai/plan/confirm 用户确认后原子写入项目 + 任务

密钥只存在于后端 .env，接口响应中不包含任何密钥信息。
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai_client import DeepSeekError
from app.database import get_db
from app.models import Project, Task
from app.schemas import (
    AiPlanConfirmOut,
    AiPlanConfirmRequest,
    AiPlanOut,
    AiPlanRequest,
)
from app.services.ai_planner import PRIORITY_LABELS, generate_plan, validate_and_normalize
from app.services.serializers import build_project_summary, build_task_out

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/plan", response_model=AiPlanOut)
def create_plan(data: AiPlanRequest):
    """生成科研计划草稿：调用 DeepSeek（无 Key 时演示模式），返回预览任务列表。

    - 输入校验失败 → 422（中文提示）
    - DeepSeek 超时/网络/Key 无效/余额不足/限流等 → 502 + 友好提示
    - 格式错误自动重试 2 次，仍失败 → 502 + 友好提示
    """
    try:
        source, tasks, warning = generate_plan(
            topic=data.topic,
            deadline=data.deadline,
            weekly_hours=data.weekly_hours,
            current_stage=data.current_stage,
            completed_work=data.completed_work or "",
            today=date.today(),
        )
    except DeepSeekError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return AiPlanOut(source=source, tasks=tasks, warning=warning)


@router.post("/plan/confirm", response_model=AiPlanConfirmOut)
def confirm_plan(data: AiPlanConfirmRequest, db: Session = Depends(get_db)):
    """确认计划：用户点「确认」时才写入数据库（项目 + 任务原子创建）。

    任务会在服务端重新校验（标题/日期/优先级/耗时），日期必须落在项目截止日期内。
    """
    # 服务端重新校验任务（不信任前端回传内容）
    try:
        tasks = validate_and_normalize(
            [t.model_dump() for t in data.tasks], data.project.deadline, date.today()
        )
    except Exception as e:  # PlanFormatError → 入参不合法
        raise HTTPException(status_code=422, detail=f"任务列表校验失败：{e}")

    # 创建项目
    project = Project(
        name=data.project.name,
        goal=data.project.goal,
        deadline=data.project.deadline,
        weekly_hours=data.project.weekly_hours,
    )
    db.add(project)
    db.flush()  # 拿到 project.id

    # 创建任务（先全部落库，再回填 parent_id 依赖）
    priority_map = {label: key for key, label in PRIORITY_LABELS.items()}
    created: dict[str, Task] = {}
    for index, task in enumerate(tasks):
        row = Task(
            project_id=project.id,
            title=task.title,
            description="\n\n".join(
                part
                for part in (
                    task.description,
                    f"预期产出：{task.expected_deliverable}" if task.expected_deliverable else "",
                    f"安排理由：{task.rationale}" if task.rationale else "",
                )
                if part
            )
            or None,
            status="todo",
            priority=priority_map.get(task.priority, "medium"),
            planned_start_date=task.start_date,
            planned_end_date=task.due_date,
            estimated_hours=task.estimated_hours,
            progress=0,
            is_milestone=False,
            sort_order=index,
        )
        db.add(row)
        created[task.task_id] = row
    db.flush()

    # 依赖 → parent_id（取第一个存在的前置任务作为父任务，未知引用忽略）
    for task in tasks:
        row = created[task.task_id]
        for dep_id in task.dependencies:
            dep = created.get(dep_id)
            if dep is not None and dep.id != row.id:
                row.parent_id = dep.id
                break

    db.commit()
    db.refresh(project)
    rows = [created[t.task_id] for t in tasks]
    for row in rows:
        db.refresh(row)
    return AiPlanConfirmOut(
        project=build_project_summary(project, rows),
        tasks=[build_task_out(r) for r in rows],
    )
