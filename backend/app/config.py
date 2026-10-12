"""全局配置：数据库路径、风险阈值、输入边界。

后续接入 DeepSeek 时，API Key 等敏感配置放 .env 文件（不进 git）。
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# SQLite 数据库文件（backend/research.db，重启服务数据不丢失）
DATABASE_URL = f"sqlite:///{(BASE_DIR / 'research.db').as_posix()}"

# ── 风险识别阈值（PRD §9，纯本地规则，不调 AI）──────────────────────────
# 计划时间已过超过该比例，才参与"进度落后"判断
ELAPSED_RATIO_THRESHOLD = 0.30
# 实际进度落后于应达进度超过该百分点数 → 中风险
BEHIND_PROGRESS_THRESHOLD = 20
# 项目整体进度落后该百分点数 → 项目中风险
PROJECT_BEHIND_THRESHOLD = 20
# 中风险任务达到该数量 → 项目中风险
MEDIUM_TASK_COUNT_THRESHOLD = 3
