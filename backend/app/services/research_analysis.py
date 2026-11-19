"""AI 研究分析编排（v2.2 核心服务）：

职责边界（严格）：
- Python 后端：确定性统计计算（min/max/mean/best/delta）、上下文组装、引用校验；
- DeepSeek：只负责解释、判断与建议，不得自行计算数值或编造引用；
- 数据库：唯一事实来源——不存在的 run/卡片/片段引用一律丢弃，页码与原文以库为准。

输出结构（严格 JSON，Pydantic 校验）：
1. observed_facts   实验事实（必须带真实 experiment_run_id）
2. paper_evidence   文献证据（必须带真实 paper_note_id + snippet_id，页码/原文以库为准）
3. interpretation   解释（明确为推测，非结论）
4. hypothesis_status support / not_support / insufficient_evidence
5. uncertainty      数据不足、混杂因素、无法判断的问题
6. next_experiments 最多 3 条（8 个字段齐全）
7. task_conversion  由用户显式调用转换接口，AI 输出阶段不产生任何任务

无实验记录 → ResearchAnalysisError（路由转 400，明确提示）；
无 Key → 演示模板（统计值真实、文字模板、source=demo）。
"""
import json
import re
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai_client import DeepSeekClient, DeepSeekError
from app.config import AI_FORMAT_RETRY_TIMES, DEEPSEEK_API_KEY
from app.models import Experiment, ExperimentRun, LiteratureCard, ResearchQuestion

NO_DATA_MESSAGE = "当前缺少实验数据，无法进行结果分析；请先为该研究问题关联实验并录入真实运行记录"
MAX_NEXT_EXPERIMENTS = 3
HYPOTHESIS_STATUSES = ("support", "not_support", "insufficient_evidence")
# interpretation 必须出现的推测性表述（需求：明确标记为推测而不是结论）
SPECULATION_MARKERS = ("推测", "可能", "或许", "尚不", "待验证", "不确定", "难以断言", "不足以")


class ResearchAnalysisError(Exception):
    """用户可读的分析前置条件错误（路由层转 400）。"""


class ResearchFormatError(Exception):
    """DeepSeek 输出格式/约束错误（触发重试）。"""


def _fmt_number(value) -> str:
    """数值展示：浮点保留 4 位小数，整数原样。"""
    if isinstance(value, float):
        return f"{round(value, 4):g}"
    return str(value)


def _load_json(text: str | None, default):
    try:
        return json.loads(text) if text else default
    except (ValueError, TypeError):
        return default


# ═══════════════════════ 确定性统计（Python 计算，AI 不得自行算数） ═══════════════════════

