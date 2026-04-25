"""
backend/routers/generate.py
===========================
API 路由 - 处理前端请求

这一节讲什么:
1. FastAPI 路由怎么写？
2. 怎么获取请求中的数据？
3. 怎么返回 JSON 响应？
"""

from fastapi import APIRouter, HTTPException

# 从上级目录导入数据模型
import sys
sys.path.append("..")
from backend.models.schemas import (
    GenerateRequest,
    GenerateResponse,
    ModelListResponse,
    ModelInfo
)
from backend.services.llm import generate_reply, LLMService


# ============================================================
# 第1部分: 创建路由
# ============================================================
# APIRouter 就像是"路由器"
# 它知道哪些 URL 应该由哪些函数处理
#
# 比如：
# - POST /api/generate → generate_reply_handler()
# - GET /api/models → get_models_handler()
# ============================================================

router = APIRouter(prefix="/api", tags=["生成反驳"])

# 全局 LLM 服务实例（在应用启动时创建）
llm_service: LLMService | None = None


def set_llm_service(service: LLMService):
    """
    设置 LLM 服务实例（由 main.py 调用）

    Args:
        service: LLMService 实例
    """
    global llm_service
    llm_service = service


# ============================================================
# 第2部分: 生成反驳接口
# ============================================================
@router.post("/generate", response_model=GenerateResponse)
async def generate_reply_handler(req: GenerateRequest):
    """
    生成反驳内容

    这是一个 POST 接口，前端发送 JSON 请求，
    后端返回生成的反驳内容。

    请求格式 (GenerateRequest):
    {
        "message": "对方说的话",
        "scene": "背景场景",
        "my_stance": "我的立场",
        "opponent_profile": "对方定位",
        "aggression": 7,
        "temperature": 0.8,
        "target_length": 200,
        "model": "minimax"
    }

    响应格式 (GenerateResponse):
    {
        "success": true,
        "reply": "生成的反驳内容"
    }
    或
    {
        "success": false,
        "error": "错误信息"
    }
    """
    # 检查 LLM 服务是否已初始化
    if llm_service is None:
        raise HTTPException(
            status_code=500,
            detail="LLM服务未初始化，请检查配置"
        )

    try:
        # 调用 generate_reply 函数生成反驳
        reply = generate_reply(
            llm_service=llm_service,
            model=req.model,
            model_variant=req.model_variant,
            message=req.message,
            scene=req.scene,
            my_stance=req.my_stance,
            opponent_profile=req.opponent_profile,
            aggression=req.aggression,
            temperature=req.temperature,
            target_length=req.target_length,
            api_key=req.api_key,
            base_url=req.base_url
        )

        # 返回成功响应
        return GenerateResponse(
            success=True,
            reply=reply
        )

    except ValueError as e:
        # 参数错误（如模型不支持、API密钥未配置）
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # 其他错误（如 API 调用失败）
        # 不暴露内部错误细节给用户
        return GenerateResponse(
            success=False,
            error=f"生成失败: {str(e)}"
        )


# ============================================================
# 第3部分: 获取可用模型列表
# ============================================================
@router.get("/models", response_model=ModelListResponse)
async def get_models_handler():
    """
    获取可用的模型列表

    这是一个 GET 接口，返回所有支持的模型。

    响应格式:
    {
        "models": [
            {"id": "minimax", "name": "MiniMax", "provider": "MiniMax"},
            ...
        ],
        "default": "minimax"
    }
    """
    if llm_service is None:
        raise HTTPException(
            status_code=500,
            detail="LLM服务未初始化"
        )

    # 获取提供商列表
    providers = llm_service.get_available_providers()

    return ModelListResponse(
        models=[ModelInfo(**p) for p in providers],
        default="minimax"
    )


# ============================================================
# 第3.5部分: 获取模型变体列表
# ============================================================
@router.get("/model-variants")
async def get_model_variants_handler(provider: str | None = None):
    """
    获取模型变体列表

    如果指定了 provider，返回该提供商的所有模型
    如果没有指定，返回所有模型

    响应格式:
    {
        "variants": [
            {"provider": "minimax", "id": "MiniMax-M2.7", "name": "MiniMax-M2.7", "description": "..."},
            ...
        ]
    }
    """
    if llm_service is None:
        raise HTTPException(
            status_code=500,
            detail="LLM服务未初始化"
        )

    if provider:
        # 返回指定提供商的模型变体
        variants = llm_service.get_provider_variants(provider)
    else:
        # 返回所有模型变体
        variants = llm_service.get_all_model_variants()

    return {"variants": variants}


# ============================================================
# 第4部分: 健康检查
# ============================================================
@router.get("/health")
async def health_check():
    """
    健康检查接口

    用于检查服务是否正常运行
    """
    return {"status": "ok", "message": "DisputeBot 服务正常运行"}