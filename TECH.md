# 反驳生成器 - 技术文档

> 本文档是技术实现指南，需求分析见 `SPEC.md`

---

## 1. 技术栈选择

### 1.1 后端框架: FastAPI

| 维度 | 选择 | 原因 |
|------|------|------|
| 框架 | FastAPI | 中文资料丰富、自动文档生成、类型提示完善、异步性能好 |
| 语言 | Python 3.10+ | 学习曲线低，AI模型API支持完善 |
| ASGI服务器 | Uvicorn | FastAPI官方推荐，Windows兼容 |
| 异步HTTP | requests (sync) / httpx (async) | Python最常用的HTTP客户端 |

**为什么不是 Django？**
- Django太重，对于这个简单项目不需要
- Django的ORM和后台对我们的场景没有意义

**为什么不是 Flask？**
- Flask是同步的，FastAPI的异步性能更好
- FastAPI自动生成API文档，比Flask更方便调试

### 1.2 前端: 原生 HTML + CSS + JavaScript

| 维度 | 选择 | 原因 |
|------|------|------|
| HTML | HTML5 | 语义化标签，无需框架 |
| CSS | 原生CSS + CSS变量 | 简单够用，无需预处理 |
| JS | Vanilla JS (ES6+) | 不需要React/Vue等框架 |
| 打包 | 无 | 单文件直接运行 |

**为什么不用 React/Vue？**
- 项目简单，不需要状态管理
- 减少构建步骤，直接浏览器打开
- 降低学习成本，专注后端

### 1.3 AI模型支持

| 模型 | API格式 | 默认模型 | 备注 |
|------|---------|---------|------|
| MiniMax | OpenAI兼容 | MiniMax-M2.7 | 国内可用 |
| DeepSeek | OpenAI兼容 | deepseek-v4-flash | 最新V4模型 |
| KIMI (Moonshot) | OpenAI兼容 | kimi-k2.5 | 最新K2.5模型 |
| 智谱 GLM | OpenAI兼容 | glm-5.1 | 最新GLM-5模型 |
| 自定义中转站 | OpenAI兼容 | - | 支持任意OpenAI兼容API |

**统一接口设计**: 所有模型都遵循 OpenAI 的 `chat/completions` 格式，便于切换。

### 1.4 开发工具链

| 工具 | 用途 | Windows说明 |
|------|------|-------------|
| Python 3.10+ | 运行环境 | 使用Anaconda |
| pip / pip3 | 包管理 | Python自带 |
| uvicorn | ASGI服务器 | `pip install uvicorn` |
| Git | 版本控制 | 安装Git for Windows |
| VSCode / PyCharm | 编辑器 | 推荐VSCode |

---

## 2. 项目结构

```
D:\create\play\
│
├── backend/                    # 后端项目目录
│   ├── __init__.py            # Python包标识
│   ├── main.py                # FastAPI应用入口
│   │
│   ├── routers/               # 路由目录
│   │   ├── __init__.py
│   │   └── generate.py        # 生成反驳的API
│   │
│   ├── services/              # 业务逻辑目录
│   │   ├── __init__.py
│   │   ├── llm.py             # LLM统一接口
│   │   └── providers/         # 模型提供商
│   │       ├── __init__.py
│   │       ├── base.py        # 基类
│   │       ├── minimax.py     # MiniMax
│   │       ├── deepseek.py    # DeepSeek
│   │       ├── kimi.py        # KIMI
│   │       └── zhipu.py       # 智谱GLM
│   │
│   └── models/                # 数据模型目录
│       ├── __init__.py
│       └── schemas.py         # Pydantic模型定义
│
├── frontend/                   # 前端项目目录
│   └── index.html             # 单页应用（支持中英文切换）
│
├── guides/                     # 学习指南目录
│   └── GUIDE-001-xxx.md       # 代码讲解文档
│
├── .env                        # 环境变量配置
├── .env.example               # 环境变量示例
├── requirements.txt          # Python依赖
├── SPEC.md                   # 需求分析
└── TECH.md                   # 本文档（技术实现）
```

### 2.1 目录结构说明

```
backend/
├── main.py          # FastAPI实例创建、CORS配置、路由注册
├── routers/         # 存放API路由，类似Flask的Blueprint
├── services/        # 存放业务逻辑，如LLM调用
└── models/          # 存放数据模型，用Pydantic做验证

frontend/
└── index.html       # 纯前端单页应用

guides/
└── GUIDE-001-xxx.md # 配套学习文档
```

---

## 3. 数据模型

### 3.1 后端数据模型 (Pydantic)

