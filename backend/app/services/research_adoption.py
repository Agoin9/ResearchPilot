"""科研建议采纳服务（v2.3）：把"科研决策"层与"执行计划"层打通。

分层原则（严格）：
- 科研决策层：AI 建议只是起点，用户确认（可先修改）后才生效；
- 执行计划层：采纳时创建 Experiment（科研载体）+ Task（执行载体），
  Task 关联实验 id / 研究问题 id / 计划日期 / 预计工时 / 依赖关系；
- 风险引擎只按任务执行进度计算风险（逾期/阻塞/落后/工时不足），
  不参与任何科研结论的生成；
- 动态重规划只调整任务执行安排（日期/优先级/工时），不触碰实验假设与结果。

所有采纳 / 拒绝 / 修改操作写入 research_action_log 历史。
"""
import json
from datetime import date

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Experiment,
    ResearchActionLog,
    ResearchAnalysis,
    Task,
)

ADOPTED = "adopted"
REJECTED = "rejected"
MODIFIED = "modified"


def _suggestions_of(analysis: ResearchAnalysis) -> list[dict]:
    return json.loads(analysis.next_experiments_json or "[]")


def _to_date(value) -> date:
    """归一化日期：兼容 date 对象与 ISO 字符串两种入参。"""
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _save_suggestions(db: Session, analysis: ResearchAnalysis, suggestions: list[dict]) -> None:
    analysis.next_experiments_json = json.dumps(suggestions, ensure_ascii=False)
    db.commit()


