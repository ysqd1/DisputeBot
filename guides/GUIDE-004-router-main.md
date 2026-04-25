# GUIDE-004: API 路由与 FastAPI 入口

## 这块代码做了什么

1. **API 路由** (`generate.py`)
   - 处理前端请求
   - 返回 JSON 响应

2. **FastAPI 应用入口** (`main.py`)
   - 创建 FastAPI 应用
   - 配置 CORS
   - 注册路由
   - 初始化 LLM 服务

## 核心知识点

### 1. APIRouter 是什么？

```python
router = APIRouter(prefix="/api")

@router.post("/generate")
async def handler(req: GenerateRequest):
    return {"result": "ok"}
```

`APIRouter` 就像一个"小路由器"，它知道：
- `/generate` 这个路径应该由哪个函数处理
- 用 `prefix="/api"` 给所有路由加前缀

### 2. 路由的路径

```python
# generate.py
router = APIRouter(prefix="/api")  # 前缀
@router.post("/generate")           # 路径

# 最终路径 = prefix + 路径 = /api/generate
```

### 3. 什么是 CORS？

CORS = Cross-Origin Resource Sharing（跨域资源共享）

**问题场景**：
```
你的前端: http://127.0.0.1:8000/index.html
你的后端: http://127.0.0.1:8000/api/generate

虽然都在 localhost:8000，但浏览器认为这是不同的"源"
（源 = 协议 + 域名 + 端口）
```

**解决**：服务器告诉浏览器"允许这个源访问"

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源（开发环境）
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],   # 允许所有请求头
)
```

### 4. @app.on_event("startup")

```python
@app.on_event("startup")
async def startup_event():
    init_llm_service()
```

这个装饰器表示"应用启动时自动执行这个函数"。

### 5. if __name__ == "__main__"

```python
if __name__ == "__main__":
    uvicorn.run("backend.main:app", ...)
```

- `__name__` 是 Python 内置变量
- 当直接运行这个文件时，`__name__ == "__main__"`
- 当被 import 时，`__name__` 是文件名（如 `"backend.main"`）

这让你可以：
- 直接运行 `python backend/main.py` 启动服务器
- 或用 `uvicorn backend.main:app --reload` 启动

## 代码逐段解读

### generate.py - 路由定义

```python
router = APIRouter(prefix="/api", tags=["生成反驳"])
```

- `prefix="/api"` 所有路由都有 /api 前缀
- `tags=["生成反驳"]` 在 API 文档里分组显示

### generate.py - 生成反驳接口

```python
@router.post("/generate", response_model=GenerateResponse)
async def generate_reply_handler(req: GenerateRequest):
```

- `@router.post` 这是一个 POST 请求
- `response_model=GenerateResponse` 自动把返回值转成 JSON
- `req: GenerateRequest` 自动验证请求数据

### generate.py - 错误处理

```python
try:
    reply = generate_reply(...)
    return GenerateResponse(success=True, reply=reply)
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    return GenerateResponse(success=False, error=str(e))
```

- `ValueError` → 400 错误（用户输入问题）
- 其他 `Exception` → 返回 success=False（不暴露内部错误）

### main.py - CORS 配置

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该改成具体域名
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### main.py - LLM 服务初始化

```python
def init_llm_service():
    # 从环境变量读取多个模型的 API 密钥
    api_keys = {
        "minimax": os.environ.get("MINIMAX_API_KEY", ""),
        "deepseek": os.environ.get("DEEPSEEK_API_KEY", ""),
        "kimi": os.environ.get("KIMI_API_KEY", ""),
        "zhipu": os.environ.get("ZHIPU_API_KEY", ""),
    }

    # 自定义中转站配置（JSON 格式）
    # 格式: {"api_key": "xxx", "base_url": "https://...", "model": "gpt-4o-mini"}
    custom_settings_str = os.environ.get("CUSTOM_SETTINGS", "")
    custom_settings = json.loads(custom_settings_str) if custom_settings_str else {}

    service = LLMService(api_keys=api_keys, custom_settings=custom_settings)
    set_llm_service(service)
    return service
```

读取环境变量，创建 LLM 服务，传递给路由。
支持多模型配置和自定义中转站设置。

## 启动命令

```bash
# 方式1: 直接运行
cd D:\create\play
disputebot-venv\Scripts\python backend\main.py

# 方式2: 用 uvicorn（推荐，支持热重载）
disputebot-venv\Scripts\uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

启动后访问：
- http://127.0.0.1:8000/ - 欢迎页面
- http://127.0.0.1:8000/docs - API 文档（可以在这里测试）

---

下一步是创建前端页面，准备好了吗？