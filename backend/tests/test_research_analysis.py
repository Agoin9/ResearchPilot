# -*- coding: utf-8 -*-
"""AI 研究分析服务单元测试（unittest，不依赖外部 API / 真实数据库）。

覆盖（按要求）：
1. 无实验数据 → ResearchAnalysisError（明确提示，不用虚构结果替代）
2. 只有一组实验
3. 多组实验（确定性统计与跨实验比较）
4. 有缺失文献证据（空证据合法，编造引用被丢弃）
5. 模型返回错误 JSON（重试后报错）
6. API 不可用（直接抛 DeepSeekError，不重试）

另覆盖：引用校验（run/卡片/片段 id）、页码以库为准、单实验禁「证明」、
假设状态枚举、建议截断、演示模式（统计真实+文字模板）。
"""
import json
import unittest
from datetime import date
from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.ai_client import DeepSeekError
from app.database import Base
from app.models import (
    Experiment,
    ExperimentRun,
    LiteratureCard,
    Project,
    ResearchQuestion,
)
from app.services import research_analysis as ra

NO_DATA = ra.NO_DATA_MESSAGE


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def seed(db, n_experiments=1, runs_per=1, with_cards=True, with_snippets=True):
    """构造测试数据：问题 + 可选文献卡片（含证据片段）+ n 组实验 × runs 次运行。"""
    project = Project(
        name="测试项目", goal="验证研究分析", deadline=date(2027, 12, 31), weekly_hours=10
    )
    db.add(project)
    db.flush()
    question = ResearchQuestion(
        project_id=project.id,
        content="方法A是否优于方法B？",
        objective="为目标场景选择方法",
        hypothesis="方法A的精度更高",
    )
    db.add(question)
    db.flush()
    if with_cards:
        snippets = (
            json.dumps(
                [
                    {"quote": "方法A在数据集X上取得87.3%的精度", "page": "5"},
                    {"quote": "基线方法为80.1%", "page": "6"},
                ],
                ensure_ascii=False,
            )
            if with_snippets
            else "[]"
        )
        db.add(
            LiteratureCard(
                project_id=project.id,
                question_id=question.id,
                title="对比论文",
                key_results="方法A优于基线",
                evidence_snippets_json=snippets,
            )
        )
    for i in range(n_experiments):
        exp = Experiment(
            project_id=project.id,
            question_id=question.id,
            title=f"实验{i + 1}",
            objective="对比实验",
            hypothesis="A 精度更高",
            metrics_json=json.dumps(
                [{"name": "Accuracy", "unit": "%", "higher_is_better": True}]
            ),
            status="running",
        )
        db.add(exp)
        db.flush()
        for j in range(runs_per):
            db.add(
                ExperimentRun(
                    experiment_id=exp.id,
                    run_no=j + 1,
                    config_json="{}",
                    results_json=json.dumps({"Accuracy": 80.0 + i * 5 + j}),
                    notes=f"第{j + 1}次",
                )
            )
    db.commit()
    return question


def make_context(n_experiments=1, runs_per=1):
    """手工构造 context（供 validate 测试，不依赖数据库）。"""
    valid_run_ids = set()
    experiments = []
    experiments_data = []
    for i in range(n_experiments):
        runs = []
        data_runs = []
        for j in range(runs_per):
            run_id = i * 100 + j + 1
            valid_run_ids.add(run_id)
            runs.append({"id": run_id, "run_no": j + 1, "config": {}, "results": {"Accuracy": 80.0 + i * 5 + j}, "notes": "", "random_seed": 42, "git_commit": ""})
            data_runs.append({"run_no": j + 1, "results": {"Accuracy": 80.0 + i * 5 + j}})
        experiments.append({"id": i + 1, "title": f"实验{i + 1}", "objective": "对比", "hypothesis": "A更优", "status": "running", "runs": runs})
        experiments_data.append({"id": i + 1, "title": f"实验{i + 1}", "metrics": [{"name": "Accuracy", "unit": "%", "higher_is_better": True}], "runs": data_runs})
    cards = [{
        "id": 1, "title": "对比论文", "method": "", "metrics": "", "key_results": "A优于基线",
        "limitations": "", "innovations": "",
        "snippets": [
            {"snippet_id": "1-1", "page": "5", "quote": "方法A在数据集X上取得87.3%的精度"},
            {"snippet_id": "1-2", "page": "6", "quote": "基线方法为80.1%"},
        ],
    }]
    return {
        "question": {"id": 1, "content": "A是否优于B", "objective": "", "hypothesis": "A更优"},
        "cards": cards,
        "experiments": experiments,
        "stats": ra.compute_stats(experiments_data),
        "valid_run_ids": valid_run_ids,
        "n_experiments": n_experiments,
    }