def compute_stats(experiments: list[dict]) -> dict:
    """按指标聚合全部实验运行记录，计算确定性统计。

    experiments: [{"id", "title", "metrics": [{"name","unit","higher_is_better"}],
                   "runs": [{"run_no", "results": {指标名: 数值}}]}]

    返回：
    {
      "metrics": [{"name","unit","higher_is_better","experiments": [
          {"experiment_id","title","run_count","min","max","mean",
           "best","best_run_no","latest","latest_run_no"}]}],
      "comparisons": [{"metric","unit","higher_is_better","rows": [
          {"experiment_id","title","best","best_run_no","delta_vs_first"}]}]
    }
    """
    # 指标名 → {"unit", "higher_is_better", "points": [(exp_id, title, run_no, value)]}
    metric_map: dict[str, dict] = {}
    for exp in experiments:
        direction_map = {m["name"]: m.get("higher_is_better", True) for m in exp.get("metrics", [])}
        unit_map = {m["name"]: m.get("unit", "") for m in exp.get("metrics", [])}
        for run in exp.get("runs", []):
            for name, value in (run.get("results") or {}).items():
                if not isinstance(value, (int, float)) or isinstance(value, bool):
                    continue  # 非数值不进统计
                group = metric_map.setdefault(
                    name,
                    {"unit": unit_map.get(name, ""),
                     "higher_is_better": direction_map.get(name, True),
                     "points": []},
                )
                group["points"].append((exp["id"], exp["title"], run["run_no"], float(value)))

    metrics = []
    comparisons = []
    for name in sorted(metric_map.keys()):
        group = metric_map[name]
        higher = group["higher_is_better"]
        by_exp: dict[int, dict] = {}
        for exp_id, title, run_no, value in group["points"]:
            entry = by_exp.setdefault(
                exp_id,
                {"experiment_id": exp_id, "title": title, "values": []},
            )
            entry["values"].append((run_no, value))

        rows = []
        for entry in by_exp.values():
            values = sorted(entry["values"], key=lambda x: x[0])
            nums = [v for _, v in values]
            best_run_no, best = max(values, key=lambda x: x[1]) if higher else min(values, key=lambda x: x[1])
            latest_run_no, latest = values[-1]
            rows.append({
                "experiment_id": entry["experiment_id"],
                "title": entry["title"],
                "run_count": len(nums),
                "min": round(min(nums), 4),
                "max": round(max(nums), 4),
                "mean": round(sum(nums) / len(nums), 4),
                "best": round(best, 4),
                "best_run_no": best_run_no,
                "latest": round(latest, 4),
                "latest_run_no": latest_run_no,
            })
        rows.sort(key=lambda r: r["experiment_id"])
        metrics.append({
            "name": name,
            "unit": group["unit"],
            "higher_is_better": higher,
            "experiments": rows,
        })

        # 跨实验比较：仅当 >=2 个实验都报告了该指标
        if len(rows) >= 2:
            first_best = rows[0]["best"]
            comparison_rows = [
                {
                    "experiment_id": r["experiment_id"],
                    "title": r["title"],
                    "best": r["best"],
                    "best_run_no": r["best_run_no"],
                    "delta_vs_first": round(r["best"] - first_best, 4),
                }
                for r in rows
            ]
            comparisons.append({
                "metric": name,
                "unit": group["unit"],
                "higher_is_better": higher,
                "rows": comparison_rows,
            })

    return {"metrics": metrics, "comparisons": comparisons}


# ═══════════════════════ 上下文组装 ═══════════════════════

def gather_context(db: Session, question: ResearchQuestion) -> dict:
    """读取与研究问题关联的真实数据，组装分析上下文。

    返回结构（同时供 Prompt 与校验使用）：
    {
      "question": {...},
      "cards": [{"id","title","method","metrics","key_results","limitations","innovations",
                 "snippets":[{"snippet_id":"卡片id-序号","page","quote"}]}],
      "experiments": [{"id","title","objective","hypothesis","status",
                       "metrics":[MetricDef dict...],
                       "runs":[{"id","run_no","config","results","notes","random_seed","git_commit"}]}],
      "stats": compute_stats(...),
      "valid_run_ids": {int},
      "n_experiments": int,
    }
    """
    cards = list(
        db.scalars(
            select(LiteratureCard)
            .where(LiteratureCard.question_id == question.id)
            .order_by(LiteratureCard.id)
        )
    )
    experiments = list(
        db.scalars(
            select(Experiment)
            .where(Experiment.question_id == question.id)
            .order_by(Experiment.id)
        )
    )

    card_ctx = []
    for card in cards:
        snippets_raw = _load_json(card.evidence_snippets_json, [])
        snippets = []
        for index, sn in enumerate(snippets_raw, start=1):
            if not isinstance(sn, dict) or not str(sn.get("quote") or "").strip():
                continue
            snippets.append({
                "snippet_id": f"{card.id}-{index}",
                "page": str(sn.get("page") or "").strip() or None,
                "quote": str(sn["quote"]).strip(),
            })
        card_ctx.append({
            "id": card.id,
            "title": card.title or "未命名卡片",
            "method": card.method or "",
            "metrics": card.metrics or "",
            "key_results": card.key_results or "",
            "limitations": card.limitations or "",
            "innovations": card.innovations or "",
            "snippets": snippets,
        })

    experiments_data = []
    experiment_ctx = []
    valid_run_ids: set[int] = set()
    for exp in experiments:
        runs = list(
            db.scalars(
                select(ExperimentRun)
                .where(ExperimentRun.experiment_id == exp.id)
                .order_by(ExperimentRun.run_no)
            )
        )
        metric_defs = _load_json(exp.metrics_json, [])
        run_ctx = []
        for run in runs:
            valid_run_ids.add(run.id)
            run_ctx.append({
                "id": run.id,
                "run_no": run.run_no,
                "config": _load_json(run.config_json, {}),
                "results": _load_json(run.results_json, {}),
                "notes": run.notes or "",
                "random_seed": run.random_seed,
                "git_commit": run.git_commit,
            })
        experiments_data.append({
            "id": exp.id,
            "title": exp.title,
            "metrics": [
                {"name": m.get("name", ""), "unit": m.get("unit", ""),
                 "higher_is_better": m.get("higher_is_better", True)}
                for m in metric_defs if isinstance(m, dict) and m.get("name")
            ],
            "runs": [{"run_no": r["run_no"], "results": r["results"]} for r in run_ctx],
        })
        experiment_ctx.append({
            "id": exp.id,
            "title": exp.title,
            "objective": exp.objective,
            "hypothesis": exp.hypothesis or "",
            "status": exp.status,
            "runs": run_ctx,
        })

    stats = compute_stats(experiments_data)
    return {
        "question": {
            "id": question.id,
            "content": question.content,
            "objective": question.objective or "",
            "hypothesis": question.hypothesis or "",
        },
        "cards": card_ctx,
        "experiments": experiment_ctx,
        "stats": stats,
        "valid_run_ids": valid_run_ids,
        "n_experiments": len(experiments),
    }


