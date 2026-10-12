"""全局配置：数据库路径、风险阈值、输入边界、DeepSeek API 配置。

DeepSeek API Key 等敏感配置放 backend/.env 文件（不进 git、不暴露给前端）。
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# 启动时加载 backend/.env（不存在则忽略）
load_dotenv(BASE_DIR / ".env")

# SQLite 数据库文件（backend/research.db，重启服务数据不丢失）
DATABASE_URL = f"sqlite:///{(BASE_DIR / 'research.db').as_posix()}"

# ── DeepSeek API 配置（仅后端读取，绝不下发前端）─────────────────────────
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_TIMEOUT = float(os.getenv("DEEPSEEK_TIMEOUT", "60"))
# DeepSeek 返回格式错误时的自动重试次数（共 1 + 重试 次尝试）
AI_FORMAT_RETRY_TIMES = 2
# 单个计划最多接受的任务数（防御异常输出）
AI_MAX_TASKS = 30

# ── 风险识别阈值（PRD §9，纯本地规则，不调 AI）──────────────────────────
# 计划时间已过超过该比例，才参与"进度落后"判断
ELAPSED_RATIO_THRESHOLD = 0.30
# 实际进度落后于应达进度超过该百分点数 → 中风险
BEHIND_PROGRESS_THRESHOLD = 20
# 项目整体进度落后该百分点数 → 项目中风险
PROJECT_BEHIND_THRESHOLD = 20
# 中风险任务达到该数量 → 项目中风险
MEDIUM_TASK_COUNT_THRESHOLD = 3