# ═══════════════════════ 确定性统计 ═══════════════════════

class TestComputeStats(unittest.TestCase):
    def test_single_experiment_stats(self):
        data = [{"id": 1, "title": "实验1", "metrics": [{"name": "Accuracy", "unit": "%", "higher_is_better": True}],
                 "runs": [{"run_no": 1, "results": {"Accuracy": 80.0}},
                          {"run_no": 2, "results": {"Accuracy": 88.0}},
                          {"run_no": 3, "results": {"Accuracy": 84.0}}]}]
        stats = ra.compute_stats(data)
        row = stats["metrics"][0]["experiments"][0]
        self.assertEqual(row["min"], 80.0)
        self.assertEqual(row["max"], 88.0)
        self.assertEqual(row["mean"], 84.0)
        self.assertEqual(row["best"], 88.0)
        self.assertEqual(row["best_run_no"], 2)
        self.assertEqual(row["latest"], 84.0)
        self.assertEqual(row["latest_run_no"], 3)
        self.assertEqual(stats["comparisons"], [])  # 单实验无跨实验比较

    def test_multiple_experiments_comparison(self):
        data = [
            {"id": 1, "title": "实验1", "metrics": [{"name": "Accuracy", "unit": "%", "higher_is_better": True}],
             "runs": [{"run_no": 1, "results": {"Accuracy": 80.0}},
                      {"run_no": 2, "results": {"Accuracy": 82.0}}]},
            {"id": 2, "title": "实验2", "metrics": [{"name": "Accuracy", "unit": "%", "higher_is_better": True}],
             "runs": [{"run_no": 1, "results": {"Accuracy": 85.0}},
                      {"run_no": 2, "results": {"Accuracy": 79.0}}]},
        ]
        stats = ra.compute_stats(data)
        rows = stats["metrics"][0]["experiments"]
        self.assertEqual(len(rows), 2)
        comparison = stats["comparisons"][0]
        self.assertEqual(comparison["metric"], "Accuracy")
        # 实验1 最优 82.0；实验2 最优 85.0 → delta +3.0
        self.assertEqual(comparison["rows"][0]["delta_vs_first"], 0.0)
        self.assertEqual(comparison["rows"][1]["delta_vs_first"], 3.0)

    def test_non_numeric_values_ignored(self):
        data = [{"id": 1, "title": "实验1", "metrics": [],
                 "runs": [{"run_no": 1, "results": {"Accuracy": 80.0, "备注": "无法量化", "ok": True}}]}]
        stats = ra.compute_stats(data)
        names = [m["name"] for m in stats["metrics"]]
        self.assertIn("Accuracy", names)
        self.assertNotIn("备注", names)
        self.assertNotIn("ok", names)


# ═══════════════════════ 无实验数据 / 上下文组装 ═══════════════════════