# ═══════════════════════ Prompt 组装 ═══════════════════════

def build_messages(context: dict) -> list[dict]:
    """组装强约束 Prompt：所有引用必须来自给定数据，数值只能引用统计块。"""
    question = context["question"]
    stats = context["stats"]

    run_lines = []
    for exp in context["experiments"]:
        run_lines.append(f"实验「{exp['title']}」（experiment_id={exp['id']}，状态 {exp['status']}）")
        run_lines.append(f"  目的：{exp['objective']}")
        if exp["hypothesis"]:
            run_lines.append(f"  待验证假设：{exp['hypothesis']}")
        for run in exp["runs"]:
            run_lines.append(
                f"  - 运行 #{run['run_no']}（experiment_run_id={run['id']}）："
                f"指标={json.dumps(run['results'], ensure_ascii=False)}，"
                f"参数={json.dumps(run['config'], ensure_ascii=False)}，"
                f"备注={run['notes'] or '无'}，随机种子={run['random_seed']}，"
                f"Git={run['git_commit'] or '无'}"
            )

    card_lines = []
    for card in context["cards"]:
        card_lines.append(f"[paper_note_id={card['id']}]《{card['title']}》")
        if card["method"]:
            card_lines.append(f"  方法：{card['method'][:300]}")
        if card["key_results"]:
            card_lines.append(f"  主要结果：{card['key_results'][:500]}")
        if card["limitations"]:
            card_lines.append(f"  局限：{card['limitations'][:300]}")
        for sn in card["snippets"]:
            card_lines.append(
                f"  证据片段 {sn['snippet_id']}（页码 p.{sn['page'] or '未知'}）：{sn['quote'][:300]}"
            )

    system = (
        "你是严谨的科研分析助手。用户提供：一个研究问题、关联文献卡片（含证据片段）"
        "、关联实验的运行记录、以及由后端确定性计算好的统计值。\n"
        "输出要求（必须严格遵守）：\n"
        "1. 只输出一个 JSON 对象，不要任何解释文字或 Markdown 代码块：\n"
        '   {"observed_facts": [{"experiment_run_id": 数字, "content": "事实描述"}], '
        '"paper_evidence": [{"paper_note_id": 数字, "snippet_id": "卡片id-序号", '
        '"page": "页码", "quote": "原文摘录", "statement": "该证据说明什么"}], '
        '"interpretation": "解释（推测）", '
        '"hypothesis_status": "support / not_support / insufficient_evidence", '
        '"uncertainty": "数据不足与无法判断之处", '
        '"next_experiments": [{"objective": "", "hypothesis": "", "changed_variables": "", '
        '"fixed_conditions": "", "metrics": "", "expected_observation": "", '
        '"risks": "", "estimated_effort": ""}]}\n'
        "2. observed_facts 只能引用给定运行记录中真实存在的 experiment_run_id 与数值，"
        "禁止编造任何记录或数字；\n"
        "3. paper_evidence 只能引用给定卡片与片段：paper_note_id、snippet_id、quote "
        "必须逐字来自给定数据；找不到文献依据时 paper_evidence 写空数组 []，"
        "并在 interpretation/uncertainty 中明确写「原文未找到」——严禁编造引用；\n"
        "4. interpretation 是基于当前事实的推测而非结论，表述必须体现推测性质"
        "（如「可能是」「推测」「尚不能确定」），不得使用「证明」「证实」等结论性词汇；\n"
        "5. hypothesis_status 只能取 support / not_support / insufficient_evidence 之一："
        "仅有一组实验或单次运行时，不得声称假设得到证明，应谨慎给出判断；\n"
        "6. 所有数值只能引用「确定性统计」块中的数据，不得自行计算或编造数值；\n"
        "7. next_experiments 最多 3 条，每条 8 个字段都必须给出（不确定时写「待定」），"
        "建议是待验证的实验方向，不是结论；\n"
        "8. 若文献对某问题没有说明，明确写「原文未找到」，不得用外部知识补充。"
    )
    user = (
        f"研究问题：{question['content']}\n"
        f"研究目标：{question['objective'] or '无'}\n"
        f"研究假设：{question['hypothesis'] or '无'}\n\n"
        f"确定性统计（后端计算，可信）：\n{json.dumps(stats, ensure_ascii=False)}\n\n"
        f"实验运行记录（共 {len(context['experiments'])} 组实验）：\n" + "\n".join(run_lines) + "\n\n"
        f"文献卡片与证据片段：\n" + "\n".join(card_lines) + "\n"
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


# ═══════════════════════ 输出校验（严格，防编造） ═══════════════════════

def _extract_json(text: str) -> dict:
    raw = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL)
    if fence:
        raw = fence.group(1).strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}")
        if start == -1 or end <= start:
            raise ResearchFormatError("输出中找不到 JSON 对象")
        try:
            data = json.loads(raw[start : end + 1])
        except json.JSONDecodeError as e:
            raise ResearchFormatError(f"JSON 解析失败：{e.msg}")
    if not isinstance(data, dict):
        raise ResearchFormatError("顶层结构不是 JSON 对象")
    return data


def _normalize(text: str) -> str:
    return "".join(text.split())


def validate_analysis(data: dict, context: dict) -> dict:
    """严格校验 AI 输出：引用必须真实存在，页码/原文以数据库为准。

    返回完整分节结构；硬性违反抛 ResearchFormatError（触发重试）。
    """
    # 1. observed_facts：引用必须真实存在
    raw_facts = data.get("observed_facts")
    if not isinstance(raw_facts, list):
        raise ResearchFormatError("observed_facts 必须是数组")
    facts = []
    for item in raw_facts:
        if not isinstance(item, dict):
            continue
        try:
            run_id = int(item.get("experiment_run_id"))
        except (TypeError, ValueError):
            continue
        if run_id not in context["valid_run_ids"]:
            continue  # 引用不存在的记录 → 丢弃（不得编造）
        content = str(item.get("content") or "").strip()
        if not content:
            continue
        facts.append({"experiment_run_id": run_id, "content": content[:2000]})
    if not facts:
        raise ResearchFormatError("observed_facts 中没有引用任何真实存在的运行记录")

    # 2. paper_evidence：引用必须真实存在，页码/原文以库为准
    raw_evidence = data.get("paper_evidence")
    if not isinstance(raw_evidence, list):
        raise ResearchFormatError("paper_evidence 必须是数组")
    card_by_id = {c["id"]: c for c in context["cards"]}
    snippet_map = {
        sn["snippet_id"]: sn for c in context["cards"] for sn in c["snippets"]
    }
    evidence = []
    for item in raw_evidence:
        if not isinstance(item, dict):
            continue
        try:
            card_id = int(item.get("paper_note_id"))
        except (TypeError, ValueError):
            continue
        if card_id not in card_by_id:
            continue  # 编造的卡片 id → 丢弃
        snippet = snippet_map.get(str(item.get("snippet_id") or ""))
        if snippet is None:
            continue  # 编造的片段 id → 丢弃
        ai_quote = _normalize(str(item.get("quote") or ""))
        if ai_quote:
            # AI 给的原句必须是片段原文的子串（防改写/编造）
            if ai_quote[:8] not in _normalize(snippet["quote"]):
                continue
        statement = str(item.get("statement") or "").strip()
        if not statement:
            continue
        evidence.append({
            "paper_note_id": card_id,
            "snippet_id": snippet["snippet_id"],
            "page": snippet["page"],     # 页码以数据库为准
            "quote": snippet["quote"],   # 原文以数据库为准（防 AI 改写）
            "statement": statement[:2000],
        })

    # 3. interpretation：非空，且必须明确标记为推测（而不是结论）
    interpretation = str(data.get("interpretation") or "").strip()
    if not interpretation:
        raise ResearchFormatError("缺少 interpretation 字段")
    if not any(marker in interpretation for marker in SPECULATION_MARKERS):
        raise ResearchFormatError(
            "interpretation 必须明确标记为推测（使用「推测」「可能」「尚不能确定」等表述），"
            "不得写成结论"
        )

    # 4. hypothesis_status：枚举
    status = str(data.get("hypothesis_status") or "")
    if status not in HYPOTHESIS_STATUSES:
        raise ResearchFormatError(
            "hypothesis_status 必须是 support / not_support / insufficient_evidence 之一"
        )

    # 5. uncertainty
    uncertainty = str(data.get("uncertainty") or "").strip()

    # 单组实验不得声称证明
    if context["n_experiments"] <= 1:
        for word in ("证明", "证实", "已验证"):
            if word in interpretation + uncertainty:
                raise ResearchFormatError(
                    f"仅有一组实验时不得使用「{word}」等结论性表述"
                )

    # 6. next_experiments：≤3 条，关键字段必填
    raw_next = data.get("next_experiments")
    if not isinstance(raw_next, list):
        raise ResearchFormatError("next_experiments 必须是数组")
    next_experiments = []
    for item in raw_next[:MAX_NEXT_EXPERIMENTS]:
        if not isinstance(item, dict):
            continue
        objective = str(item.get("objective") or "").strip()
        hypothesis = str(item.get("hypothesis") or "").strip()
        if not objective or not hypothesis:
            continue  # 缺关键字段 → 丢弃
        next_experiments.append({
            "objective": objective[:1000],
            "hypothesis": hypothesis[:1000],
            "changed_variables": str(item.get("changed_variables") or "").strip()[:1000],
            "fixed_conditions": str(item.get("fixed_conditions") or "").strip()[:1000],
            "metrics": str(item.get("metrics") or "").strip()[:1000],
            "expected_observation": str(item.get("expected_observation") or "").strip()[:1000],
            "risks": str(item.get("risks") or "").strip()[:1000],
            "estimated_effort": str(item.get("estimated_effort") or "").strip()[:500],
            "converted": False,
        })

    return {
        "observed_facts": facts,
        "paper_evidence": evidence,
        "interpretation": interpretation,
        "hypothesis_status": status,
        "uncertainty": uncertainty,
        "next_experiments": next_experiments,
    }