```python
# backend/models/schemas.py

class GenerateRequest(BaseModel):
    """生成反驳的请求模型"""
    message: str              # 对方说的话
    scene: str                # 背景场景：领域+背景+争论焦点
    my_stance: str            # 我的立场
    opponent_profile: str     # 对方定位
    aggression: int          # 激烈程度 1-5
    temperature: float       # 随机性 0-2
    target_length: int       # 目标字数，0=不限制
    model: str               # 供应商ID：minimax/deepseek/kimi/zhipu/custom
    model_variant: str | None  # 具体模型名称，留空用默认
    api_key: str | None       # API密钥，前端填写则优先使用
    base_url: str | None      # 自定义中转站地址，仅model=custom时用

class GenerateResponse(BaseModel):
    """生成反驳的响应模型"""
    success: bool
    reply: str                # 生成的反驳内容
    error: str | None         # 错误信息

class ModelInfo(BaseModel):
    """模型信息"""
    id: str                   # 模型标识
    name: str                 # 显示名称
    provider: str             # 提供商

class ModelListResponse(BaseModel):
    """可用模型列表响应"""
    models: list[ModelInfo]
    default: str               # 默认模型
```

### 3.2 API 接口设计

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 生成反驳 | POST | `/api/generate` | 核心接口 |
| 可用模型 | GET | `/api/models` | 获取支持的模型列表 |
| 健康检查 | GET | `/health` | 服务健康状态 |

### 3.3 前端数据流

```
用户输入 → 表单验证 → Fetch API → 后端API → LLM调用 → 响应 → DOM更新
```

---

## 4. 关键技术实现

### 4.1 LLM统一接口设计

**目标**: 一个 `LLMService` 类，支持切换不同模型

```python
# 统一接口
class LLMProvider(ABC):
    """LLM提供商基类"""
    @abstractmethod
    def chat(self, messages: list, **kwargs) -> str:
        """统一聊天接口"""
        pass

# 具体实现
class MiniMaxProvider(LLMProvider):
    def chat(self, messages, **kwargs) -> str:
        # MiniMax特定实现
        pass

class ZhipuProvider(LLMProvider):
    def chat(self, messages, **kwargs) -> str:
        # 智谱特定实现
        pass
```

**设计模式**: 策略模式 (Strategy Pattern) - 不同算法（模型）可以互换

### 4.2 Prompt 工程

反驳生成的Prompt结构:

```
【角色】你是一个辩论助手，擅长以理服人地反驳喷子。

【场景】{scene}
【我的立场】{my_stance}
【对方定位】{opponent_profile}
【激烈程度】{aggression}/10

【要求】
1. 所有事实性陈述必须真实，不可编造
2. 以理服人，可以用归谬法、指出逻辑漏洞
3. 根据激烈程度调整语气
4. 目标字数: 约{target_length}字

【对方的话】
{message}

【开始反驳】
```

### 4.3 字数控制

通过 prompt 引导控制:
1. **Prompt引导**: 在prompt中要求"约为XX字"
2. **max_tokens上限**: 固定 3000，防止API异常

实际实现: 不再根据 target_length 硬性限制输出，避免截断

### 4.4 异步处理

```python
# 非阻塞调用LLM API
@app.post("/api/generate")
async def generate(req: GenerateRequest):
    # async让服务器在等待LLM响应时可以处理其他请求
    result = await llm_service.chat_async(req.messages)
    return result
```

---

## 5. 关键技术难点

### 5.1 多模型API适配

**难点**: 不同模型的API格式、endpoint、认证方式不同

**解决方案**:
- 统一抽象 `LLMProvider` 基类
- 每个模型单独实现，但接口统一
- 配置文件中管理API密钥和endpoint

### 5.2 Prompt注入防护

**难点**: 用户输入可能干扰Prompt结构

**解决方案**:
- 用户输入通过 Prompt 变量传入，不直接拼接
- 输入长度限制
- 过滤危险字符

### 5.3 响应时间优化

**难点**: LLM调用较慢，用户等待时间长

**解决方案**:
- 异步处理
- 流式输出 (Server-Sent Events)
- 前端加载状态提示

### 5.4 真实性验证

**难点**: 如何确保生成的反驳事实准确

**解决方案**:
- Prompt中强调"禁止编造事实"
- 较低temperature降低胡说八道概率
- 添加"未经核实请注明"的提示

---

## 6. Windows 环境注意事项

### 6.1 创建独立的虚拟环境（推荐）

为了不破坏你原有的Python环境，使用Anaconda创建独立环境：