class TestNoDataAndGather(unittest.TestCase):
    def test_generate_no_data_raises(self):
        db = make_session()
        question = seed(db, n_experiments=0)
        with self.assertRaises(ra.ResearchAnalysisError) as ctx:
            ra.generate_analysis(db, question)
        self.assertIn("当前缺少实验数据", str(ctx.exception))

    def test_gather_single_experiment(self):
        db = make_session()
        question = seed(db, n_experiments=1, runs_per=2)
        context = ra.gather_context(db, question)
        self.assertEqual(context["n_experiments"], 1)
        self.assertEqual(len(context["valid_run_ids"]), 2)
        self.assertEqual(context["cards"][0]["snippets"][0]["snippet_id"], "1-1")
        self.assertEqual(context["cards"][0]["snippets"][0]["page"], "5")
        self.assertIn("Accuracy", context["stats"]["metrics"][0]["name"])

    def test_gather_multiple_experiments(self):
        db = make_session()
        question = seed(db, n_experiments=2, runs_per=2)
        context = ra.gather_context(db, question)
        self.assertEqual(context["n_experiments"], 2)
        self.assertEqual(len(context["valid_run_ids"]), 4)
        self.assertEqual(len(context["stats"]["comparisons"]), 1)

    def test_gather_without_cards(self):
        db = make_session()
        question = seed(db, n_experiments=1, runs_per=1, with_cards=False)
        context = ra.gather_context(db, question)
        self.assertEqual(context["cards"], [])


# ═══════════════════════ 输出校验（防编造） ═══════════════════════

