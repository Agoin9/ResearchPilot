"""文献处理服务（文献精读与引用溯源助手）：

1. PDF 文字提取（pypdf）+ 扫描版检测；
2. 按段落切块（每段约 500~800 字）；
3. 关键词检索（jieba 分词打分）取最相关 5 个片段；
4. 问答编排：5 个片段 + 问题 → DeepSeek（只依据片段回答，返回严格 JSON，
   格式错误自动重试）；无 Key 时进入演示模式。
"""
import json
import re
from datetime import date
from io import BytesIO

import jieba
from pypdf import PdfReader

from app.ai_client import DeepSeekClient, DeepSeekError
from app.config import AI_FORMAT_RETRY_TIMES, DEEPSEEK_API_KEY
from app.schemas import CitationOut

CHUNK_MIN_LEN = 500
CHUNK_MAX_LEN = 800
TOP_K = 5
MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20MB
# 每页提取字数低于该值时判定为扫描版（无文字层）
SCANNED_CHARS_PER_PAGE = 30

# 提问中的停用词（不参与关键词匹配）
QUESTION_STOPWORDS = {
    "什么", "哪些", "为什么", "怎么", "如何", "请问", "一下", "这个", "那个",
    "吗", "呢", "的", "了", "是", "在", "有", "与", "和", "以及", "相关", "问题",
    "是否", "有没有", "请", "帮我", "介绍",
}


class DocumentServiceError(Exception):
    """用户可读的文献处理错误（路由层转 400）。"""


class PlanFormatError(Exception):
    """DeepSeek 输出格式错误（触发重试）。"""


# ═══════════════════════ PDF 提取与切块 ═══════════════════════

def extract_pdf_text(data: bytes) -> tuple[str, bool]:
    """返回 (全文, 是否疑似扫描版)。解析失败抛 DocumentServiceError。"""
    if len(data) > MAX_UPLOAD_BYTES:
        raise DocumentServiceError("文件过大，最大支持 20MB")
    try:
        reader = PdfReader(BytesIO(data))
    except Exception:
        raise DocumentServiceError("无法解析该文件，请确认上传的是有效的 PDF 文件")
    if reader.is_encrypted:
        raise DocumentServiceError("该 PDF 已加密，无法提取文字")

    pages_text: list[str] = []
    for page in reader.pages:
        try:
            pages_text.append(page.extract_text() or "")
        except Exception:
            pages_text.append("")
    full_text = "\n".join(pages_text).strip()
    scanned = len(reader.pages) > 0 and len(full_text) < len(reader.pages) * SCANNED_CHARS_PER_PAGE
    return full_text, scanned


def chunk_text(text: str, min_len: int = CHUNK_MIN_LEN, max_len: int = CHUNK_MAX_LEN) -> list[str]:
    """按段落切块：尽量在段落边界断开，每段约 500~800 字（尾部允许更短）。"""
    paragraphs = [p.strip() for p in re.split(r"\n+", text) if p.strip()]
    if not paragraphs:
        return []

    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        # 单个段落过长：先按句号/分号切到 max_len 以内
        while len(para) > max_len:
            cut = para[:max_len]
            idx = max(cut.rfind("。"), cut.rfind("；"), cut.rfind(". "), cut.rfind(". "))
            if idx < min_len:
                idx = max_len - 1
            chunks.append(para[: idx + 1].strip())
            para = para[idx + 1 :].strip()

        if not current:
            current = para
        elif len(current) + len(para) + 1 <= max_len:
            current = f"{current}\n{para}"
        else:
            chunks.append(current)
            current = para
    if current:
        chunks.append(current)
    return [c for c in chunks if c.strip()]


# ═══════════════════════ 关键词检索 ═══════════════════════

def extract_keywords(question: str) -> list[str]:
    """jieba 分词取关键词（去掉停用词与单字），保持顺序去重。"""
    words = [
        w.strip()
        for w in jieba.cut(question)
        if len(w.strip()) > 1 and w.strip() not in QUESTION_STOPWORDS
    ]
    return list(dict.fromkeys(words))


def search_chunks(question: str, chunks: list) -> list:
    """按关键词命中打分，返回最相关的前 TOP_K 个切片（按相关度降序）。

    chunks: DocChunk ORM 列表；返回同样类型的有序列表。
    """
    keywords = extract_keywords(question)
    if not keywords or not chunks:
        return chunks[:TOP_K]

    scored: list[tuple[int, object]] = []
    for chunk in chunks:
        score = sum(chunk.content.count(kw) * max(len(kw), 2) for kw in keywords)
        if score > 0:
            scored.append((score, chunk))
    scored.sort(key=lambda item: item[0], reverse=True)
    top = [chunk for _, chunk in scored[:TOP_K]]
    if not top:
        # 没有任何关键词命中：兜底返回文档前 5 个切片
        return chunks[:TOP_K]
    return top


# ═══════════════════════ 问答编排（DeepSeek / 演示模式） ═══════════════════════

