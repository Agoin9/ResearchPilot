# -*- coding: utf-8 -*-
"""科研建议采纳服务单元测试（v2.3）：决策层 → 执行层打通。

覆盖：
- 采纳：原子创建 Experiment + Task（实验/问题/日期/工时/依赖关联齐全）
- 依赖校验：不存在的依赖 → 400；跨项目依赖 → 400
- 防重复：二次采纳 / 采纳已拒绝建议 → 400
- 拒绝：标记 + 留档，且不创建任何实验/任务
- 修改：保存修改 + 留档；已处理建议不可修改
- 历史：采纳/拒绝/修改全部留档可查
"""
import json
import unittest
from datetime import date, timedelta
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import (
    Experiment,
    ExperimentRun,
    Project,
    ResearchActionLog,
    ResearchAnalysis,
    ResearchQuestion,
    Task,
)
from app.services import research_adoption as adoption


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def seed_analysis(db, n_suggestions=1, with_runs=False):
    project = Project(
        name="测试项目", goal="验证采纳服务", deadline=date(2027, 12, 31), weekly_hours=10
    )
    db.add(project)
    db.flush()
    question = ResearchQuestion(
        project_id=project.id, content="A是否优于B？", hypothesis="A 更优"
    )
    db.add(question)
    db.flush()
    exp = Experiment(
        project_id=project.id, question_id=question.id, title="现有实验",
        objective="复现", hypothesis="A更优", status="running",
    )
    db.add(exp)
    db.flush()
    if with_runs:
        db.add(ExperimentRun(
            experiment_id=exp.id, run_no=1, config_json="{}",
            results_json=json.dumps({"Accuracy": 82.0}), notes="原始结果",
        ))
    suggestions = [
        {
            "objective": f"建议实验{i + 1}",
            "hypothesis": f"假设{i + 1}",
            "changed_variables": "变量",
            "fixed_conditions": "条件",
            "metrics": "Accuracy",
            "expected_observation": "提升",
            "risks": "低",
            "estimated_effort": "2天",
            "converted": False,
        }
        for i in range(n_suggestions)
    ]
    analysis = ResearchAnalysis(
        project_id=project.id,
        question_id=question.id,
        experiment_ids_json=json.dumps([exp.id]),
        run_ids_json="[]",
        card_ids_json="[]",
        observed_facts_json="[]",
        paper_evidence_json="[]",
        stats_json="{}",
        interpretation="演示",
        hypothesis_status="insufficient_evidence",
        uncertainty="",
        next_experiments_json=json.dumps(suggestions, ensure_ascii=False),
        source="demo",
    )
    db.add(analysis)
    db.commit()
    return project, question, exp, analysis


PAYLOAD = {
    "objective": "验证方法A的消融效果",
    "hypothesis": "去掉模块A后精度下降",
    "variables": "是否包含模块A",
    "required_data": "数据集X（训练/验证划分）",
    "preconditions": "方法A复现实验完成",
    "estimated_hours": 12.0,
    "planned_start_date": date(2026, 12, 1),
    "planned_end_date": date(2026, 12, 15),
    "dependencies": [],
}


