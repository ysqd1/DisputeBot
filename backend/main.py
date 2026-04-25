"""
backend/main.py
===============
FastAPI 应用入口

这一节讲什么:
1. FastAPI 应用怎么创建？
2. CORS 是什么？为什么需要配置？
3. 怎么注册路由？
4. 怎么启动应用？
"""

# Windows 终端默认使用 GBK 编码，需要提前配置
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from pathlib import Path
from dotenv import load_dotenv

# 导入路由
from backend.routers.generate import router as generate_router, set_llm_service

# 导入 LLM 服务
from backend.services.llm import LLMService


# ============================================================
# 第1部分: 加载环境变量
# ============================================================
# .env 文件存储 API 密钥等敏感配置
# load_dotenv() 会自动读取项目根目录的 .env 文件
# ============================================================
load_dotenv()


# ============================================================
# 第2部分: 创建 FastAPI 应用
# ============================================================
# FastAPI() 创建了一个 Web 应用实例
# title、description 等信息会显示在 API 文档里
# ============================================================
app = FastAPI(
    title="DisputeBot",
    description="反驳生成器 - 输入喷子言论，AI生成有力反驳",
    version="1.0.0"
)


# ============================================================
# 第3部分: 配置 CORS
# ============================================================
# CORS (Cross-Origin Resource Sharing) 跨域资源共享
#
# 问题：浏览器出于安全考虑，不允许 A 网站的页面请求 B 网站的数据
# 解决：服务器明确告诉浏览器，哪些来源可以访问
#
# 场景：你的前端在 http://127.0.0.1:8000，后端也在 http://127.0.0.1:8000
# 虽然端口相同，但浏览器仍认为是不同"源"（因为协议+域名+端口组合不同）
# 所以需要配置 CORS 允许前端访问
# ============================================================
app.add_middleware(
    CORSMiddleware,
    # 允许所有来源访问（开发环境）
    # 生产环境应该改成具体的域名，如 ["http://localhost:3000"]
    allow_origins=["*"],
    # 允许的方法：GET、POST 等
    allow_methods=["*"],
    # 允许的请求头
    allow_headers=["*"],
)


# ============================================================
# 第4部分: 初始化 LLM 服务
# ============================================================
def init_llm_service():
    """
    初始化 LLM 服务

    从环境变量读取 API 密钥，创建 LLMService 实例
    """
    import json

    # 从环境变量读取 API 密钥
    # os.environ.get("key", "default") 表示获取环境变量，失败则用默认值
    api_keys = {
        "minimax": os.environ.get("MINIMAX_API_KEY", ""),
        "deepseek": os.environ.get("DEEPSEEK_API_KEY", ""),
        "kimi": os.environ.get("KIMI_API_KEY", ""),
        "zhipu": os.environ.get("ZHIPU_API_KEY", ""),
        # 后续可以添加其他模型
        # "qwen": os.environ.get("QWEN_API_KEY", ""),
        # "doubao": os.environ.get("DOUBAO_API_KEY", ""),
    }
    # 调试：打印加载的 keys（不要在生产环境这样做）
    print(f"[DEBUG] Loaded API keys: minimax={'Yes' if api_keys['minimax'] else 'No'}, deepseek={'Yes' if api_keys['deepseek'] else 'No'}")

    # 从环境变量读取自定义中转站配置
    # 格式: CUSTOM_SETTINGS={"api_key": "xxx", "base_url": "https://api.proxy.com/v1", "model": "gpt-4o-mini"}
    custom_settings_str = os.environ.get("CUSTOM_SETTINGS", "")
    custom_settings = {}
    if custom_settings_str:
        try:
            custom_settings = json.loads(custom_settings_str)
        except json.JSONDecodeError:
            print("⚠️ 警告: CUSTOM_SETTINGS 格式错误，请检查 JSON 格式")

    # 检查是否配置了密钥
    missing_keys = [k for k, v in api_keys.items() if not v]
    if missing_keys:
        print(f"⚠️ 警告: 未配置以下模型的 API 密钥: {', '.join(missing_keys)}")
        print("请在 .env 文件中配置，或设置环境变量")

    # 创建 LLM 服务实例
    service = LLMService(api_keys=api_keys, custom_settings=custom_settings)

    # 传递给路由
    set_llm_service(service)

    return service


# ============================================================
# 第5部分: 注册路由
# ============================================================
# include_router() 将路由注册到应用
# prefix="/api" 意味着所有路由都有 /api 前缀
# 比如 generate_router 中的 /generate 变成 /api/generate
# ============================================================
app.include_router(generate_router)


# ============================================================
# 第6部分: 根路径处理 - 返回前端页面
# ============================================================
@app.get("/")
async def root():
    """
    根路径，返回前端页面

    访问 http://127.0.0.1:8000/ 时显示前端页面
    """
    # 获取项目根目录
    # __file__ = D:\create\play\backend\main.py
    # parent = D:\create\play\backend
    # parent.parent = D:\create\play  (项目根目录)
    root_dir = Path(__file__).parent.parent
    frontend_path = root_dir / "frontend" / "index.html"
    return FileResponse(frontend_path)


# ============================================================
# 第7部分: 启动时初始化
# ============================================================
# @app.on_event("startup") 装饰器表示"应用启动时执行"
# ============================================================
@app.on_event("startup")
async def startup_event():
    """
    应用启动时执行
    """
    # Windows 终端默认使用 GBK 编码，如果输出中文或特殊字符可能出错
    # 使用 safe_encode 处理编码问题
    import sys
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    print("=" * 50)
    print("DisputeBot 启动中...")
    init_llm_service()
    print("[OK] LLM 服务已初始化")
    print("=" * 50)


# ============================================================
# 第8部分: 运行应用
# ============================================================
# 这段代码只在直接运行 main.py 时执行
# 如果 main.py 是被 import 的（如 uvicorn 导入），则不会执行
# ============================================================
if __name__ == "__main__":
    import uvicorn

    # 运行服务器
    # host="127.0.0.1" 表示只允许本机访问
    # port=8000 是端口号
    # reload=True 表示代码变化时自动重启（开发环境用）
    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )