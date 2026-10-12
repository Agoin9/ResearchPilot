"""AI 科研计划生成编排（PRD §8）：

1. 组装强约束 Prompt（只输出 JSON 数组，给出完整字段示例与约束）；
2. 容错解析模型输出（剥离代码块围栏、对象/数组双兼容）；
3. 逐字段校验与归一化，格式错误自动重试（附纠错说明）；
4. 未配置 API Key 时进入演示模式，返回预设样例计划。
"""
import json
import re
from datetime import date, timedelta

from app.ai_client import DeepSeekClient, DeepSeekError
from app.config import AI_FORMAT_RETRY_TIMES, AI_MAX_TASKS
from app.schemas import AiPlanTask

PRIORITY_ALIASES = {
    "高": "high",
    "high": "high",
    "中": "medium",
    "medium": "medium",
    "低": "low",
    "low": "low",
}
PRIORITY_LABELS = {"high": "高", "medium": "中", "low": "低"}


class PlanFormatError(Exception):
    """DeepSeek 输出无法通过格式校验（触发重试）。"""


# ═══════════════════════ Prompt 组装 ═══════════════════════

def build_messages(
    topic: str,
    deadline: date,
    weekly_hours: float,
    current_stage: str,
    completed_work: str,
    today: date,
) -> list[dict]:
    weeks = max(round((deadline - today).days / 7, 1), 1)
    total_hours = round(weekly_hours * weeks * 0.85, 1)
    system = (
        "你是资深科研项目规划专家。根据用户提供的科研信息，制定一份可执行的"
        "科研任务计划，覆盖从当前阶段到项目截止日期的完整路径。\n"
        "输出要求（必须严格遵守）：\n"
        "1. 只输出一个 JSON 数组，不要输出任何解释文字、前后缀、Markdown 代码块标记；\n"
        "2. 数组每个元素是一个任务对象，字段如下（示例）：\n"
        '   {"task_id": "T1", "title": "完成文献综述初稿", '
        '"description": "系统梳理智能体行为规划相关文献", '
        '"start_date": "2026-10-13", "due_date": "2026-10-26", '
        '"priority": "高", "expected_deliverable": "文献综述初稿（3000字）", '
        '"dependencies": [], "estimated_hours": 18, '
        '"rationale": "文献调研是当前阶段的首要工作，为方法设计打基础"}\n'
        "3. task_id 为唯一字符串（如 T1、T2…），dependencies 只能引用数组中"
        "已出现的 task_id，没有前置任务则为空数组 [];\n"
        "4. priority 只能是「高」「中」「低」之一；\n"
        "5. estimated_hours 为数字（小时）；\n"
        "6. 任务数量 6~12 个；\n"
        f"7. 所有日期必须在 {today.isoformat()} 到 {deadline.isoformat()} 之间，"
        "且 due_date 不得早于 start_date；\n"
        f"8. 全部任务 estimated_hours 总和约 {total_hours} 小时"
        f"（每周 {weekly_hours:g} 小时 × {weeks:g} 周 × 0.85 缓冲系数）；\n"
        "9. 从当前研究阶段之后开始安排任务，已完成的工作不再重复安排；\n"
        "10. 任务安排要有前后依赖关系，形成一条从当前阶段到论文初稿的推进链路。"
    )
    user = (
        f"研究主题：{topic}\n"
        f"项目截止日期：{deadline.isoformat()}\n"
        f"每周可用小时：{weekly_hours:g} 小时\n"
        f"当前研究阶段：{current_stage}\n"
        f"已完成工作：{completed_work or '无'}"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def build_retry_correction(reason: str) -> str:
    return (
        f"上一次的输出无法解析为合法的 JSON 数组（原因：{reason}）。"
        "请严格只输出 JSON 数组本身，不要包含任何解释文字或代码块标记。"
    )


# ═══════════════════════ 解析与校验 ═══════════════════════

def _extract_json(text: str) -> list | dict:
    """容错提取 JSON：剥代码块围栏，兼容顶层数组与 {"tasks": [...]} 对象。"""
    raw = text.strip()
    # 剥掉 ```json ... ``` 围栏
    fence = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL)
    if fence:
        raw = fence.group(1).strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # 兜底：截取第一个 '[' 到最后一个 ']' 之间的内容
        start, end = raw.find("["), raw.rfind("]")
        if start == -1 or end <= start:
            raise PlanFormatError("输出中找不到 JSON 数组") from None
        try:
            data = json.loads(raw[start : end + 1])
        except json.JSONDecodeError as e:
            raise PlanFormatError(f"JSON 解析失败：{e.msg}") from None
    if isinstance(data, dict):
        data = data.get("tasks", data.get("plan"))
    if not isinstance(data, list):
        raise PlanFormatError("顶层结构不是任务数组")
    return data


