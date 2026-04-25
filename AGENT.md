# Agent 开发规范

> 本文件是 Claude Code 在本项目中的行为规范

---

## 1. 项目概述

**项目名称**: DisputeBot (反驳生成器)
**项目类型**: 本地优先的 Web 应用
**核心功能**: 输入喷子言论，AI 生成有力反驳
**目标用户**: 计算机专业大学生（边做边学）

**技术栈**:
- 后端: FastAPI (Python)
- 前端: 原生 HTML + CSS + JS
- AI: MiniMax (首选) / 智谱GLM / KIMI / 千问 / DeepSeek / 豆包

**重要原则**:
- 信息真实性: 反驳中的所有事实必须为真
- 以理服人: 不是为了喷而喷，而是驳倒对方
- 驳倒手段: 指出错误、归谬法、逻辑漏洞、事实对比

---

## 2. 代码风格规范

### 2.1 注释要求

**必须包含**:
```python
# 模块/文件顶部: 文件功能说明
"""
DisputeBot 后端入口
包含FastAPI应用创建、CORS配置、路由注册
"""

# 类顶部: 类功能、用途
class LLMService:
    """统一LLM调用服务，封装多个模型提供商"""

# 函数顶部: 函数功能、参数、返回值
def generate_reply(message: str, scene: str) -> str:
    """
    生成反驳内容

    Args:
        message: 对方说的话
        scene: 场景（足球/游戏/生活）

    Returns:
        生成的反驳内容
    """

# 复杂逻辑: 解释为什么这样做
# 使用策略模式：不同模型可以互换
provider = self.get_provider(model)
```

**行内注释**:
- 解释"为什么"，不解释"是什么"
- 避免废话注释: `i += 1  # i自增` ❌
- 必要注释: `i += 1  # 跳过已处理的元素` ✓

### 2.2 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 文件 | 小写下划线 | `llm_service.py` |
| 类 | 大驼峰 | `LLMService`, `MiniMaxProvider` |
| 函数 | 小写下划线 | `generate_reply()`, `get_provider()` |
| 常量 | 全大写下划线 | `MAX_TOKENS`, `DEFAULT_MODEL` |
| 变量 | 小写下划线 | `api_key`, `target_length` |
| 私有 | 前置下划线 | `_cache`, `__init__` |

### 2.3 代码结构

**Python 文件结构**:
```python
"""
模块说明
"""

# 标准库
import os
from typing import Optional

# 第三方库
import requests
from fastapi import APIRouter

# 本地导入
from models.schemas import GenerateRequest

# 类和函数定义
class MyClass:
    """类说明"""
    def method(self):
        pass

def my_function():
    pass

# 如果有main逻辑
if __name__ == "__main__":
    main()
```

### 2.4 简单优先

- 能用简单方式就不要用复杂方式
- 不要过度工程化
- 一个函数不超过50行
- 一个类不超过300行

---

## 3. 开发流程规范

### 3.1 分步生成代码

**规则**: 每次只生成一小块代码，配套 GUIDE 文档

1. 创建 `guides/GUIDE-XXX-name.md`
2. 生成代码块（如: backend/models/schemas.py）
3. 等待用户确认理解
4. 继续下一步

### 3.2 GUIDE 文档格式

```markdown
# GUIDE-XXX: [功能名称]

## 这块代码做了什么
[简单解释]

## 核心知识点
- 知识点1
- 知识点2

## 代码解读
[逐行或逐段解释]

## 如果我想试试看
[动手实验的建议]
```

### 3.3 用户交互要求

**必须**:
- 每步完成后询问用户是否理解
- 解释代码时用"你"而不是"开发者"
- 确认用户理解了再继续

**禁止**:
- 不要一次生成所有代码
- 不要在用户没确认前继续下一步
- 不要假设用户已经理解

---

### 4.1 字数控制

- 字数控制完全由 prompt 引导，不通过 max_tokens 硬性限制
- max_tokens 只设一个上限（3000），防止API异常
- 避免截断：让 AI 自己控制输出长度

### 4.2 Windows 环境