def _log(
    db: Session,
    analysis: ResearchAnalysis,
    index: int,
    action: str,
    payload: dict,
    task_id: int | None = None,
    experiment_id: int | None = None,
) -> ResearchActionLog:
    log = ResearchActionLog(
        project_id=analysis.project_id,
        analysis_id=analysis.id,
        suggestion_index=index,
        action=action,
        # default=str：兼容 payload 中含 date 等非 JSON 原生类型的调用方
        payload_json=json.dumps(payload, ensure_ascii=False, default=str),
        task_id=task_id,
        experiment_id=experiment_id,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def _validate_dependencies(
    db: Session, project_id: int, dependencies: list[int]
) -> list[int]:
    """校验依赖任务：必须存在、属于同一项目；返回清理后的列表。"""
    if not dependencies:
        return []
    tasks = db.scalars(select(Task).where(Task.id.in_(dependencies))).all()
    found = {t.id for t in tasks}
    missing = [dep for dep in dependencies if dep not in found]
    if missing:
        raise HTTPException(status_code=400, detail=f"依赖任务不存在：{missing}")
    foreign = [t.id for t in tasks if t.project_id != project_id]
    if foreign:
        raise HTTPException(status_code=400, detail=f"依赖任务不属于该项目：{foreign}")
    return dependencies


def adopt_suggestion(
    db: Session,
    analysis: ResearchAnalysis,
    suggestion_index: int,
    payload: dict,
    today: date,
) -> tuple[Experiment, Task, ResearchActionLog]:
    """用户确认采纳：原子创建 Experiment + 关联 Task，并写入历史。

    前置检查：建议存在、未被转换、未被拒绝。
    创建内容：
    - Experiment：objective/hypothesis/variables + design（含所需数据/前置条件/来源），
      状态 draft（设计待用户补充方案细节）；
    - Task：计划日期/预计工时/依赖（parent_id 取首个依赖以复用风险引擎的
      前置阻塞规则，全部依赖存入 dependencies_json），
      source_type=research_analysis，experiment_id / question_id 关联。
    """
    suggestions = _suggestions_of(analysis)
    if not 0 <= suggestion_index < len(suggestions):
        raise HTTPException(status_code=404, detail="建议不存在")
    suggestion = suggestions[suggestion_index]
    if suggestion.get("converted"):
        raise HTTPException(status_code=400, detail="该建议已采纳过，不能重复采纳")
    if suggestion.get("rejected"):
        raise HTTPException(status_code=400, detail="该建议已被拒绝，不能采纳")

    dependencies = _validate_dependencies(
        db, analysis.project_id, payload.get("dependencies") or []
    )

    design_parts = []
    if payload.get("required_data"):
        design_parts.append(f"所需数据：{payload['required_data']}")
    if payload.get("preconditions"):
        design_parts.append(f"前置条件：{payload['preconditions']}")
    design_parts.append(
        f"来源：研究分析 #{analysis.id} 的建议 #{suggestion_index + 1}"
    )
    experiment = Experiment(
        project_id=analysis.project_id,
        question_id=analysis.question_id,
        title=f"实验：{payload['objective'][:180]}",
        objective=payload["objective"],
        hypothesis=payload["hypothesis"],
        variables=payload.get("variables"),
        design="\n".join(design_parts) or None,
        status="draft",
    )
    db.add(experiment)
    db.flush()

    description_parts = [
        f"实验目的：{payload['objective']}",
        f"研究假设：{payload['hypothesis']}",
    ]
    if payload.get("variables"):
        description_parts.append(f"实验变量：{payload['variables']}")
    if payload.get("required_data"):
        description_parts.append(f"所需数据：{payload['required_data']}")
    if payload.get("preconditions"):
        description_parts.append(f"前置条件：{payload['preconditions']}")
    if dependencies:
        dep_titles = []
        dep_tasks = db.scalars(select(Task).where(Task.id.in_(dependencies))).all()
        title_map = {t.id: t.title for t in dep_tasks}
        dep_titles = [f"#{dep} {title_map.get(dep, '')}" for dep in dependencies]
        description_parts.append(f"依赖任务：{'、'.join(dep_titles)}")
    description_parts.append(f"来源：研究分析 #{analysis.id}（实验 #{experiment.id}）")

    # parent_id 取第一个依赖：复用风险引擎"前置任务阻塞"规则
    parent_id = dependencies[0] if dependencies else None
    task = Task(
        project_id=analysis.project_id,
        title=f"实验执行：{payload['objective'][:150]}",
        description="\n".join(description_parts),
        status="todo",
        priority="medium",
        planned_start_date=_to_date(payload["planned_start_date"]),
        planned_end_date=_to_date(payload["planned_end_date"]),
        estimated_hours=payload["estimated_hours"],
        parent_id=parent_id,
        source_type="research_analysis",
        source_id=analysis.id,
        experiment_id=experiment.id,
        question_id=analysis.question_id,
        dependencies_json=json.dumps(dependencies, ensure_ascii=False),
    )
    db.add(task)

    suggestion["converted"] = True
    suggestions[suggestion_index] = suggestion
    _save_suggestions(db, analysis, suggestions)

    log = _log(
        db,
        analysis,
        suggestion_index,
        ADOPTED,
        payload=dict(payload),
        task_id=task.id,
        experiment_id=experiment.id,
    )
    db.refresh(task)
    return experiment, task, log


def reject_suggestion(
    db: Session,
    analysis: ResearchAnalysis,
    suggestion_index: int,
    reason: str | None,
) -> tuple[dict, ResearchActionLog]:
    """用户拒绝建议：标记 rejected 并写入历史（不创建任何实验/任务）。"""
    suggestions = _suggestions_of(analysis)
    if not 0 <= suggestion_index < len(suggestions):
        raise HTTPException(status_code=404, detail="建议不存在")
    suggestion = suggestions[suggestion_index]
    if suggestion.get("converted"):
        raise HTTPException(status_code=400, detail="该建议已采纳过，不能拒绝")
    if suggestion.get("rejected"):
        raise HTTPException(status_code=400, detail="该建议已被拒绝过")

    suggestion["rejected"] = True
    if reason:
        suggestion["reject_reason"] = reason
    suggestions[suggestion_index] = suggestion
    _save_suggestions(db, analysis, suggestions)

    log = _log(
        db,
        analysis,
        suggestion_index,
        REJECTED,
        payload={"reason": reason or "", "suggestion": suggestion},
    )
    return suggestion, log


def modify_suggestion(
    db: Session,
    analysis: ResearchAnalysis,
    suggestion_index: int,
    fields: dict,
) -> tuple[dict, ResearchActionLog]:
    """用户修改建议（不采纳）：保存修改并留档。"""
    suggestions = _suggestions_of(analysis)
    if not 0 <= suggestion_index < len(suggestions):
        raise HTTPException(status_code=404, detail="建议不存在")
    suggestion = suggestions[suggestion_index]
    if suggestion.get("converted") or suggestion.get("rejected"):
        raise HTTPException(status_code=400, detail="该建议已处理，不能修改")

    changes = {}
    for key, value in fields.items():
        if value is None:
            continue
        changes[key] = value
    if not changes:
        raise HTTPException(status_code=400, detail="没有需要保存的修改")

    suggestion.update(changes)
    suggestions[suggestion_index] = suggestion
    _save_suggestions(db, analysis, suggestions)

    log = _log(
        db,
        analysis,
        suggestion_index,
        MODIFIED,
        payload={"changes": changes, "suggestion": suggestion},
    )
    return suggestion, log