```bash
# 1. 创建新环境（Python 3.11）
conda create -n disputebot python=3.11 -y

# 2. 激活环境
conda activate disputebot

# 3. 安装所有依赖
pip install fastapi uvicorn[standard] pydantic pydantic-settings requests python-dotenv

# 4. 以后每次使用前都要先激活环境
conda activate disputebot
```

**验证环境是否正常**:
```bash
python --version  # 应该显示 3.11.x
pip list          # 应该看到 fastapi, uvicorn 等
```

### 6.2 启动命令

```bash
# 进入项目目录
cd D:\create\play

# 激活环境（每次使用前都要执行）
conda activate disputebot

# 启动服务器（开发模式，热重载）
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

# 访问地址
# 前端: http://127.0.0.1:8000
# API文档: http://127.0.0.1:8000/docs
```

### 6.3 编码问题

Windows 默认使用 GBK 编码，Python 3 默认 UTF-8。

```python
# 如果遇到编码问题，在文件开头添加
import sys
sys.stdout.reconfigure(encoding='utf-8')
```

### 6.4 路径问题

Windows 路径使用反斜杠 `\`，但在代码中：
- Python 字符串中 `\n` `\t` 是转义符，所以用原始字符串 `r"D:\path"` 或正斜杠 `"D:/path"`
- URL路径使用正斜杠 `/`

### 6.5 环境变量

Windows 设置环境变量:
```bash
# 临时设置（当前命令行有效）
set MINIMAX_API_KEY=your_key

# 永久设置（控制面板 → 系统 → 高级 → 环境变量）
```

---

## 7. 配置管理

### 7.1 配置文件结构

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """应用配置"""

    # MiniMax
    minimax_api_key: str = ""
    minimax_api_url: str = "https://api.minimax.chat/v1/text/chatcompletion_v2"

    # 智谱
    zhipu_api_key: str = ""
    zhipu_api_url: str = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

    # KIMI
    kimi_api_key: str = ""
    kimi_api_url: str = "https://api.moonshot.cn/v1/chat/completions"

    # ... 其他模型配置

    class Config:
        env_file = ".env"  # 从.env文件读取

settings = Settings()
```

### 7.2 .env 文件示例

```bash
# .env 文件（不要提交到git）
MINIMAX_API_KEY=your_minimax_key_here
DEEPSEEK_API_KEY=your_deepseek_key_here
KIMI_API_KEY=your_kimi_key_here
ZHIPU_API_KEY=your_zhipu_key_here

# 自定义中转站配置（JSON格式）
CUSTOM_SETTINGS={"api_key": "xxx", "base_url": "https://openrouter.ai/api/v1", "model": "gpt-4o-mini"}
```

---

## 8. 依赖列表

```
# requirements.txt

fastapi>=0.109.0          # Web框架
uvicorn[standard]>=0.27.0  # ASGI服务器
pydantic>=2.5.0           # 数据验证
pydantic-settings>=2.1.0  # 配置管理
requests>=2.31.0          # HTTP客户端
python-dotenv>=1.0.0      # .env文件支持
```

---

## 9. 开发流程

### 步骤1: 项目初始化
1. 创建目录结构
2. 安装依赖
3. 配置环境变量

### 步骤2: 后端基础 - 数据模型
1. 创建 `backend/models/schemas.py`
2. 实现请求验证

### 步骤3: 后端基础 - LLM服务
1. 实现 Provider 基类 `backend/services/providers/base.py`
2. 实现第一个 Provider (MiniMax) `backend/services/providers/minimax.py`
3. 实现 LLM服务 `backend/services/llm.py`

### 步骤4: 后端基础 - API路由
1. 实现 `/api/generate` 和 `/api/models`
2. 实现健康检查接口 `/health`
3. 创建 `backend/main.py` 入口

### 步骤5: 前端开发
1. 创建 `frontend/index.html`
2. 实现表单和交互
3. 调用API并展示结果

### 步骤6: 扩展模型
1. 按需添加其他 Provider
2. 统一测试

---

## 10. 测试验证

### 10.1 后端测试

```bash
# 启动服务器
uvicorn backend.main:app --reload

# 打开浏览器访问
http://127.0.0.1:8000/docs

# 在Swagger文档中测试POST /api/generate
{
  "message": "骡子就靠皇马体系，没有本泽马什么都不是",
  "scene": "足球",
  "my_stance": "巴萨球迷",
  "opponent_profile": "皇马球迷结晶",
  "aggression": 7,
  "temperature": 0.8,
  "target_length": 200,
  "model": "minimax"
}
```

### 10.2 前端测试

1. 访问 http://127.0.0.1:8000
2. 填写表单，点击生成
3. 检查是否有错误，查看控制台日志

---

**文档版本**: v1.1
**最后更新**: 2026-04-25