- Python 路径使用 `/` 或 raw string `r"D:\path"`
- 默认编码是 GBK，需要时添加 `sys.stdout.reconfigure(encoding='utf-8')`
- 启动命令: `uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000`

### 4.3 信息真实性

- 所有生成的事实性内容必须为真
- 不确定时标注"未经核实"
- 禁止编造数据、成绩、事件

### 4.4 API 密钥优先级

- 前端填写 API Key → 优先使用
- 前端留空 → 使用 .env 对应供应商的配置
- .env 格式: `MINIMAX_API_KEY`, `DEEPSEEK_API_KEY`, `KIMI_API_KEY`, `ZHIPU_API_KEY`
- 自定义中转站: `CUSTOM_SETTINGS={"api_key": "xxx", "base_url": "https://...", "model": "gpt-4o-mini"}`

### 4.5 API 密钥安全

- 不在代码中硬编码 API 密钥
- 使用环境变量或 .env 文件
- .env 文件添加到 .gitignore

### 4.6 错误处理

- 所有 API 调用都要 try-except
- 给用户有意义的错误信息
- 不要暴露内部错误细节

---

## 5. 文件创建顺序

1. `SPEC.md` - 需求分析 ✅ 已创建
2. `TECH.md` - 技术文档 ✅ 已创建
3. `AGENT.md` - 本规范文档 ✅ 已创建
4. `guides/` - 指南目录
5. `requirements.txt` - 依赖列表
6. `config.py` - 配置文件
7. `backend/__init__.py`
8. `backend/models/__init__.py`
9. `backend/models/schemas.py` - 数据模型
10. `backend/services/__init__.py`
11. `backend/services/providers/__init__.py`
12. `backend/services/providers/base.py` - Provider基类
13. `backend/services/providers/minimax.py` - 第一个Provider
14. `backend/services/llm.py` - LLM服务
15. `backend/routers/__init__.py`
16. `backend/routers/generate.py` - API路由
17. `backend/main.py` - FastAPI 入口
18. `frontend/index.html` - 前端页面

---

## 6. 用户学习要求

**边做边学原则**:
- 每段代码都要讲解
- 讲解内容包括:
  - 这段代码做什么
  - 核心概念解释
  - 为什么会这样写
  - 如果改掉会怎样
- 用户可以随时提问
- 用户确认理解了才继续

**讲解方式**:
- 用通俗语言解释技术术语
- 给出生活中的类比
- 鼓励用户动手实验

---

## 7. 质量检查清单

完成每个 GUIDE 后自检:
- [ ] 代码有适当注释
- [ ] 变量命名清晰
- [ ] 错误处理完善
- [ ] 功能描述已更新
- [ ] 用户已确认理解

---

## 8. 代码质量要求

### 8.1 测试验证

**必须**:
- 每段代码生成后要测试运行
- 至少测试 2-3 次确保功能正常
- 测试正常结果
- 测试边界情况和错误情况

**示例**:
```
# 生成 schemas.py 后
1. 启动服务器: uvicorn backend.main:app --reload
2. 访问 http://127.0.0.1:8000/docs
3. 测试 POST /api/generate 接口
4. 检查返回结果是否符合预期
```

### 8.2 避免拆东墙补西墙

**禁止**:
- 为了修一个问题，修改很多不相关的代码
- 在修复bug时引入新的bug
- 随意修改已经正常工作的代码

**正确做法**:
- 只改需要改的地方
- 如果需要大改，先备份
- 改完后验证之前的功能是否还能正常工作

### 8.3 模块化原则

**核心思想**: 把大问题拆成小问题，每个小问题独立解决

**具体要求**:
- 每个文件/模块只做一件事
- 模块之间通过明确的接口通信
- 独立的逻辑抽成函数或类
- 不要把所有代码写在一个文件里

**示例**:
```
backend/
├── main.py           # 只负责创建app和注册路由
├── routers/          # 只负责路由
├── services/         # 只负责业务逻辑
└── models/          # 只负责数据模型
```

---

**文档版本**: v1.3
**最后更新**: 2026-04-25