# ═══════════════════════ 演示模板（无 Key；统计值真实、文字模板） ═══════════════════════

DEMO_WARNING = (
    "演示模式：未配置 DeepSeek API Key。本分析的统计数值由后端基于数据库真实记录确定性计算，"
    "分析文字为模板生成，不代表真实分析结论；请在 backend/.env 配置 DEEPSEEK_API_KEY 后重新生成。"
)


def build_demo_analysis(context: dict) -> dict:
    """无 Key 时的演示分析：observed_facts / paper_evidence / stats 全部来自真实数据，
    解释与建议为明确标注的模板文字。"""
    facts = []
    for exp in context["experiments"]:
        if not exp["runs"]:
            continue
        run = exp["runs"][-1]  # 最新一次运行
        parts = [
            f"{name}={_fmt_number(value)}"
            for name, value in run["results"].items()
        ]
        facts.append({
            "experiment_run_id": run["id"],
            "content": f"实验「{exp['title']}」第 {run['run_no']} 次运行：{'；'.join(parts)}"
            + (f"（备注：{run['notes']}）" if run["notes"] else ""),
        })

    evidence = []
    for card in context["cards"]:
        for sn in card["snippets"][:2]:
            evidence.append({
                "paper_note_id": card["id"],
                "snippet_id": sn["snippet_id"],
                "page": sn["page"],
                "quote": sn["quote"],
                "statement": "（演示模式）该证据来自文献卡片摘录，请人工核对原文",
            })

    summary_lines = []
    for metric in context["stats"].get("metrics", []):
        for row in metric["experiments"]:
            summary_lines.append(
                f"{metric['name']}（{row['title']}）：{row['run_count']} 次运行，"
                f"均值 {row['mean']}，最优 {row['best']}（第 {row['best_run_no']} 次）"
            )
    interpretation = (
        "（演示模式·推测性说明，非真实分析结论）"
        + "后端确定性统计显示：" + "；".join(summary_lines)
        + "。上述数值来自数据库真实记录的计算；"
        + "解释文字为模板生成，请配置 DeepSeek API Key 获得真实分析。"
    )
    uncertainty = (
        "（演示模式）模板生成：样本量、重复次数、潜在混杂因素等"
        "需由真实分析评估；当前内容不代表任何结论。"
    )
    next_experiments = [{
        "objective": "（演示模板）围绕关键变量设计一次对照实验",
        "hypothesis": "（演示模板）调整关键变量后指标变化方向待验证",
        "changed_variables": "（演示模板）待定",
        "fixed_conditions": "（演示模板）保持现有数据划分与评价方式不变",
        "metrics": "（演示模板）沿用当前实验指标",
        "expected_observation": "（演示模板）待定",
        "risks": "（演示模板）请人工评估",
        "estimated_effort": "（演示模板）待定",
        "converted": False,
    }]
    return {
        "observed_facts": facts,
        "paper_evidence": evidence,
        "interpretation": interpretation,
        "hypothesis_status": "insufficient_evidence",
        "uncertainty": uncertainty,
        "next_experiments": next_experiments,
    }


