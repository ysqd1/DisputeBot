"""
backend/services/providers/deepseek.py
======================================
DeepSeek 模型提供商实现

文档: https://api-docs.deepseek.com/zh-cn/

注意:
- temperature 范围是 0-2（标准范围）
- 支持 deepseek-chat 和 deepseek-reasoner 模型
"""

import requests
from .base import LLMProvider


class DeepSeekProvider(LLMProvider):
    """
    DeepSeek 模型提供商

    支持的模型:
    - deepseek-chat (对话模型)
    - deepseek-reasoner (推理模型)
    """

    # DeepSeek API 地址
    API_URL = "https://api.deepseek.com/chat/completions"

    # 支持的模型列表
    SUPPORTED_MODELS = [
        "deepseek-v4-flash",
        "deepseek-chat",
        "deepseek-reasoner"
    ]

    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-v4-flash"
    ):
        """
        初始化 DeepSeek Provider

        Args:
            api_key: DeepSeek API密钥
            model: 模型名称，默认 "deepseek-v4-flash"
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
        调用 DeepSeek API 获取回复

        Args:
            messages: 对话消息列表
            temperature: 随机性 (0-2)
            max_tokens: 最大返回token数
            reasoning_split: 是否分离思考过程（DeepSeek推理模型专用）

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

        # 构建请求体 - DeepSeek API格式
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        # 如果是推理模型且启用 reasoning_split
        if reasoning_split and self.model == "deepseek-reasoner":
            payload["thinking"] = {"type": "enabled"}

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
            message = choice["message"]

            # 如果是推理模型，reasoning_content 在 message 里
            if "reasoning_content" in message and message["reasoning_content"]:
                # 返回推理内容 + 最终回复
                return message["reasoning_content"] + "\n\n" + message["content"]
            else:
                return message["content"]

        except requests.exceptions.Timeout:
            raise Exception("DeepSeek API 请求超时，请稍后重试")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"DeepSeek API 错误: {e.response.status_code} - {str(e)}")
        except KeyError as e:
            raise Exception(f"DeepSeek 响应格式错误: 缺少字段 {str(e)}")
        except Exception as e:
            raise Exception(f"DeepSeek 调用失败: {str(e)}")

    def get_provider_name(self) -> str:
        """
        返回提供商名称
        """
        return "DeepSeek"

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
        return "deepseek-v4-flash"

    @classmethod
    def get_supported_models(cls) -> list[dict]:
        """
        返回所有支持的模型列表（类方法）

        Returns:
            模型列表，每项包含 id, name, description
        """
        return [
            {
                "id": "deepseek-v4-flash",
                "name": "DeepSeek V4 Flash",
                "description": "最新V4旗舰模型，速度快效果好"
            },
            {
                "id": "deepseek-chat",
                "name": "DeepSeek Chat",
                "description": "对话模型（即将停用）"
            },
            {
                "id": "deepseek-reasoner",
                "name": "DeepSeek Reasoner",
                "description": "推理模型，擅长逻辑推理和复杂分析"
            }
        ]
