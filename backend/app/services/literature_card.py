"""文献研究卡片抽取编排（v2 核心模块）：

1. 输入：已上传文献的全文（截取前 MAX_TEXT_CHARS 字控制成本）；
2. DeepSeek 严格 JSON 抽取结构化字段（研究问题/方法/数据/指标/结果/局限）；
3. 容错解析 + 格式错误自动重试（复用与 AI 计划一致的策略）；
4. 无 Key → 演示模式：返回空字段模板（明确标注，由用户手工填写，不伪造内容）；
5. 抽取不到的内容一律留空——绝不编造。
"""
import json
import re

from app.ai_client import DeepSeekClient, DeepSeekError
from app.config import AI_FORMAT_RETRY_TIMES, DEEPSEEK_API_KEY

MAX_TEXT_CHARS = 15000  # 全文截断长度（中文字符，约 1.5~3 万 token）

CARD_FIELDS = (
    "title", "authors", "year", "research_question", "method",
    "materials_datasets", "metrics", "key_results", "limitations", "relevance",
)


class CardFormatError(Exception):
    """DeepSeek 输出格式错误（触发重试）。"""


def build_card_messages(full_text: str) -> list[dict]:
    """组装抽取 Prompt：严格 JSON、允许字段留空、禁止编造。"""
    excerpt = full_text[:MAX_TEXT_CHARS]
    truncated_note = (
        "（注：全文较长，以下仅为开头部分节选，抽取不完整时字段可留空）"
        if len(full_text) > MAX_TEXT_CHARS
        else ""
    )
    system = (
        "你是严谨的科研文献分析助手。用户会提供一篇论文的文字内容，"
        "请把它整理成一张结构化研究卡片。\n"
        "输出要求（必须严格遵守）：\n"
        "1. 只输出一个 JSON 对象，不要任何解释文字或 Markdown 代码块，字段如下：\n"
        '   {"title": "论文标题", "authors": "作者", "year": "年份", '
        '"research_question": "该文研究的问题", "method": "方法简述", '
        '"materials_datasets": "数据集/材料/实验对象", "metrics": "评价指标", '
        '"key_results": "主要结果（可多条，用分号分隔）", '
        '"limitations": "作者自述或明显的局限", '
        '"relevance": "与我们研究的可能关联（不确定时写待定）"}\n'
        "2. 只能依据提供的文字内容提取，禁止使用你的外部知识补充论文信息；\n"
        "3. 无法从文字中确定的内容，对应字段写空字符串——留空是合法的，"
        "禁止编造或猜测；\n"
        "4. key_results 只写论文报告的结果，不写你的评价。"
    )
    user = f"论文文字内容{truncated_note}：\n{excerpt}"
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
            raise CardFormatError("输出中找不到 JSON 对象")
        try:
            data = json.loads(raw[start : end + 1])
        except json.JSONDecodeError as e:
            raise CardFormatError(f"JSON 解析失败：{e.msg}")
    if not isinstance(data, dict):
        raise CardFormatError("顶层结构不是 JSON 对象")
    return data


def validate_card(data: dict) -> dict:
    """校验并归一化抽取结果：字段缺失/非字符串一律置空字符串（不伪造）。"""
    card: dict = {}
    for field in CARD_FIELDS:
        value = data.get(field, "")
        if not isinstance(value, str):
            value = ""
        card[field] = value.strip()
    return card


def extract_card(full_text: str) -> tuple[dict, str, str]:
    """返回 (card_fields, source, warning)。

    source: deepseek（真实抽取）/ demo（空模板，需手工填写）。
    """
    if not full_text or not full_text.strip():
        raise CardFormatError("文献没有可抽取的文字内容")

    if not DEEPSEEK_API_KEY:
        # 演示模式：返回空字段模板，明确提示用户手工填写
        empty = {field: "" for field in CARD_FIELDS}
        return empty, "demo", (
            "演示模式：未配置 DeepSeek API Key，已创建空卡片模板，请手工填写各字段。"
            "在 backend/.env 配置 DEEPSEEK_API_KEY 后即可一键 AI 抽取。"
        )

    client = DeepSeekClient()
    messages = build_card_messages(full_text)
    for attempt in range(1 + AI_FORMAT_RETRY_TIMES):
        content = client.chat(messages)
        try:
            data = _extract_json(content)
            return validate_card(data), "deepseek", ""
        except CardFormatError as e:
            if attempt >= AI_FORMAT_RETRY_TIMES:
                raise DeepSeekError(
                    "AI 返回的卡片格式多次校验失败，请稍后重试；"
                    "也可以手工创建研究卡片"
                ) from e
            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"上一次输出格式不正确（{e}）。请严格只输出一个 JSON 对象，"
                        "包含全部 10 个字段，无法确定的内容写空字符串。"
                    ),
                }
            )
    raise DeepSeekError("卡片抽取失败，请稍后重试")  # 理论不可达
