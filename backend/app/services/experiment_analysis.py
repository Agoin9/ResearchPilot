"""AI 实验分析编排（v2 核心模块，P4）：

1. 输入：实验的全部真实运行记录（结构化结果 + 备注）+ 实验目标/假设
   + 关联研究问题 + 相关文献卡片的结论摘要（作为领域参照）；
2. DeepSeek 输出严格 JSON：概述（必须引用 run 编号）/ 与假设一致性 /
   与文献对比 / 局限 / 结构化下一步建议；
3. 容错解析 + 格式错误自动重试；
4. 严格防伪造：无运行记录时拒绝生成；无 Key 时不生成 AI 内容（走手工笔记）；
   文献参照与用户数据在 Prompt 中明确隔离。
"""
import json
import re

from app.ai_client import DeepSeekClient, DeepSeekError
from app.config import AI_FORMAT_RETRY_TIMES, DEEPSEEK_API_KEY

MAX_RUNS_IN_CONTEXT = 20   # 上下文最多携带的运行记录条数（超出时按时间截断）
MAX_RESULTS_CHARS = 400    # 单条 run 结果 JSON 截断长度


class AnalysisFormatError(Exception):
    """DeepSeek 输出格式错误（触发重试）。"""


def build_analysis_messages(
    experiment,
    runs: list,
    question_content: str | None,
    card_summaries: list[str],
) -> list[dict]:
    """组装分析上下文（只允许真实数据进入 Prompt）。"""
    run_lines = []
    for run in runs[:MAX_RUNS_IN_CONTEXT]:
        results_text = run.results_json or "{}"
        if len(results_text) > MAX_RESULTS_CHARS:
            results_text = results_text[:MAX_RESULTS_CHARS] + "…（截断）"
        config_text = run.config_json or "{}"
        if len(config_text) > MAX_RESULTS_CHARS:
            config_text = config_text[:MAX_RESULTS_CHARS] + "…（截断）"
        run_lines.append(
            f"[运行 #{run.run_no}（记录 id={run.id}）]\n"
            f"条件：{config_text}\n"
            f"结果：{results_text}\n"
            f"备注：{run.notes or '无'}\n"
            f"开始：{run.started_at or '—'}，结束：{run.finished_at or '—'}"
        )
    if len(runs) > MAX_RUNS_IN_CONTEXT:
        run_lines.append(f"（另有 {len(runs) - MAX_RUNS_IN_CONTEXT} 条更早的运行记录未列出）")

    card_lines = [f"- {s}" for s in card_summaries] if card_summaries else ["无"]
    question_line = question_content or "无"

    system = (
        "你是资深科研实验分析师，帮助研究生解读自己的实验结果。\n"
        "用户会提供：实验信息、该实验的真实运行记录、研究问题、以及若干文献结论"
        "（仅作领域参照）。\n"
        "输出要求（必须严格遵守）：\n"
        "1. 只输出一个 JSON 对象，不要任何解释文字或 Markdown 代码块：\n"
        '   {"summary": "结果概述", "interpretation": "与假设的一致性、趋势与异常解读", '
        '"comparison_with_literature": "与文献参照的对比（无参照则写：无参照文献）", '
        '"limitations": "基于现有数据能说与不能说什么", '
        '"suggestions": [{"type": "new_task/new_experiment/read_literature/modify_design", '
        '"content": "建议内容", "reason": "理由"}]}\n'
        "2. 只能依据用户提供的真实数据，禁止编造不存在的运行结果或数字；\n"
        "3. summary 与 interpretation 中必须明确引用具体运行编号（如「运行 #2」），"
        "结论要能对应到具体记录；\n"
        "4. 文献结论只是参照，必须与用户自己的数据明确区分，"
        "不得把文献数字当成用户的实验结果；\n"
        "5. 数据不足（如只有一次运行）时，在 limitations 中如实说明，"
        "不得过度推断；\n"
        "6. suggestions 给出 1~4 条真正可执行的下一步，type 只能使用给定的四种取值。"
    )
    user = (
        f"实验标题：{experiment.title}\n"
        f"实验目的：{experiment.objective}\n"
        f"实验假设：{experiment.hypothesis or '无'}\n"
        f"关联研究问题：{question_line}\n"
        f"文献参照结论（仅参照）：\n" + "\n".join(card_lines) + "\n"
        f"真实运行记录（共 {len(runs)} 条，按时间排序）：\n" + "\n\n".join(run_lines)
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _extract_json(text: str) -> dict:
    """容错提取 JSON 对象（与 AI 计划一致的策略）。"""
    raw = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL)
    if fence:
        raw = fence.group(1).strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}")
        if start == -1 or end <= start:
            raise AnalysisFormatError("输出中找不到 JSON 对象")
        try:
            data = json.loads(raw[start : end + 1])
        except json.JSONDecodeError as e:
            raise AnalysisFormatError(f"JSON 解析失败：{e.msg}")
    if not isinstance(data, dict):
        raise AnalysisFormatError("顶层结构不是 JSON 对象")
    return data