class TestValidateAnalysis(unittest.TestCase):
    def valid_ai_output(self, **overrides):
        base = {
            "observed_facts": [
                {"experiment_run_id": 1, "content": "第1次运行 Accuracy=80.0"},
                {"experiment_run_id": 2, "content": "第2次运行 Accuracy=81.0"},
            ],
            "paper_evidence": [
                {"paper_note_id": 1, "snippet_id": "1-1", "page": "5",
                 "quote": "方法A在数据集X上取得87.3%的精度", "statement": "文献报告了更高的精度"},
            ],
            "interpretation": "第2次运行精度略升，可能是参数差异导致（推测）",
            "hypothesis_status": "support",
            "uncertainty": "样本少，未重复验证",
            "next_experiments": [
                {"objective": "消融实验", "hypothesis": "关键模块贡献大", "changed_variables": "去掉模块A",
                 "fixed_conditions": "其余不变", "metrics": "Accuracy", "expected_observation": "精度下降",
                 "risks": "时间成本", "estimated_effort": "2天"},
            ],
        }
        base.update(overrides)
        return base

    def test_valid_output_passes(self):
        sections = ra.validate_analysis(self.valid_ai_output(), make_context(runs_per=2))
        self.assertEqual(len(sections["observed_facts"]), 2)
        self.assertEqual(len(sections["paper_evidence"]), 1)

    def test_fabricated_run_ids_dropped_all_invalid_raises(self):
        output = self.valid_ai_output(
            observed_facts=[{"experiment_run_id": 9999, "content": "编造的事实"}]
        )
        with self.assertRaises(ra.ResearchFormatError):
            ra.validate_analysis(output, make_context(runs_per=2))

    def test_fabricated_run_ids_partial_keeps_valid(self):
        output = self.valid_ai_output(
            observed_facts=[
                {"experiment_run_id": 9999, "content": "编造"},
                {"experiment_run_id": 1, "content": "真实"},
            ]
        )
        sections = ra.validate_analysis(output, make_context(runs_per=2))
        self.assertEqual([f["experiment_run_id"] for f in sections["observed_facts"]], [1])

    def test_missing_literature_evidence_is_empty_legal(self):
        # 文献证据缺失：AI 返回空数组 → 合法，不得编造引用
        output = self.valid_ai_output(paper_evidence=[])
        sections = ra.validate_analysis(output, make_context(runs_per=2))
        self.assertEqual(sections["paper_evidence"], [])

    def test_fabricated_card_or_snippet_dropped(self):
        output = self.valid_ai_output(
            paper_evidence=[
                {"paper_note_id": 999, "snippet_id": "999-1", "page": "1", "quote": "x", "statement": "编造卡片"},
                {"paper_note_id": 1, "snippet_id": "1-99", "page": "1", "quote": "x", "statement": "编造片段"},
                {"paper_note_id": 1, "snippet_id": "1-1", "page": "1", "quote": "方法A在数据集X上取得87.3%的精度", "statement": "真实证据"},
            ]
        )
        sections = ra.validate_analysis(output, make_context(runs_per=2))
        self.assertEqual(len(sections["paper_evidence"]), 1)

    def test_page_and_quote_use_database_truth(self):
        # AI 谎报页码：页码与原文均以数据库为准（引用 id 与引文真实）
        output = self.valid_ai_output(
            paper_evidence=[
                {"paper_note_id": 1, "snippet_id": "1-1", "page": "999",
                 "quote": "方法A在数据集X上取得87.3%的精度", "statement": "真实证据"},
            ]
        )
        sections = ra.validate_analysis(output, make_context(runs_per=2))
        self.assertEqual(sections["paper_evidence"][0]["page"], "5")
        self.assertIn("87.3%", sections["paper_evidence"][0]["quote"])

    def test_quote_not_from_snippet_dropped(self):
        output = self.valid_ai_output(
            paper_evidence=[
                {"paper_note_id": 1, "snippet_id": "1-2", "page": "6",
                 "quote": "完全无关的编造句子", "statement": "x"},
            ]
        )
        sections = ra.validate_analysis(output, make_context(runs_per=2))
        self.assertEqual(sections["paper_evidence"], [])

    def test_invalid_hypothesis_status_raises(self):
        output = self.valid_ai_output(hypothesis_status="maybe")
        with self.assertRaises(ra.ResearchFormatError):
            ra.validate_analysis(output, make_context(runs_per=2))

    def test_interpretation_without_speculation_marker_raises(self):
        # 解释必须明确标记为推测：写成结论 → 触发重试
        output = self.valid_ai_output(interpretation="两组实验差异显著，方法A更优（结论）")
        with self.assertRaises(ra.ResearchFormatError) as ctx:
            ra.validate_analysis(output, make_context(runs_per=2))
        self.assertIn("推测", str(ctx.exception))

    def test_interpretation_with_marker_passes(self):
        for text in ("两组实验存在差异，可能是参数不同导致（推测）",
                     "尚不能确定方法A更优，需更多重复实验"):
            output = self.valid_ai_output(interpretation=text)
            sections = ra.validate_analysis(output, make_context(runs_per=2))
            self.assertEqual(sections["interpretation"], text)

    def test_single_experiment_forbids_proof_claim(self):
        output = self.valid_ai_output(interpretation="这证明方法A更优（结论）")
        with self.assertRaises(ra.ResearchFormatError):
            ra.validate_analysis(output, make_context(n_experiments=1, runs_per=2))

    def test_single_experiment_insufficient_status_ok(self):
        output = self.valid_ai_output(
            hypothesis_status="insufficient_evidence",
            interpretation="单次实验不足以判断，可能是偶然（推测）",
        )
        sections = ra.validate_analysis(output, make_context(n_experiments=1, runs_per=2))
        self.assertEqual(sections["hypothesis_status"], "insufficient_evidence")

    def test_next_experiments_truncated_and_missing_dropped(self):
        items = [
            {"objective": f"实验{i}", "hypothesis": "H"} for i in range(5)
        ] + [{"objective": "", "hypothesis": ""}]
        output = self.valid_ai_output(next_experiments=items)
        sections = ra.validate_analysis(output, make_context(runs_per=2))
        self.assertEqual(len(sections["next_experiments"]), ra.MAX_NEXT_EXPERIMENTS)
        self.assertFalse(sections["next_experiments"][0]["converted"])


# ═══════════════════════ 生成流程（错误 JSON / API 不可用 / 演示模式） ═══════════════════════

