# GUIDE-001: 数据模型 schemas.py

## 这块代码做了什么

定义了数据的"形状" - 告诉 FastAPI 什么样的请求是合法的，什么样的响应会返回给用户。

## 核心知识点

### 1. Pydantic 是什么?

想象你要从用户那里收"年龄"这个数据。如果用户输入了"hello"怎么办？

**没有 Pydantic 时**（大量 if 语句）:
```python
age = input("年龄: ")
if not age.isdigit():
    raise ValueError("年龄必须是数字")
if int(age) < 0:
    raise ValueError("年龄不能为负")
if int(age) > 150:
    raise ValueError("年龄太大了")
```

**有了 Pydantic 时**（声明式验证）:
```python
age: int = Field(ge=0, le=150)
# 自动完成：类型转换、范围检查、错误提示
```

### 2. Field 验证参数

```python
message: str = Field(
    ...,  # ... 表示必填
    min_length=1,  # 最少1个字符
    description="描述"  # 这个描述会显示在API文档里
)

aggression: int = Field(
    default=3,  # 默认值
    ge=1,  # greater than or equal (大于等于)
    le=5  # less than or equal (小于等于)
)
```

### 3. | None 的含义

```python
reply: str | None = None
```

意思是：`reply` 可以是字符串，也可以是 `None`

### 4. 模型类的作用

```python
class GenerateRequest(BaseModel):
    message: str
    scene: str
```

当用户发送请求时，FastAPI 会：
1. 接收 JSON 数据
2. 验证每个字段是否符合定义
3. 如果不符合，返回 422 错误（不会进入你的代码）
4. 如果符合，把数据转成 Python 对象传给你的函数

## 代码逐段解读

### 第1段: 导入
```python
from pydantic import BaseModel, Field
```
从 pydantic 库导入两个东西：
- `BaseModel`: 所有数据模型的"基类"，就像一个模板
- `Field`: 用来给每个字段加验证规则

### 第2段: GenerateRequest
```python
class GenerateRequest(BaseModel):
    message: str = Field(..., min_length=1, description="...")
    scene: str = Field(..., description="...")
    ...
```
这是用户发给服务器的数据格式。

`...` 在 Python 里叫"省略号"，这里表示"这个字段必填"。

### 第3段: GenerateResponse
```python
class GenerateResponse(BaseModel):
    success: bool
    reply: str | None = None
    error: str | None = None
```
这是服务器返回给用户的数据格式。

注意 `reply` 和 `error` 有默认值 `None`，意味着它们可以没有值。

### 第4段: ModelInfo 和 ModelListResponse
```python
class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str

class ModelListResponse(BaseModel):
    models: list[ModelInfo]
    default: str
```
`models: list[ModelInfo]` 意思是"一个 ModelInfo 组成的列表"。

### 第5段: 新增字段（API密钥优先级）

GenerateRequest 中新增了三个字段，支持前端直接传入 API 密钥：

```python
api_key: str | None = Field(default=None)
base_url: str | None = Field(default=None)
model_variant: str | None = Field(default=None)
```

**api_key**: 前端可以直接输入 API 密钥，优先于 .env 配置
**base_url**: 自定义中转站地址，仅 model=custom 时使用
**model_variant**: 具体模型名称，留空使用默认模型

这种设计让用户可以：
1. 在前端输入自己购买的 API Key（优先使用）
2. 使用 .env 中配置的密钥（前端留空时）
3. 自定义中转站（需要同时提供 base_url 和 api_key）

## 如果我想试试看

1. **验证是否工作**: 启动服务器后，访问 http://127.0.0.1:8000/docs，找到 GenerateRequest 相关的接口，试着发一个不合法的请求（比如 aggression=20），看看会发生什么。

2. **看看自动生成的文档**: FastAPI 根据这些模型自动生成了交互式文档，你可以在 /docs 页面看到每个字段的说明。

---

有问题吗？理解了这个数据模型，我们继续往下走。