def _parse_date(value, field: str) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value.strip())
        except ValueError:
            raise PlanFormatError(f"任务 {field} 不是合法日期（YYYY-MM-DD）") from None
    raise PlanFormatError(f"任务缺少 {field} 字段")


def validate_and_normalize(
    raw_tasks: list, deadline: date, today: date
) -> list[AiPlanTask]:
    """逐字段校验 + 归一化；硬性约束失败抛 PlanFormatError（触发重试）。"""
    if not raw_tasks:
        raise PlanFormatError("任务数组为空")
    if len(raw_tasks) > AI_MAX_TASKS:
        raw_tasks = raw_tasks[:AI_MAX_TASKS]

    tasks: list[AiPlanTask] = []
    seen_ids: set[str] = set()
    for index, raw in enumerate(raw_tasks):
        if not isinstance(raw, dict):
            raise PlanFormatError(f"第 {index + 1} 个任务不是对象")

        title = str(raw.get("title") or "").strip()
        if not title:
            raise PlanFormatError(f"第 {index + 1} 个任务缺少 title")

        # 日期：硬性校验
        start = _parse_date(raw.get("start_date"), "start_date")
        due = _parse_date(raw.get("due_date"), "due_date")
        if due < start:
            raise PlanFormatError(f"任务「{title}」的 due_date 早于 start_date")
        if due > deadline:
            raise PlanFormatError(
                f"任务「{title}」的 due_date（{due}）晚于项目截止日期（{deadline}）"
            )

        # task_id：缺失则补，重复则加后缀
        task_id = str(raw.get("task_id") or f"T{index + 1}").strip()
        base_id, suffix = task_id, 1
        while task_id in seen_ids:
            suffix += 1
            task_id = f"{base_id}-{suffix}"
        seen_ids.add(task_id)

        # 优先级：高/中/低（或英文别名），无法识别归一为「中」
        priority_raw = str(raw.get("priority") or "中").strip().lower()
        priority = PRIORITY_ALIASES.get(priority_raw, "medium")

        # 耗时：非法/缺失归一为 8 小时
        hours = raw.get("estimated_hours", 8)
        try:
            hours = float(hours)
        except (TypeError, ValueError):
            hours = 8.0
        hours = max(min(hours, 1000.0), 0.5)

        # 依赖：只保留数组里存在的 task_id（未知引用忽略）
        deps_raw = raw.get("dependencies") or []
        dependencies = [str(d) for d in deps_raw] if isinstance(deps_raw, list) else []

        tasks.append(
            AiPlanTask(
                task_id=task_id,
                title=title,
                description=str(raw.get("description") or "").strip(),
                start_date=start,
                due_date=due,
                priority=PRIORITY_LABELS[priority],
                expected_deliverable=str(raw.get("expected_deliverable") or "").strip(),
                dependencies=dependencies,
                estimated_hours=hours,
                rationale=str(raw.get("rationale") or "").strip(),
            )
        )

    tasks.sort(key=lambda t: (t.start_date, t.due_date))
    return tasks


# ═══════════════════════ 生成计划（含重试与演示模式） ═══════════════════════

