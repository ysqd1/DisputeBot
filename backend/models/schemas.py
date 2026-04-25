"""
backend/models/schemas.py
=========================
数据模型定义 - 告诉FastAPI"什么样的数据是合法的"

这一节讲什么:
1. Pydantic 是什么？为什么要用它？
2. 怎么定义一个数据模型？
3. 什么是 Field 验证？
"""

from pydantic import BaseModel, Field


# ============================================================
# 第1部分: Pydantic 简介
# ============================================================
# Pydantic 是一个数据验证库。
# 想象一下: 你在填表单，表单要求填"年龄"，你填了"hello"
# Pydantic 会在数据进入你的程序之前就拒绝这个错误数据
#
# 好处:
# - 不用写大量 if age < 0: raise Error 这样的代码
# - 自动类型转换: "18" (字符串) -> 18 (整数)
# - 自动生成API文档
# ============================================================


# ============================================================
# 第2部分: 生成反驳的请求模型
# ============================================================
class GenerateRequest(BaseModel):
    """
    用户发送的请求格式

    每一行冒号后面的内容是Field验证，用来限制数据的范围
    """

    # 对方说的话 - 必填，最少1个字符
    message: str = Field(
        ...,
        min_length=1,
        description="对方喷子说的话"
    )

    # 背景场景 - 必填
    scene: str = Field(
        ...,
        description="背景场景：领域+背景+争论焦点，如'足球 - 国家德比皇马0-4巴萨'"
    )

    # 我的立场 - 必填
    my_stance: str = Field(
        ...,
        description="我的立场，如'皇马球迷'"
    )

    # 对方定位 - 必填
    opponent_profile: str = Field(
        ...,
        description="对方定位，如'巴萨球迷结晶'"
    )

    # 激烈程度 - 1到5，默认3
    aggression: int = Field(
        default=3,
        ge=1,
        le=5,
        description="激烈程度 1-5，1温和讲理，2稍带情绪，3阴阳怪气，4讽刺挖苦，5直接开喷"
    )

    # Temperature随机性 - 0到2，默认0.8
    temperature: float = Field(
        default=0.8,
        ge=0.0,
        le=2.0,
        description="随机性 0-2，越高越有创意，越低越稳定"
    )

    # 目标字数 - 10到2000，0表示不限制
    target_length: int = Field(
        default=0,
        ge=0,
        le=2000,
        description="目标字数，10-2000，0表示不限制"
    )

    # 模型选择 - 必填，提供商ID
    model: str = Field(
        default="minimax",
        description="模型提供商ID：minimax/zhipu/kimi/qwen/deepseek/doubao"
    )

    # 模型变体 - 可选，指定具体使用哪个模型
    # 例如: model="minimax" + model_variant="MiniMax-M2.7"
    # 如果不填，使用提供商的默认模型
    model_variant: str | None = Field(
        default=None,
        description="具体模型名称，如MiniMax-M2.7，不填则用默认"
    )

    # API Key - 可选，如果填了就用这个，覆盖环境变量配置
    api_key: str | None = Field(
        default=None,
        description="API密钥，如果填入则优先使用这个"
    )

    # 自定义API中转站地址 - 仅当 model="custom" 时使用
    base_url: str | None = Field(
        default=None,
        description="自定义API中转站地址，如 https://api.proxy.com/v1"
    )


# ============================================================
# 第3部分: 生成反驳的响应模型
# ============================================================
class GenerateResponse(BaseModel):
    """
    服务器返回给用户的格式
    """

    # 是否成功
    success: bool

    # 生成的反驳内容（成功时有）
    reply: str | None = None

    # 错误信息（失败时有）
    error: str | None = None


# ============================================================
# 第4部分: 模型信息
# ============================================================
class ModelInfo(BaseModel):
    """
    单个模型的详细信息
    """

    # 模型ID，如"minimax"
    id: str

    # 显示名称，如"MiniMax"
    name: str

    # 提供商，如"MiniMax"
    provider: str


# ============================================================
# 第5部分: 可用模型列表响应
# ============================================================
class ModelListResponse(BaseModel):
    """
    返回可用模型列表的响应格式
    """

    # 所有可用的模型
    models: list[ModelInfo]

    # 默认模型
    default: str


# ============================================================
# 第6部分: 健康检查响应
# ============================================================
class HealthResponse(BaseModel):
    """
    健康检查接口的返回格式
    """

    status: str = "ok"
    message: str = "DisputeBot 服务正常运行"