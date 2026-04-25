"""
backend/services/providers/kimi.py
==================================
Kimi (Moonshot) 模型提供商实现

文档: https://platform.kimi.ai/docs

注意:
- temperature 范围是 0-1
- 支持 kimi-k2.5 及思维链模式
- API 使用 OpenAI 兼容格式
"""

import requests
from .base import LLMProvider


class KimiProvider(LLMProvider):
    """
    Kimi (Moonshot) 模型提供商

    支持的模型:
    - kimi-k2.5 (最新旗舰)
    - kimi-k2-turbo-preview (高速版)
    """

    # Kimi API 地址 (OpenAI兼容格式)
    API_URL = "https://api.moonshot.ai/v1/chat/completions"

    # 支持的模型列表
    SUPPORTED_MODELS = [
        "kimi-k2.5",
        "kimi-k2-turbo-preview"
    ]

    def __init__(
        self,
        api_key: str,
        model: str = "kimi-k2.5"
    ):
        """
        初始化 Kimi Provider

        Args:
            api_key: Kimi API密钥
            model: 模型名称，默认 "kimi-k2.5"
        """
        super().__init__(api_key, model)

    def chat(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 3000,
        reasoning_split: bool = False
    ) -> str:
        """
        调用 Kimi API 获取回复

        Args:
            messages: 对话消息列表
            temperature: 随机性 (0-1)
            max_tokens: 最大返回token数
            reasoning_split: 是否分离思考过程

        Returns:
            模型回复文本

        Raises:
            Exception: API调用失败时抛出异常
        """
        # 构建请求头
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 构建请求体 - Kimi API格式 (OpenAI兼容)
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        # 如果启用 reasoning_split，关闭思维链
        if reasoning_split:
            payload["extra_body"] = {
                "thinking": {"type": "disabled"}
            }

        try:
            # 发送 POST 请求
            response = requests.post(
                self.API_URL,
                headers=headers,
                json=payload,
                timeout=60
            )

            # 检查HTTP状态码
            response.raise_for_status()

            # 解析JSON响应
            data = response.json()

            # 提取回复内容
            choice = data["choices"][0]
            return choice["message"]["content"]

        except requests.exceptions.Timeout:
            raise Exception("Kimi API 请求超时，请稍后重试")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"Kimi API 错误: {e.response.status_code} - {str(e)}")
        except KeyError as e:
            raise Exception(f"Kimi 响应格式错误: 缺少字段 {str(e)}")
        except Exception as e:
            raise Exception(f"Kimi 调用失败: {str(e)}")

    def get_provider_name(self) -> str:
        """
        返回提供商名称
        """
        return "Kimi"

    def get_model_name(self) -> str:
        """
        返回当前使用的模型名称
        """
        return self.model

    @classmethod
    def get_default_model(cls) -> str:
        """
        返回默认模型名称（类方法）

        Returns:
            默认模型名称
        """
        return "kimi-k2.5"

    @classmethod
    def get_supported_models(cls) -> list[dict]:
        """
        返回所有支持的模型列表（类方法）

        Returns:
            模型列表，每项包含 id, name, description
        """
        return [
            {
                "id": "kimi-k2.5",
                "name": "Kimi K2.5",
                "description": "最新旗舰模型，效果最好"
            },
            {
                "id": "kimi-k2-turbo-preview",
                "name": "Kimi K2 Turbo",
                "description": "高速版，响应更快"
            }
        ]