def validate_analysis(data: dict, runs: list) -> tuple[str, list[dict]]:
    """校验分析输出：返回 (content_markdown, suggestions)。

    硬性校验：summary/interpretation 必须引用至少一个真实 run 编号。
    """
    summary = str(data.get("summary") or "").strip()
    interpretation = str(data.get("interpretation") or "").strip()
    if not summary or not interpretation:
        raise AnalysisFormatError("缺少 summary 或 interpretation 字段")

    combined = summary + interpretation
    run_numbers = [str(run.run_no) for run in runs]
    cited = any(
        f"#{no}" in combined or f"运行 {no}" in combined or f"运行#{no}" in combined
        for no in run_numbers
    )
    if not cited:
        raise AnalysisFormatError("summary/interpretation 未引用任何真实运行编号")

    comparison = str(data.get("comparison_with_literature") or "").strip()
    limitations = str(data.get("limitations") or "").strip()

    sections = [
        ("## 结果概述", summary),
        ("## 与假设的一致性解读", interpretation),
        ("## 与文献参照的对比", comparison or "无参照文献"),
        ("## 局限与不确定性", limitations or "无"),
    ]
    content = "\n\n".join(f"{title}\n\n{body}" for title, body in sections)

    raw_suggestions = data.get("suggestions") or []
    if not isinstance(raw_suggestions, list):
        raise AnalysisFormatError("suggestions 必须是数组")
    suggestions: list[dict] = []
    for item in raw_suggestions[:4]:
        if not isinstance(item, dict):
            continue
        s_type = str(item.get("type") or "")
        s_content = str(item.get("content") or "").strip()
        if s_type not in ("new_task", "new_experiment", "read_literature", "modify_design"):
            continue
        if not s_content:
            continue
        suggestions.append(
            {
                "type": s_type,
                "content": s_content[:1000],
                "reason": str(item.get("reason") or "").strip()[:1000],
                "converted": False,
            }
        )
    if not suggestions:
        raise AnalysisFormatError("suggestions 中没有合法建议")
    return content, suggestions


def generate_analysis(
    experiment,
    runs: list,
    question_content: str | None,
    card_summaries: list[str],
) -> tuple[str, list[dict]]:
    """返回 (content_markdown, suggestions)。AI 失败抛 DeepSeekError。"""
    if not runs:
        raise ValueError("没有运行记录")
    client = DeepSeekClient()
    messages = build_analysis_messages(experiment, runs, question_content, card_summaries)
    for attempt in range(1 + AI_FORMAT_RETRY_TIMES):
        content = client.chat(messages)
        try:
            data = _extract_json(content)
            return validate_analysis(data, runs)
        except AnalysisFormatError as e:
            if attempt >= AI_FORMAT_RETRY_TIMES:
                raise DeepSeekError(
                    "AI 返回的分析格式多次校验失败，请稍后重试；"
                    "也可以改用「手工分析笔记」记录自己的分析"
                ) from e
            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"上一次输出格式不正确（{e}）。请严格只输出 JSON 对象，"
                        "并在 summary/interpretation 中引用具体的运行编号（如「运行 #1」）。"
                    ),
                }
            )
    raise DeepSeekError("分析生成失败，请稍后重试")  # 理论不可达