# ═══════════════════════ 生成入口 ═══════════════════════

def generate_analysis(db: Session, question: ResearchQuestion) -> tuple[dict, str, dict]:
    """返回 (sections, source, context)。source: deepseek / demo。

    context 供路由层保存统计快照与数据溯源（与生成时一致）。
    无运行记录 → ResearchAnalysisError；无 Key → 演示模板；
    AI 格式错误自动重试，重试耗尽抛 DeepSeekError。
    """
    context = gather_context(db, question)
    if not context["valid_run_ids"]:
        raise ResearchAnalysisError(NO_DATA_MESSAGE)

    if not DEEPSEEK_API_KEY:
        return build_demo_analysis(context), "demo", context

    client = DeepSeekClient()
    messages = build_messages(context)
    for attempt in range(1 + AI_FORMAT_RETRY_TIMES):
        content = client.chat(messages)
        try:
            data = _extract_json(content)
            sections = validate_analysis(data, context)
            return sections, "deepseek", context
        except ResearchFormatError as e:
            if attempt >= AI_FORMAT_RETRY_TIMES:
                raise DeepSeekError(
                    "AI 返回的分析格式多次校验失败，请稍后重试；"
                    "未配置密钥时可用演示模式查看统计结果"
                ) from e
            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"上一次输出不满足要求（{e}）。请严格按 JSON 结构输出，"
                        "所有引用必须来自给定数据，数值只能引用确定性统计块。"
                    ),
                }
            )
    raise DeepSeekError("分析生成失败，请稍后重试")  # 理论不可达
