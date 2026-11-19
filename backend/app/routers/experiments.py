"""实验管理接口（v2 核心模块）：

- 实验 CRUD（目标/假设/方案/指标定义/状态）；
- 实验运行记录 CRUD（条件/结构化结果/备注/附件图片，真实数据人工录入，
  不集成训练执行平台）；
- 同实验 run 对比（指标对齐）与跨实验指标总览（本地计算，不调 AI）。
"""
import json
import uuid
from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import UPLOAD_DIR
from app.database import get_db
from app.models import Experiment, ExperimentRun, Project, ResearchQuestion
from app.schemas import (
    CompareRow,
    ExperimentCompareOut,
    ExperimentCreate,
    ExperimentDetailOut,
    ExperimentOut,
    ExperimentUpdate,
    MetricDef,
    MetricOverviewItem,
    MetricPoint,
    MetricsOverviewOut,
    RunCreate,
    RunOut,
    RunUpdate,
)
from app.services.risk import EXPERIMENT_STALL_DAYS

router = APIRouter(tags=["实验"])

MAX_ATTACHMENTS_PER_RUN = 3
MAX_ATTACHMENT_BYTES = 5 * 1024 * 1024  # 5MB
ALLOWED_ATTACHMENT_TYPES = {"image/png", "image/jpeg"}


