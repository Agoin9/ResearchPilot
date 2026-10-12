"""DeepSeek API 客户端：只负责 HTTP 调用，把各类失败翻译成用户可读的中文错误。

API Key 只在本模块（后端）使用，绝不出现在任何接口响应里。
"""
import httpx

from app.config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
    DEEPSEEK_TIMEOUT,
)


class DeepSeekError(Exception):
    """带用户可读中文提示的 AI 调用错误（由路由层转成 502 返回前端）。"""


class DeepSeekClient:
    def __init__(
        self,
        api_key: str = DEEPSEEK_API_KEY,
        base_url: str = DEEPSEEK_BASE_URL,
        model: str = DEEPSEEK_MODEL,
        timeout: float = DEEPSEEK_TIMEOUT,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout = timeout

    def chat(self, messages: list[dict]) -> str:
        """发送对话请求，返回模型输出的文本内容。

        失败时抛出 DeepSeekError（message 为可直接展示给用户的中文提示）：
        网络超时 / 连接失败 / Key 无效 / 余额不足 / 限流 / 服务端错误。
        """
        # 兼容两种配置写法：base 主机（https://api.deepseek.com）或完整端点
        if self.base_url.endswith("/chat/completions"):
            url = self.base_url
        else:
            url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,  # 拆解求稳定（PRD §8.1）
        }
        try:
            response = httpx.post(
                url, json=payload, headers=headers, timeout=self.timeout
            )
        except httpx.TimeoutException:
            raise DeepSeekError(
                f"DeepSeek 响应超时（{self.timeout:g} 秒），请稍后重试"
                "（可在 backend/.env 调大 DEEPSEEK_TIMEOUT）"
            ) from None
        except httpx.HTTPError:
            raise DeepSeekError(
                "无法连接 DeepSeek API，请检查网络是否可访问 api.deepseek.com"
            ) from None

        if response.status_code == 200:
            try:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except (ValueError, KeyError, IndexError, TypeError):
                raise DeepSeekError("DeepSeek 返回了无法解析的响应，请稍后重试") from None

        # ── 非 200：按状态码给明确提示 ──
        status = response.status_code
        if status == 401:
            raise DeepSeekError(
                "DeepSeek API Key 无效或已过期，请检查 backend/.env 中的 DEEPSEEK_API_KEY"
            )
        if status == 402:
            raise DeepSeekError("DeepSeek 账户余额不足，请充值后重试")
        if status == 429:
            raise DeepSeekError("DeepSeek 请求被限流，请稍后重试")
        if status >= 500:
            raise DeepSeekError(
                f"DeepSeek 服务暂时不可用（HTTP {status}），请稍后重试"
            )
        raise DeepSeekError(f"DeepSeek 请求被拒绝（HTTP {status}），请稍后重试")
