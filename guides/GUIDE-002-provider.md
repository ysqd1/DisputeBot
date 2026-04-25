# GUIDE-002: Provider 基类与 MiniMax 实现

## 这块代码做了什么

1. **定义了 Provider 的"模板"** (`base.py`)
   - 所有模型提供商（MiniMax、智谱、Kimi...）都要遵守这个模板
   - 必须实现 `chat()` 和 `get_provider_name()` 方法

2. **实现了第一个具体 Provider** (`minimax.py`)
   - 告诉你怎么调用 MiniMax 的 API
   - 展示了完整的 HTTP 请求流程

## 核心知识点

### 1. 抽象类 (ABC) 是什么？

```python
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def chat(self, messages, ...):
        pass  # 不提供具体实现，只定义"必须有这个方法"
```

**为什么需要抽象类？**
- 确保每个 Provider 都有 `chat()` 方法
- 如果你忘记在某个 Provider 里实现 `chat()`，Python 会报错
- 这叫"面向接口编程" - 你只管调用 `chat()`，不管是哪个 Provider

### 2. 继承和 super()

```python
class MiniMaxProvider(LLMProvider):
    def __init__(self, api_key, model):
        super().__init__(api_key, model)  # 调用父类的 __init__
```

`super().__init__()` 的意思是"执行父类的初始化代码"。
MiniMax 需要 `api_key` 和 `model`，但同时也要保存父类需要的东西。

### 3. requests 库基本用法

```python
import requests

# 发送 POST 请求
response = requests.post(
    url,           # API地址
    headers=...,   # 请求头（如API密钥）
    json=...,       # 请求体（Python对象会自动转成JSON）
    timeout=30     # 超时时间（秒）
)

# 检查是否成功
response.raise_for_status()  # 如果不是200，会抛出异常

# 获取响应内容
data = response.json()  # 解析JSON响应
```

### 4. 异常处理

```python
try:
    # 可能出错的代码
    response = requests.post(...)
except requests.exceptions.Timeout:
    raise Exception("请求超时")
except requests.exceptions.HTTPError as e:
    raise Exception(f"HTTP错误: {e.response.status_code}")
except Exception as e:
    raise Exception(f"未知错误: {str(e)}")
```

**为什么要捕获异常？**
- 网络不稳定，API可能失败
- 不捕获的话，程序会直接崩溃
- 捕获后可以给用户友好的错误提示

## 代码逐段解读

### base.py - LLMProvider 抽象类

```python
class LLMProvider(ABC):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    @abstractmethod
    def chat(self, messages, temperature, max_tokens) -> str:
        pass  # 抽象方法，没有具体实现

    @abstractmethod
    def get_provider_name(self) -> str:
        pass  # 返回提供商名称
```

- `ABC` 是 Python 内置的抽象基类
- `@abstractmethod` 装饰器表示"子类必须实现这个方法"

### base.py - build_messages 工厂函数

```python
def build_messages(system_prompt, user_message, history=None):
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})
    return messages
```

这是一个**工厂函数** - 它的唯一目的是构建数据。
- 把"系统提示"+"历史对话"+"用户消息"组装成标准格式
- `history=None` 表示历史对话可选，不传就为空

### minimax.py - chat() 方法

```python
def chat(self, messages, temperature, max_tokens) -> str:
    headers = {"Authorization": f"Bearer {self.api_key}", ...}
    payload = {"model": self.model, "messages": messages, ...}

    response = requests.post(self.API_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()  # 检查HTTP状态

    data = response.json()
    return data["choices"][0]["message"]["content"]
```

这是典型的 OpenAI-style API 调用：
1. 准备 headers（放 API 密钥）
2. 准备 payload（放模型名、消息等）
3. 发送请求
4. 解析响应

## 支持的模型提供商

目前已实现的 Provider：

| Provider | ID | 默认模型 | API URL |
|----------|-----|---------|---------|
| MiniMax | `minimax` | MiniMax-M2.7 | https://api.minimax.chat/v1/text/chatcompletion_v2 |
| DeepSeek | `deepseek` | deepseek-v4-flash | https://api.deepseek.com/chat/completions |
| KIMI (Moonshot) | `kimi` | kimi-k2.5 | https://api.moonshot.cn/v1/chat/completions |
| 智谱 GLM | `zhipu` | glm-5.1 | https://open.bigmodel.cn/api/paas/v4/chat/completions |
| 自定义中转站 | `custom` | 自定义 | 用户提供 |

## 如果我想试试看

1. **理解抽象类**: 试着实例化 `LLMProvider`，看看会发生什么：
   ```python
   provider = LLMProvider("key", "model")  # 会报错！
   ```

2. **理解继承**: 试着实例化 `MiniMaxProvider`：
   ```python
   provider = MiniMaxProvider("你的密钥")  # 可以，但调用chat会失败（没设置代理）
   ```

3. **看看API响应格式**: 访问 MiniMax 文档，看看他们的响应长什么样

4. **添加新 Provider**: 参考现有 Provider 的实现，创建新文件如 `qwen.py`，在 `llm.py` 的 `SUPPORTED_MODELS` 字典中注册即可。

---

准备好继续了吗？下一步是实现 LLM 统一服务（llm.py）。