def generate_plan(
    topic: str,
    deadline: date,
    weekly_hours: float,
    current_stage: str,
    completed_work: str,
    today: date,
) -> tuple[str, list[AiPlanTask], str]:
    """返回 (source, tasks, warning)。source: "deepseek" / "demo"。"""
    if not DeepSeekClient().api_key:
        return "demo", build_demo_plan(
            topic, deadline, weekly_hours, current_stage, completed_work, today
        ), (
            "演示模式：未检测到 DeepSeek API Key，已返回预设示例计划。"
            "在 backend/.env 配置 DEEPSEEK_API_KEY 后即可生成真实 AI 计划。"
        )

    client = DeepSeekClient()
    messages = build_messages(
        topic, deadline, weekly_hours, current_stage, completed_work, today
    )
    for attempt in range(1 + AI_FORMAT_RETRY_TIMES):
        content = client.chat(messages)
        try:
            raw = _extract_json(content)
            tasks = validate_and_normalize(raw, deadline, today)
            return "deepseek", tasks, ""
        except PlanFormatError as e:
            if attempt >= AI_FORMAT_RETRY_TIMES:
                raise DeepSeekError(
                    "AI 返回的计划格式多次校验失败，请稍后重试；"
                    "也可以删除 .env 中的密钥使用演示模式，或手动添加任务"
                ) from e
            messages.append({"role": "user", "content": build_retry_correction(str(e))})
    raise DeepSeekError("生成计划失败，请稍后重试")  # 理论不可达


# ═══════════════════════ 演示模式样例计划 ═══════════════════════

def build_demo_plan(
    topic: str,
    deadline: date,
    weekly_hours: float,
    current_stage: str,
    completed_work: str,
    today: date,
) -> list[AiPlanTask]:
    """无 Key 时的预设样例：按科研通用路径生成 6 个任务，日期均匀铺到截止日。"""
    total_days = max((deadline - today).days + 1, 6)
    weeks = max(total_days / 7, 1)
    total_hours = round(weekly_hours * weeks * 0.85, 1)

    # 通用推进链路（从文献调研到论文定稿）
    phases = [
        ("深化文献调研与综述", "围绕「{topic}」系统检索近五年文献，整理研究脉络与关键方法，形成综述初稿", "文献综述初稿", 0.18, "高", "为后续方法设计与论文写作打基础"),
        ("研究方案与方法设计", "基于综述明确研究问题，设计实验/建模方案与评价指标", "研究方案文档（含方法与指标）", 0.16, "高", "先定方案再动手，避免返工"),
        ("核心实验 / 模型实现", "搭建实验环境或实现核心模型，开展多组对比实验", "可复现的实验代码与初步结果", 0.30, "高", "核心工作量最大，预留最多时间"),
        ("数据分析与结果整理", "处理实验数据，绘制图表，提炼主要发现", "结果图表与分析小结", 0.14, "中", "把原始结果转化为论文素材"),
        ("论文初稿撰写", "按学术论文结构完成引言、方法、实验、结论各章节", "论文初稿全文", 0.14, "高", "临近截止，集中时间写作"),
        ("修改润色与定稿", "根据导师/同行意见修改，润色语言，检查格式后定稿", "论文定稿", 0.08, "中", "收尾阶段，保证质量后提交"),
    ]
    cursor = today
    tasks: list[AiPlanTask] = []
    for index, (title, desc, deliverable, ratio, priority, rationale) in enumerate(phases):
        start = cursor
        span = max(round(total_days * ratio), 2)
        cursor = min(start + timedelta(days=span) - timedelta(days=1), deadline)
        tasks.append(
            AiPlanTask(
                task_id=f"T{index + 1}",
                title=title,
                description=desc.format(topic=topic),
                start_date=start,
                due_date=cursor,
                priority=priority,
                expected_deliverable=deliverable,
                dependencies=[f"T{index}"] if index > 0 else [],
                estimated_hours=round(total_hours * ratio, 1),
                rationale=rationale,
            )
        )
        cursor = min(cursor + timedelta(days=1), deadline)
    if current_stage:
        tasks[0].rationale += f"（基于当前阶段：{current_stage}）"
    if completed_work:
        tasks[0].description += f" 已完成工作：{completed_work}，后续任务在此基础上推进。"
    return tasks
