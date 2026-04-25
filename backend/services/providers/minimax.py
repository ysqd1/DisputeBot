"""
backend/services/providers/minimax.py
======================================
MiniMax 模型提供商实现

文档: https://platform.minimaxi.com/docs/api-reference/text-openai-api

注意:
- temperature 范围是 0-1（不是0-2）
- content 可能包含 <thinking> 标签，需要完整保留
- 支持 reasoning_split 参数分离思考过程
"""

import requests
from typing import Any
from .base import LLMProvider, build_messages


class MiniMaxProvider(LLMProvider):
    """
    MiniMax 模型提供商

    支持的模型:
    - MiniMax-M2.7 (最新旗舰)
    - MiniMax-M2.5
    - MiniMax-M2.1
    - MiniMax-M2
    - highspeed 版本适合快速响应
    """

    # MiniMax API 地址 (OpenAI兼容格式)
    API_URL = "https://api.minimax.chat/v1/text/chatcompletion_v2"

    # 支持的模型列表
    SUPPORTED_MODELS = [
        "MiniMax-M2.7",
        "MiniMax-M2.7-highspeed",
        "MiniMax-M2.5",
        "MiniMax-M2.5-highspeed",
        "MiniMax-M2.1",
        "MiniMax-M2.1-highspeed",
        "MiniMax-M2"
    ]

    def __init__(
        self,
        api_key: str,
        model: str = "MiniMax-M2.7"
    ):
        """
        初始化 MiniMax Provider

        Args:
            api_key: MiniMax API密钥
            model: 模型名称，默认 "MiniMax-M2.7"
        """
        # 不验证模型是否在列表里，信任用户输入
        # 这样如果厂商新增了模型，用户可以直接输入使用
        super().__init__(api_key, model)

    def chat(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 3000,
        reasoning_split: bool = False
    ) -> str:
        """
        调用 MiniMax API 获取回复

        Args:
            messages: 对话消息列表
            temperature: 随机性 (0-1)，注意MiniMax范围是0-1不是0-2
            max_tokens: 最大返回token数
            reasoning_split: 是否分离思考过程（reasoning_details单独输出）

        Returns:
            模型回复文本，可能包含 <thinking> 标签

        Raises:
            Exception: API调用失败时抛出异常
        """
        # 构建请求头
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 构建请求体 - MiniMax API格式
        # 注意: temperature 范围是 0-1，不是 0-2
        # clamped temperature to [0, 1] if it's out of range
        if temperature > 1.0:
            temperature = 1.0
        elif temperature < 0.0:
            temperature = 0.0

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        # 如果需要分离思考过程（Interleaved Thinking）
        if reasoning_split:
            payload["reasoning_split"] = True

        try:
            # 发送 POST 请求
            response = requests.post(
                self.API_URL,
                headers=headers,
                json=payload,
                timeout=60  # MiniMax模型可能需要更长时间
            )

            # 检查HTTP状态码
            response.raise_for_status()

            # 解析JSON响应
            data = response.json()

            # 提取回复内容
            # MiniMax的响应格式和OpenAI类似
            choice = data["choices"][0]

            # 如果启用了reasoning_split，content在reasoning_details里
            if reasoning_split and "reasoning_details" in choice.get("message", {}):
                # 完整的回复包含思考过程
                return choice["message"]["reasoning_details"]
            else:
                # 普通回复，content可能包含<thinking>标签，要完整保留
                return choice["message"]["content"]

        except requests.exceptions.Timeout:
            raise Exception("MiniMax API 请求超时，请稍后重试")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"MiniMax API 错误: {e.response.status_code} - {str(e)}")
        except KeyError as e:
            raise Exception(f"MiniMax 响应格式错误: 缺少字段 {str(e)}")
        except Exception as e:
            raise Exception(f"MiniMax 调用失败: {str(e)}")

    def get_provider_name(self) -> str:
        """
        返回提供商名称
        """
        return "MiniMax"

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
        return "MiniMax-M2.7"

    @classmethod
    def get_supported_models(cls) -> list[dict]:
        """
        返回所有支持的模型列表（类方法）

        Returns:
            模型列表，每项包含 id, name, description
        """
        return [
            {
                "id": "MiniMax-M2.7",
                "name": "MiniMax-M2.7",
                "description": "最新旗舰模型，效果最好"
            },
            {
                "id": "MiniMax-M2.7-highspeed",
                "name": "MiniMax-M2.7 高速版",
                "description": "速度更快，适合日常使用"
            },
            {
                "id": "MiniMax-M2.5",
                "name": "MiniMax-M2.5",
                "description": "中端模型，性价比高"
            },
            {
                "id": "MiniMax-M2.5-highspeed",
                "name": "MiniMax-M2.5 高速版",
                "description": "速度更快"
            },
            {
                "id": "MiniMax-M2.1",
                "name": "MiniMax-M2.1",
                "description": "轻量级模型，响应快"
            },
            {
                "id": "MiniMax-M2.1-highspeed",
                "name": "MiniMax-M2.1 高速版",
                "description": "速度更快"
            },
            {
                "id": "MiniMax-M2",
                "name": "MiniMax-M2",
                "description": "基础模型"
            }
        ]