def _get_project_or_404(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


def _get_experiment_or_404(db: Session, experiment_id: int) -> Experiment:
    experiment = db.get(Experiment, experiment_id)
    if experiment is None:
        raise HTTPException(status_code=404, detail="实验不存在")
    return experiment


def _get_run_or_404(db: Session, run_id: int) -> ExperimentRun:
    run = db.get(ExperimentRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="运行记录不存在")
    return run


def _load_json(text: str | None, default) -> object:
    try:
        return json.loads(text) if text else default
    except (ValueError, TypeError):
        return default


def _metrics_of(experiment: Experiment) -> list[MetricDef]:
    return [MetricDef(**m) for m in _load_json(experiment.metrics_json, [])]


def _runs_of(db: Session, experiment_id: int) -> list[ExperimentRun]:
    return list(
        db.scalars(
            select(ExperimentRun)
            .where(ExperimentRun.experiment_id == experiment_id)
            .order_by(ExperimentRun.run_no)
        )
    )


def _experiment_out(
    db: Session, experiment: Experiment, runs: list[ExperimentRun] | None = None
) -> ExperimentOut:
    if runs is None:
        runs = _runs_of(db, experiment.id)
    last_run_at = max((r.created_at for r in runs), default=None)
    return ExperimentOut(
        id=experiment.id,
        project_id=experiment.project_id,
        question_id=experiment.question_id,
        title=experiment.title,
        objective=experiment.objective,
        hypothesis=experiment.hypothesis,
        variables=experiment.variables,
        control_conditions=experiment.control_conditions,
        dataset=experiment.dataset,
        model=experiment.model,
        design=experiment.design,
        config=_load_json(experiment.config_json, {}),
        metrics=_metrics_of(experiment),
        status=experiment.status,
        run_count=len(runs),
        last_run_at=last_run_at,
        stalled=False,  # 列表/详情接口另行计算（见 _is_stalled）
        created_at=experiment.created_at,
        updated_at=experiment.updated_at,
    )


def _run_out(run: ExperimentRun) -> RunOut:
    return RunOut(
        id=run.id,
        experiment_id=run.experiment_id,
        run_no=run.run_no,
        config=_load_json(run.config_json, {}),
        results=_load_json(run.results_json, {}),
        random_seed=run.random_seed,
        git_commit=run.git_commit,
        environment=_load_json(run.environment_json, {}),
        log_path=run.log_path,
        result_files=_load_json(run.result_files_json, []),
        notes=run.notes,
        attachments=_load_json(run.attachments_json, []),
        started_at=run.started_at,
        finished_at=run.finished_at,
        created_at=run.created_at,
    )


# ═══════════════════════ 实验 CRUD ═══════════════════════

@router.get("/projects/{project_id}/experiments", response_model=list[ExperimentOut])
def list_experiments(project_id: int, db: Session = Depends(get_db)):
    """项目下的实验列表（最新在前，含 run 数与停滞标记）。"""
    _get_project_or_404(db, project_id)
    experiments = db.scalars(
        select(Experiment)
        .where(Experiment.project_id == project_id)
        .order_by(Experiment.created_at.desc())
    ).all()
    result: list[ExperimentOut] = []
    for experiment in experiments:
        runs = _runs_of(db, experiment.id)
        out = _experiment_out(db, experiment, runs)
        out.stalled = _is_stalled(experiment, runs)
        result.append(out)
    return result


def _is_stalled(experiment: Experiment, runs: list[ExperimentRun]) -> bool:
    """进行中/设计中的实验超过阈值天数无新运行记录 → 停滞。"""
    if experiment.status not in ("running", "draft"):
        return False
    last_run_at = max((r.created_at for r in runs), default=None)
    reference = last_run_at.date() if last_run_at else (
        experiment.created_at.date() if experiment.created_at else date.today()
    )
    return (date.today() - reference).days > EXPERIMENT_STALL_DAYS


@router.post(
    "/projects/{project_id}/experiments",
    response_model=ExperimentOut,
    status_code=status.HTTP_201_CREATED,
)
def create_experiment(project_id: int, data: ExperimentCreate, db: Session = Depends(get_db)):
    """创建实验（可关联研究问题；指标定义用于结果比较）。"""
    _get_project_or_404(db, project_id)
    if data.question_id is not None:
        question = db.get(ResearchQuestion, data.question_id)
        if question is None or question.project_id != project_id:
            raise HTTPException(status_code=400, detail="研究问题不存在或不属于该项目")

    experiment = Experiment(
        project_id=project_id,
        question_id=data.question_id,
        title=data.title,
        objective=data.objective,
        hypothesis=data.hypothesis,
        variables=data.variables,
        control_conditions=data.control_conditions,
        dataset=data.dataset,
        model=data.model,
        design=data.design,
        config_json=json.dumps(data.config or {}, ensure_ascii=False),
        metrics_json=json.dumps(
            [m.model_dump() for m in (data.metrics or [])], ensure_ascii=False
        ),
        status=data.status,
    )
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    return _experiment_out(db, experiment, [])


@router.get("/experiments/{experiment_id}", response_model=ExperimentDetailOut)
def get_experiment(experiment_id: int, db: Session = Depends(get_db)):
    """实验详情：实验信息 + 全部运行记录（时间升序）。"""
    experiment = _get_experiment_or_404(db, experiment_id)
    runs = _runs_of(db, experiment_id)
    out = _experiment_out(db, experiment, runs)
    out.stalled = _is_stalled(experiment, runs)
    return ExperimentDetailOut(experiment=out, runs=[_run_out(r) for r in runs])


@router.put("/experiments/{experiment_id}", response_model=ExperimentOut)
def update_experiment(experiment_id: int, data: ExperimentUpdate, db: Session = Depends(get_db)):
    """更新实验（改状态/方案/指标定义等）。"""
    experiment = _get_experiment_or_404(db, experiment_id)
    if data.question_id is not None:
        question = db.get(ResearchQuestion, data.question_id)
        if question is None or question.project_id != experiment.project_id:
            raise HTTPException(status_code=400, detail="研究问题不存在或不属于该项目")
    payload = data.model_dump(exclude_unset=True)
    if "metrics" in payload:
        payload["metrics_json"] = json.dumps(
            [m.model_dump() for m in (payload.pop("metrics") or [])], ensure_ascii=False
        )
    if "config" in payload:
        payload["config_json"] = json.dumps(payload.pop("config") or {}, ensure_ascii=False)
    for field, value in payload.items():
        setattr(experiment, field, value)
    db.commit()
    db.refresh(experiment)
    return _experiment_out(db, experiment)


@router.delete("/experiments/{experiment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_experiment(experiment_id: int, db: Session = Depends(get_db)):
    """删除实验（级联删除运行记录与磁盘附件）。"""
    experiment = _get_experiment_or_404(db, experiment_id)
    # 先清理磁盘附件，再删库（SQLite 级联删除运行记录）
    for run in _runs_of(db, experiment_id):
        for name in _load_json(run.attachments_json, []):
            path = UPLOAD_DIR / name
            if path.exists():
                path.unlink()
    db.delete(experiment)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ═══════════════════════ 运行记录 CRUD ═══════════════════════

@router.post(
    "/experiments/{experiment_id}/runs",
    response_model=RunOut,
    status_code=status.HTTP_201_CREATED,
)
def create_run(experiment_id: int, data: RunCreate, db: Session = Depends(get_db)):
    """新增运行记录（真实数据录入；run_no 同实验内自动递增）。"""
    experiment = _get_experiment_or_404(db, experiment_id)
    existing_runs = _runs_of(db, experiment_id)
    run_no = max((r.run_no for r in existing_runs), default=0) + 1
    run = ExperimentRun(
        experiment_id=experiment_id,
        run_no=run_no,
        random_seed=data.random_seed,
        git_commit=data.git_commit,
        environment_json=json.dumps(data.environment or {}, ensure_ascii=False),
        config_json=json.dumps(data.config or {}, ensure_ascii=False),
        results_json=json.dumps(data.results or {}, ensure_ascii=False),
        log_path=data.log_path,
        result_files_json=json.dumps(data.result_files or [], ensure_ascii=False),
        notes=data.notes,
        started_at=data.started_at,
        finished_at=data.finished_at,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return _run_out(run)


@router.get("/runs/{run_id}", response_model=RunOut)
def get_run(run_id: int, db: Session = Depends(get_db)):
    """运行记录详情。"""
    return _run_out(_get_run_or_404(db, run_id))


@router.put("/runs/{run_id}", response_model=RunOut)
def update_run(run_id: int, data: RunUpdate, db: Session = Depends(get_db)):
    """修改运行记录（改结果/备注/日期等）。"""
    run = _get_run_or_404(db, run_id)
    payload = data.model_dump(exclude_unset=True)
    for field in ("config", "results", "environment"):
        if field in payload and payload[field] is not None:
            setattr(run, f"{field}_json", json.dumps(payload.pop(field), ensure_ascii=False))
    if "result_files" in payload:
        value = payload.pop("result_files")
        if value is not None:
            run.result_files_json = json.dumps(value, ensure_ascii=False)
    for field, value in payload.items():
        setattr(run, field, value)
    db.commit()
    db.refresh(run)
    return _run_out(run)


@router.delete("/runs/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_run(run_id: int, db: Session = Depends(get_db)):
    """删除运行记录（连同其磁盘附件）。"""
    run = _get_run_or_404(db, run_id)
    for name in _load_json(run.attachments_json, []):
        path = UPLOAD_DIR / name
        if path.exists():
            path.unlink()
    db.delete(run)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ═══════════════════════ 附件上传 ═══════════════════════

@router.post("/runs/{run_id}/attachments", response_model=RunOut)
async def upload_attachment(run_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """上传运行记录附件图片（png/jpg，≤5MB，每条记录最多 3 张）。"""
    run = _get_run_or_404(db, run_id)
    if file.content_type not in ALLOWED_ATTACHMENT_TYPES:
        raise HTTPException(status_code=400, detail="只支持上传 PNG/JPG 图片")
    data = await file.read()
    if len(data) > MAX_ATTACHMENT_BYTES:
        raise HTTPException(status_code=400, detail="图片过大，最大支持 5MB")
    attachments = _load_json(run.attachments_json, [])
    if len(attachments) >= MAX_ATTACHMENTS_PER_RUN:
        raise HTTPException(status_code=400, detail="每条运行记录最多上传 3 张附件图片")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    suffix = ".png" if file.content_type == "image/png" else ".jpg"
    name = f"{uuid.uuid4().hex}{suffix}"
    (UPLOAD_DIR / name).write_bytes(data)
    attachments.append(name)
    run.attachments_json = json.dumps(attachments, ensure_ascii=False)
    db.commit()
    db.refresh(run)
    return _run_out(run)


# ═══════════════════════ 结果比较（本地计算） ═══════════════════════

@router.get("/experiments/{experiment_id}/compare", response_model=ExperimentCompareOut)
def compare_experiment(experiment_id: int, db: Session = Depends(get_db)):
    """同实验全部 run 对比：指标名对齐，缺失值为 null（前端据此渲染表格）。"""
    experiment = _get_experiment_or_404(db, experiment_id)
    runs = _runs_of(db, experiment_id)

    metric_names: list[str] = []
    for metric in _metrics_of(experiment):
        if metric.name not in metric_names:
            metric_names.append(metric.name)
    # 运行结果中出现的额外键也纳入（自由 JSON 兜底）
    for run in runs:
        for key in _load_json(run.results_json, {}):
            if key not in metric_names:
                metric_names.append(key)

    rows = []
    for run in runs:
        results = _load_json(run.results_json, {})
        rows.append(
            CompareRow(
                run_id=run.id,
                run_no=run.run_no,
                started_at=run.started_at,
                values={name: results.get(name) for name in metric_names},
            )
        )
    return ExperimentCompareOut(experiment_id=experiment_id, metric_names=metric_names, rows=rows)


@router.get("/projects/{project_id}/metrics", response_model=MetricsOverviewOut)
def metrics_overview(project_id: int, db: Session = Depends(get_db)):
    """跨实验指标总览：按同名指标聚合全部实验的运行结果（本地计算）。"""
    _get_project_or_404(db, project_id)
    experiments = db.scalars(
        select(Experiment).where(Experiment.project_id == project_id)
    ).all()

    # 指标名 → (unit, higher_is_better, points)
    groups: dict[str, dict] = {}
    for experiment in experiments:
        metrics = _metrics_of(experiment)
        units = {m.name: (m.unit, m.higher_is_better) for m in metrics}
        for run in _runs_of(db, experiment.id):
            results = _load_json(run.results_json, {})
            for key, value in results.items():
                if not isinstance(value, (int, float)):
                    continue  # 非数值指标不进对比
                unit, higher = units.get(key, ("", True))
                group = groups.setdefault(
                    key, {"unit": unit, "higher_is_better": higher, "points": []}
                )
                group["points"].append(
                    MetricPoint(
                        experiment_id=experiment.id,
                        experiment_title=experiment.title,
                        experiment_status=experiment.status,
                        run_id=run.id,
                        run_no=run.run_no,
                        value=float(value),
                    )
                )

    return MetricsOverviewOut(
        metrics=[
            MetricOverviewItem(
                name=name,
                unit=info["unit"],
                higher_is_better=info["higher_is_better"],
                points=sorted(info["points"], key=lambda p: (p.experiment_id, p.run_no)),
            )
            for name, info in groups.items()
        ]
    )