class TestGenerateFlow(unittest.TestCase):
    def _patch_client(self, responses):
        mock_client = MagicMock()
        mock_client.chat.side_effect = responses
        return patch("app.services.research_analysis.DeepSeekClient", return_value=mock_client), mock_client

    def test_model_returns_bad_json_retries_then_raises(self):
        db = make_session()
        question = seed(db, n_experiments=1, runs_per=2)
        with patch("app.services.research_analysis.DEEPSEEK_API_KEY", "sk-test"):
            patcher, mock_client = self._patch_client(["这不是JSON", "也不是JSON", "还是不对"])
            with patcher:
                with self.assertRaises(DeepSeekError):
                    ra.generate_analysis(db, question)
            # 1 次初始 + 2 次重试 = 3 次调用
            self.assertEqual(mock_client.chat.call_count, 3)

    def test_model_missing_fields_retries(self):
        db = make_session()
        question = seed(db, n_experiments=1, runs_per=2)
        with patch("app.services.research_analysis.DEEPSEEK_API_KEY", "sk-test"):
            patcher, mock_client = self._patch_client(
                [
                    json.dumps({"observed_facts": []}),  # 缺字段且空事实
                    json.dumps({"observed_facts": []}),
                    json.dumps({"observed_facts": []}),
                ]
            )
            with patcher:
                with self.assertRaises(DeepSeekError):
                    ra.generate_analysis(db, question)
            self.assertEqual(mock_client.chat.call_count, 3)

    def test_api_unavailable_propagates_without_retry(self):
        db = make_session()
        question = seed(db, n_experiments=1, runs_per=2)
        with patch("app.services.research_analysis.DEEPSEEK_API_KEY", "sk-test"):
            patcher, mock_client = self._patch_client(
                [DeepSeekError("无法连接 DeepSeek API，请检查网络是否可访问 api.deepseek.com")]
            )
            with patcher:
                with self.assertRaises(DeepSeekError) as ctx:
                    ra.generate_analysis(db, question)
            self.assertIn("无法连接", str(ctx.exception))
            self.assertEqual(mock_client.chat.call_count, 1)  # API 错误不重试

    def test_success_path_with_real_context(self):
        db = make_session()
        question = seed(db, n_experiments=2, runs_per=2)
        context = ra.gather_context(db, question)
        run_ids = sorted(context["valid_run_ids"])
        ai_output = {
            "observed_facts": [
                {"experiment_run_id": run_ids[0], "content": "真实事实1"},
                {"experiment_run_id": run_ids[1], "content": "真实事实2"},
            ],
            "paper_evidence": [
                {"paper_note_id": 1, "snippet_id": "1-1", "page": "5",
                 "quote": "方法A在数据集X上取得87.3%的精度", "statement": "文献证据"},
            ],
            "interpretation": "两组实验的最优值存在差异，可能是变量不同导致（推测）",
            "hypothesis_status": "support",
            "uncertainty": "样本量小",
            "next_experiments": [
                {"objective": "重复实验", "hypothesis": "结果可复现", "changed_variables": "无",
                 "fixed_conditions": "全部", "metrics": "Accuracy", "expected_observation": "相近",
                 "risks": "低", "estimated_effort": "1天"},
            ],
        }
        with patch("app.services.research_analysis.DEEPSEEK_API_KEY", "sk-test"):
            patcher, _ = self._patch_client([json.dumps(ai_output, ensure_ascii=False)])
            with patcher:
                sections, source, ctx = ra.generate_analysis(db, question)
        self.assertEqual(source, "deepseek")
        self.assertEqual(sections["hypothesis_status"], "support")
        self.assertEqual(len(sections["observed_facts"]), 2)
        self.assertIn("comparisons", ctx["stats"])

    def test_demo_mode_without_key(self):
        db = make_session()
        question = seed(db, n_experiments=1, runs_per=2)
        context = ra.gather_context(db, question)
        with patch("app.services.research_analysis.DEEPSEEK_API_KEY", ""):
            sections, source, _ = ra.generate_analysis(db, question)
        self.assertEqual(source, "demo")
        # 事实引用必须真实存在
        for fact in sections["observed_facts"]:
            self.assertIn(fact["experiment_run_id"], context["valid_run_ids"])
        # 统计为真实计算
        self.assertIn("metrics", context["stats"])
        # 明确标注演示模式，不得描述为真实分析
        self.assertIn("演示模式", sections["interpretation"])
        self.assertEqual(sections["hypothesis_status"], "insufficient_evidence")


if __name__ == "__main__":
    unittest.main(verbosity=2)