class TestAdoptSuggestion(unittest.TestCase):
    def test_adopt_creates_experiment_and_task_with_links(self):
        db = make_session()
        _, _, _, analysis = seed_analysis(db)
        experiment, task, log = adoption.adopt_suggestion(
            db, analysis, 0, dict(PAYLOAD), date.today()
        )
        # Experiment 字段
        self.assertEqual(experiment.hypothesis, PAYLOAD["hypothesis"])
        self.assertEqual(experiment.variables, PAYLOAD["variables"])
        self.assertIn("所需数据", experiment.design)
        self.assertEqual(experiment.status, "draft")
        # Task 关联字段
        self.assertEqual(task.experiment_id, experiment.id)
        self.assertEqual(task.question_id, analysis.question_id)
        self.assertEqual(task.planned_start_date, PAYLOAD["planned_start_date"])
        self.assertEqual(task.estimated_hours, 12.0)
        self.assertEqual(task.source_type, "research_analysis")
        self.assertEqual(task.source_id, analysis.id)
        self.assertEqual(json.loads(task.dependencies_json), [])
        # 历史
        self.assertEqual(log.action, "adopted")
        self.assertEqual(log.task_id, task.id)
        self.assertEqual(log.experiment_id, experiment.id)
        # 建议标记 converted
        suggestions = json.loads(analysis.next_experiments_json)
        self.assertTrue(suggestions[0]["converted"])

    def test_adopt_with_dependencies(self):
        db = make_session()
        _, _, _, analysis = seed_analysis(db)
        prereq = Task(
            project_id=analysis.project_id, title="前置任务", status="todo"
        )
        db.add(prereq)
        db.commit()
        payload = dict(PAYLOAD, dependencies=[prereq.id])
        _, task, _ = adoption.adopt_suggestion(db, analysis, 0, payload, date.today())
        self.assertEqual(task.parent_id, prereq.id)  # 复用风险引擎前置阻塞规则
        self.assertEqual(json.loads(task.dependencies_json), [prereq.id])

    def test_missing_dependency_raises(self):
        db = make_session()
        _, _, _, analysis = seed_analysis(db)
        payload = dict(PAYLOAD, dependencies=[99999])
        with self.assertRaises(HTTPException) as ctx:
            adoption.adopt_suggestion(db, analysis, 0, payload, date.today())
        self.assertEqual(ctx.exception.status_code, 400)

    def test_foreign_project_dependency_raises(self):
        db = make_session()
        _, _, _, analysis = seed_analysis(db)
        other = Project(name="其他项目", goal="x", deadline=date(2027, 1, 1), weekly_hours=5)
        db.add(other)
        db.flush()
        foreign_task = Task(project_id=other.id, title="别的项目的任务", status="todo")
        db.add(foreign_task)
        db.commit()
        payload = dict(PAYLOAD, dependencies=[foreign_task.id])
        with self.assertRaises(HTTPException) as ctx:
            adoption.adopt_suggestion(db, analysis, 0, payload, date.today())
        self.assertEqual(ctx.exception.status_code, 400)

    def test_double_adopt_rejected(self):
        db = make_session()
        _, _, _, analysis = seed_analysis(db)
        adoption.adopt_suggestion(db, analysis, 0, dict(PAYLOAD), date.today())
        with self.assertRaises(HTTPException) as ctx:
            adoption.adopt_suggestion(db, analysis, 0, dict(PAYLOAD), date.today())
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("已采纳", str(ctx.exception.detail))

    def test_adopt_nonexistent_suggestion_raises(self):
        db = make_session()
        _, _, _, analysis = seed_analysis(db)
        with self.assertRaises(HTTPException) as ctx:
            adoption.adopt_suggestion(db, analysis, 9, dict(PAYLOAD), date.today())
        self.assertEqual(ctx.exception.status_code, 404)


class TestRejectAndModify(unittest.TestCase):
    def test_reject_marks_and_logs_without_creating(self):
        db = make_session()
        _, _, _, analysis = seed_analysis(db)
        suggestion, log = adoption.reject_suggestion(db, analysis, 0, "方向与导师意见不符")
        self.assertTrue(suggestion["rejected"])
        self.assertEqual(log.action, "rejected")
        # 不创建任何实验/任务
        self.assertEqual(db.query(Task).count(), 0)
        self.assertEqual(db.query(Experiment).count(), 1)  # 只有种子实验
        # 拒绝后不可采纳
        with self.assertRaises(HTTPException) as ctx:
            adoption.adopt_suggestion(db, analysis, 0, dict(PAYLOAD), date.today())
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("拒绝", str(ctx.exception.detail))

    def test_double_reject_raises(self):
        db = make_session()
        _, _, _, analysis = seed_analysis(db)
        adoption.reject_suggestion(db, analysis, 0, "理由")
        with self.assertRaises(HTTPException):
            adoption.reject_suggestion(db, analysis, 0, "再拒一次")

    def test_modify_saves_and_logs(self):
        db = make_session()
        _, _, _, analysis = seed_analysis(db)
        suggestion, log = adoption.modify_suggestion(
            db, analysis, 0, {"objective": "修改后的实验目的", "estimated_effort": "5天"}
        )
        self.assertEqual(suggestion["objective"], "修改后的实验目的")
        self.assertEqual(suggestion["estimated_effort"], "5天")
        self.assertEqual(log.action, "modified")
        self.assertIn("objective", json.loads(log.payload_json)["changes"])

    def test_modify_after_adopt_raises(self):
        db = make_session()
        _, _, _, analysis = seed_analysis(db)
        adoption.adopt_suggestion(db, analysis, 0, dict(PAYLOAD), date.today())
        with self.assertRaises(HTTPException):
            adoption.modify_suggestion(db, analysis, 0, {"objective": "x"})

    def test_full_history_three_actions(self):
        db = make_session()
        _, _, _, analysis = seed_analysis(db, n_suggestions=2)
        adoption.modify_suggestion(db, analysis, 0, {"objective": "改"})
        adoption.adopt_suggestion(db, analysis, 0, dict(PAYLOAD), date.today())
        adoption.reject_suggestion(db, analysis, 1, "不做")
        logs = (
            db.query(ResearchActionLog)
            .filter(ResearchActionLog.analysis_id == analysis.id)
            .order_by(ResearchActionLog.id)
            .all()
        )
        actions = [log.action for log in logs]
        self.assertEqual(actions, ["modified", "adopted", "rejected"])
        suggestions = json.loads(analysis.next_experiments_json)
        self.assertTrue(suggestions[0]["converted"])
        self.assertTrue(suggestions[1]["rejected"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
