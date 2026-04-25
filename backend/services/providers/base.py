"""
backend/services/providers/base.py
===================================
LLM Provider 基类 - 所有模型提供商的"模板"

这一节讲什么:
1. 什么是抽象类 (ABC)？
2. 为什么要用抽象方法？
3. 策略模式是什么？
"""

from abc import ABC, abstractmethod
from typing import Any


# ============================================================
# 第1部分: 什么是抽象类？
# ============================================================
# 想象你要做奶茶：
# - 你定义了"奶茶店"这个概念（抽象类）
# - 然后有"一点点奶茶店"、"喜茶奶茶店"（具体实现）
#
# "奶茶店"只是一个概念，你不能真的去"奶茶店"点单
# 但你可以在"一点点"或"喜茶"点单
#
# 在代码里同理：
# - LLMProvider 是一个抽象类，定义了"聊天"这个方法
# - MiniMaxProvider、ZhipuProvider 是具体实现
# - 你不能调用 LLMProvider.chat()，但可以调用 MiniMaxProvider.chat()
# ============================================================


# ============================================================
# 第2部分: 策略模式 (Strategy Pattern)
# ============================================================
# 策略模式就是：同一个问题，有多种解决方法，可以互换
#
# 场景：
# - 你要去旅行，可以坐飞机、坐火车、开车
# - 到达目的地这件事是固定的（坐交通工具）
# - 但具体怎么去可以换（策略可以换）
#
# 在我们的代码里：
# - "聊天"这个行为是固定的（调用LLM返回结果）
# - 但具体用哪个模型可以换（MiniMax/Zhipu/Kimi...）
# ============================================================


class LLMProvider(ABC):
    """
    LLM 提供商抽象基类

    所有具体模型（如 MiniMax、Zhipu）都必须继承这个类，
    并实现 chat() 方法。

    为什么用 ABC（抽象基类）？
    - 确保每个 Provider 都有相同的方法
    - 防止忘记实现某个方法
    - 让我们可以"面向接口编程"而不是"面向实现编程"
    """

    def __init__(self, api_key: str, model: str):
        """
        初始化 Provider

        Args:
            api_key: API密钥（从环境变量或配置文件读取）
            model: 模型名称（如 "minimax-t2"）
        """
        self.api_key = api_key
        self.model = model

    @abstractmethod
    def chat(
        self,
        messages: list[dict],
        temperature: float = 0.8,
        max_tokens: int = 3000
    ) -> str:
        """
        发送对话并获取回复

        Args:
            messages: 对话历史，格式如:
                [
                    {"role": "system", "content": "你是一个助手"},
                    {"role": "user", "content": "你好"}
                ]
            temperature: 随机性参数
                - MiniMax: 0-1
                - 其他模型（智谱/Kimi/千问等）: 0-2
            max_tokens: 最大返回token数

        Returns:
            模型生成的回复文本

        Raises:
            Exception: 如果API调用失败
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        返回提供商名称

        Returns:
            提供商名称字符串，如 "MiniMax"
        """
        pass

    @classmethod
    @abstractmethod
    def get_default_model(cls) -> str:
        """
        返回默认模型名称（类方法）

        Returns:
            默认模型名称
        """
        pass

    @classmethod
    @abstractmethod
    def get_supported_models(cls) -> list[dict]:
        """
        返回所有支持的模型列表（类方法）

        Returns:
            模型列表，每项包含 id, name, description
        """
        pass


# ============================================================
# 第3部分: 对话消息格式
# ============================================================
# messages 是 OpenAI 风格的对话格式
#
# 例子：
# messages = [
#     {"role": "system", "content": "你是一个辩论助手"},
#     {"role": "user", "content": "梅西是不是历史最佳？"},
#     {"role": "assistant", "content": "这个问题见仁见智..."},
#     {"role": "user", "content": "骡子比梅西强吗？"}
# ]
#
# role 可以是：
# - system: 系统提示（设定AI角色）
# - user: 用户说的话
# - assistant: AI之前说的话
# ============================================================


def build_messages(
    system_prompt: str,
    user_message: str,
    history: list[dict] | None = None
) -> list[dict]:
    """
    构建对话消息列表

    这是一个工厂函数，帮助构建标准的 messages 格式

    Args:
        system_prompt: 系统提示词（如"你是一个辩论助手"）
        user_message: 用户当前说的话
        history: 可选的对话历史

    Returns:
        标准化的消息列表
    """
    messages = [
        {"role": "system", "content": system_prompt}
    ]

    # 如果有历史对话，加入进去
    if history:
        messages.extend(history)

    # 加入用户当前的消息
    messages.append({"role": "user", "content": user_message})

    return messages