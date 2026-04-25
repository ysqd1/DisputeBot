# GUIDE-003: LLM 统一服务 (llm.py)

## 这块代码做了什么

**核心作用**：把"路由层"和"Provider层"连接起来

```
路由 (generate.py) → LLMService → MiniMaxProvider / ZhipuProvider / ...
```

## 核心知识点

### 1. 缓存模式避免重复创建

```python
self._provider_cache: dict[str, LLMProvider] = {}

def _get_provider(self, model: str) -> LLMProvider:
    if model in self._provider_cache:
        return self._provider_cache[model]  # 直接返回缓存
    # 否则创建新的...
```

**为什么要缓存？**
- 创建 Provider 需要传 API 密钥
- 每次请求都重新创建会比较慢
- 缓存起来可以复用

### 2. 工厂方法模式

```python
def _get_provider(self, model: str) -> LLMProvider:
    provider_class = self.SUPPORTED_MODELS.get(model)  # 找到类
    provider = provider_class(api_key=api_key)  # 创建实例
    return provider
```

`SUPPORTED_MODELS` 是一个字典，**键是字符串，值是类**。
这让我们可以用字符串动态选择要创建哪个类。

### 3. Prompt 工程

Prompt 就是给 AI 的"指令"，决定 AI 怎么回复。

```python
def build_system_prompt(...):
    prompt = f"""你是一个辩论助手...

    【背景场景】
    {scene}

    【我的立场】
    {my_stance}

    ...
    """
    return prompt
```

### 4. 核心函数：generate_reply()

```python
def generate_reply(
    llm_service, model, message, scene,
    my_stance, opponent_profile, aggression,
    temperature, target_length
) -> str:
    # 1. 构建提示词
    system_prompt = build_system_prompt(...)
    user_message = build_user_message(message)

    # 2. 组装消息列表
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    # 3. 计算 max_tokens (字数转token，约0.75倍)
    max_tokens = int(target_length * 0.75) if target_length > 0 else 2000

    # 4. 调用 LLM
    reply = llm_service.chat(model=model, messages=messages, ...)

    return reply
```

这是整个后端的核心函数，把所有参数串联起来。

## 代码逐段解读

### 第1段: SUPPORTED_MODELS 字典

```python
SUPPORTED_MODELS = {
    "minimax": MiniMaxProvider,
    "deepseek": DeepSeekProvider,
    "kimi": KimiProvider,
    "zhipu": ZhipuProvider,
    "custom": CustomProvider,  # 自定义中转站
}
```

这叫"注册表模式" - 用字符串映射到类。
以后想添加新模型，只需在这个字典里加一行。

### 第2段: _get_provider() 方法

```python
def _get_provider(self, model: str) -> LLMProvider:
    provider_class = self.SUPPORTED_MODELS.get(model)
    if provider_class is None:
        raise ValueError(f"不支持的模型: {model}")
    ...
    return provider
```

1. 用 `dict.get()` 安全地查找（找不到返回 None 不会报错）
2. 找不到就抛异常
3. 找到了就创建实例

### 第3段: API 密钥优先级

LLMService 支持**前端传入密钥优先**的机制：

```python
def chat(self, model, messages, temperature, max_tokens,
         api_key=None, base_url=None, model_variant=None):
    # API 密钥优先级：前端传入 > .env 配置 > 自定义配置
    effective_api_key = api_key or self.api_keys.get(model, "")

    # Custom 模型的特殊处理
    if model == "custom":
        effective_base_url = base_url or self.custom_settings.get("base_url", "")
        effective_api_key = api_key or self.custom_settings.get("api_key", "")
        effective_model = model_variant or self.custom_settings.get("model", "gpt-4o-mini")
```

这允许用户：
- 在前端直接输入 API Key（优先使用）
- 或使用 .env 文件中配置好的密钥
- 自定义中转站可以指定 base_url

### 第4段: build_system_prompt() 函数

这个函数决定了 AI 的"性格"和"行为准则"。

关键部分 - 激烈程度（现在分为 1-5 级）：
```python
# 根据激烈程度决定语气
if aggression == 1:
    tone = "极度温和，摆事实讲道理，以理服人"
elif aggression == 2:
    tone = "温和但有态度，稍带情绪"
elif aggression == 3:
    tone = "中等，阴阳怪气、讽刺"
elif aggression == 4:
    tone = "很强，讽刺挖苦、拉满"
else:  # aggression == 5
    tone = "直接开喷，攻击力极强，可以用少量脏话"
```

```python
# 核心原则
- 以理服人，不是为了喷而喷
- 无论多激烈，论据必须站得住脚
- 不要暴露你是在使用AI
- 禁止编造事实，不确定时标注"未经核实"
```

这些原则会注入到 AI 的系统提示里。

### 第5段: generate_reply() 函数

这是"门面函数"，把复杂逻辑包装成简单接口。

调用流程：
```
用户调用 generate_reply(...)
  → 构建 system_prompt
  → 构建 user_message
  → 组合成 messages 列表
  → max_tokens 固定 3000（字数由 prompt 引导控制）
  → 调用 llm_service.chat()
  → 返回 reply
```

**注意**：字数控制现在完全由 prompt 引导，不再根据 target_length 硬性限制 max_tokens，避免截断。

## 如果我想试试看

1. **理解工厂模式**: 在 Python 交互式环境试试：
   ```python
   class Dog:
       def speak(self): return "汪"
   class Cat:
       def speak(self): return "喵"

   animals = {"dog": Dog, "cat": Cat}
   animal = animals["dog"]()
   print(animal.speak())
   ```

2. **理解 Prompt**: 修改 `build_system_prompt()` 里的语气描述，看看 AI 回复有什么区别。

3. **理解 API 密钥优先级**: 在 .env 配置一个密钥，然后在前端表单也输入一个密钥，验证前端传入的优先使用。

4. **测试自定义中转站**: 选择 "custom" 模型，输入 OpenRouter 的 API Key 和地址，测试是否能正常工作。

---

下一步是创建 API 路由，继续吗？