def build_qa_messages(question: str, top_chunks: list) -> list[dict]:
    chunk_lines = []
    for chunk in top_chunks:
        chunk_lines.append(f"[片段 {chunk.chunk_index}]\n{chunk.content}")
    system = (
        "你是严谨的文献阅读助手。用户会提供若干文献片段和一个问题。\n"
        "回答规则（必须严格遵守）：\n"
        "1. 只能依据提供的文献片段回答，禁止使用你的外部知识；\n"
        "2. 如果片段中找不到答案，answer 中明确写「文献片段中未提及该内容」；\n"
        "3. 引用必须来自片段：citations 中的 chunk_index 只能是片段编号，"
        "quote 必须逐字摘自对应片段原文（不超过 60 字）；\n"
        "4. 只输出一个 JSON 对象，不要任何解释文字或 Markdown 代码块，格式：\n"
        '{"answer": "回答正文", "citations": [{"chunk_index": 1, "quote": "原文原句"}], '
        '"confidence": 0.85}\n'
        "5. confidence 为 0~1 的数字，表示答案的可信程度（依据片段覆盖问题的程度估计）。"
    )
    user = "文献片段：\n" + "\n\n".join(chunk_lines) + f"\n\n问题：{question}"
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _extract_json(text: str) -> dict:
    """容错提取 JSON 对象（复用与 AI 计划一致的策略）。"""
    raw = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL)
    if fence:
        raw = fence.group(1).strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}")
        if start == -1 or end <= start:
            raise PlanFormatError("输出中找不到 JSON 对象")
        try:
            data = json.loads(raw[start : end + 1])
        except json.JSONDecodeError as e:
            raise PlanFormatError(f"JSON 解析失败：{e.msg}")
    if not isinstance(data, dict):
        raise PlanFormatError("顶层结构不是 JSON 对象")
    return data


def parse_qa_answer(text: str, top_chunks: list) -> tuple[str, list[CitationOut], float]:
    """解析并校验 DeepSeek 返回的 {answer, citations, confidence}。"""
    data = _extract_json(text)
    answer = str(data.get("answer") or "").strip()
    if not answer:
        raise PlanFormatError("缺少 answer 字段")

    valid_indexes = {c.chunk_index for c in top_chunks}
    citations: list[CitationOut] = []
    raw_citations = data.get("citations") or []
    if not isinstance(raw_citations, list) or not raw_citations:
        raise PlanFormatError("citations 必须是非空数组")
    for item in raw_citations:
        if not isinstance(item, dict):
            continue
        try:
            chunk_index = int(item.get("chunk_index"))
        except (TypeError, ValueError):
            continue
        if chunk_index not in valid_indexes:
            continue  # 引用不在给定片段里 → 丢弃（不得编造）
        quote = str(item.get("quote") or "").strip()
        if not quote:
            chunk = next(c for c in top_chunks if c.chunk_index == chunk_index)
            quote = chunk.content[:60]
        citations.append(CitationOut(chunk_index=chunk_index, quote=quote[:120]))
    if not citations:
        raise PlanFormatError("citations 中没有引用任何给定片段")

    try:
        confidence = float(data.get("confidence", 0.5))
    except (TypeError, ValueError):
        confidence = 0.5
    confidence = max(0.0, min(confidence, 1.0))
    return answer, citations, confidence


def answer_question(question: str, chunks: list) -> tuple[str, list[CitationOut], float, str]:
    """返回 (answer, citations, confidence, source)。source: deepseek / demo。"""
    top_chunks = search_chunks(question, chunks)

    # 演示模式：无 Key 时直接用检索结果拼答案
    if not DEEPSEEK_API_KEY:
        lines = [
            "（演示模式）未配置 DeepSeek API Key，以下为关键词匹配到的最相关片段，"
            "请结合原文片段阅读：",
        ]
        for chunk in top_chunks:
            lines.append(f"\n【片段 {chunk.chunk_index}】{chunk.content[:120]}…")
        answer = "\n".join(lines)
        citations = [
            CitationOut(chunk_index=c.chunk_index, quote=c.content[:60])
            for c in top_chunks
        ]
        confidence = 0.3
        return answer, citations, confidence, "demo"

    client = DeepSeekClient()
    messages = build_qa_messages(question, top_chunks)
    for attempt in range(1 + AI_FORMAT_RETRY_TIMES):
        content = client.chat(messages)
        try:
            answer, citations, confidence = parse_qa_answer(content, top_chunks)
            return answer, citations, confidence, "deepseek"
        except PlanFormatError as e:
            if attempt >= AI_FORMAT_RETRY_TIMES:
                raise DeepSeekError(
                    "AI 回答格式多次校验失败，请稍后重试；"
                    "也可以删除 .env 中的密钥使用演示模式"
                ) from e
            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"上一次输出格式不正确（{e}）。请严格只输出 JSON 对象："
                        '{"answer": "...", "citations": [{"chunk_index": 1, '
                        '"quote": "原文原句"}], "confidence": 0~1}，'
                        "citations 只能引用给定片段的编号。"
                    ),
                }
            )
    raise DeepSeekError("回答失败，请稍后重试")  # 理论不可达
