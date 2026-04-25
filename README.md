# DisputeBot - 反驳生成器

输入喷子言论，AI 生成有力反驳。

[English](#english) | 中文

---

## 功能特性

- 支持多种 LLM 提供商：MiniMax、DeepSeek、KIMI、智谱GLM、自定义中转站
- 可调节反驳激烈程度（1-5 级）
- 可调节输出随机性（Temperature 0-2）
- 字数控制（10-2000 字）
- 中英文界面切换
- 事实真实性验证

---

## 安装

### 1. 克隆项目

```bash
# 方式1: Git克隆
git clone https://github.com/ysqd1/DisputeBot.git

# 方式2: 手动下载
# 下载并解压到本地文件夹

cd /d <DisputeBot的本地路径>


```

### 2. 创建虚拟环境（推荐）

```bash
python -m venv disputebot-venv

# Windows（命令提示符或PowerShell）
disputebot-venv\Scripts\activate

# Linux/Mac
source disputebot-venv/bin/activate
```

### 3. 安装依赖

```bash
pip install fastapi uvicorn[standard] pydantic pydantic-settings requests python-dotenv
```

### 4. 配置环境变量

复制 `.env.example` 为 `.env`，填入你的 API 密钥：

```bash
# Windows 命令提示符
copy .env.example .env

# Git Bash 或 Linux/Mac
cp .env.example .env
```

编辑 `.env` 文件（可选，也可直接在网页端填写 Key）：

```env
MINIMAX_API_KEY=你的MiniMax密钥
DEEPSEEK_API_KEY=你的DeepSeek密钥
KIMI_API_KEY=你的KIMI密钥
ZHIPU_API_KEY=你的智谱密钥

# 自定义中转站（可选）
# CUSTOM_SETTINGS={"api_key": "xxx", "base_url": "https://api.proxy.com/v1", "model": "gpt-4o-mini"}
```

> **两种方式选择一种：**
> 1. 在 `.env` 文件中配置 Key（启动时自动加载）
> 2. 直接在网页端填写 Key（优先级更高）

---

## 运行

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

启动后访问：
- 前端页面：http://127.0.0.1:8000
- API 文档：http://127.0.0.1:8000/docs

---

## 项目结构

```
DisputeBot\
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── routers/generate.py  # API 路由
│   ├── services/llm.py      # LLM 服务
│   └── models/schemas.py    # 数据模型
├── frontend/index.html       # 前端页面
├── guides/                   # 学习指南
├── .env.example             # 环境变量示例
├── SPEC.md                  # 需求分析
├── TECH.md                  # 技术文档
└── AGENT.md                 # 开发规范
```

---

## API 接口

### 生成反驳

```
POST /api/generate
```

**请求体：**

```json
{
  "message": "骡子就靠皇马体系，没有本泽马什么都不是",
  "scene": "足球 - 国家德比皇马0-4巴萨",
  "my_stance": "皇马球迷",
  "opponent_profile": "巴萨球迷结晶",
  "aggression": 3,
  "temperature": 0.8,
  "target_length": 200,
  "model": "minimax",
  "model_variant": null,
  "api_key": null,
  "base_url": null
}
```

### 可用模型列表

```
GET /api/models
```

---

## 许可证

本项目采用 MIT 许可证。

---

## English

### DisputeBot - Rebuttal Generator

Input toxic remarks and get AI-generated rebuttals.

### Features

- Multiple LLM providers: MiniMax, DeepSeek, KIMI, ZhipuGLM, Custom Proxy
- Adjustable aggression level (1-5)
- Adjustable randomness (Temperature 0-2)
- Word count control (10-2000)
- Chinese/English language toggle
- Fact verification

### Quick Start

```bash
# Clone the project
git clone <your-repo-url>
cd /d <DisputeBot的本地路径>

# Create virtual environment
python -m venv disputebot-venv

# Windows (CMD or PowerShell)
disputebot-venv\Scripts\activate

# Git Bash or Linux/Mac
source disputebot-venv/bin/activate

# Install dependencies
pip install fastapi uvicorn[standard] pydantic pydantic-settings requests python-dotenv

# Copy and configure environment
# Windows
copy .env.example .env
# Git Bash or Linux/Mac
cp .env.example .env
# Then edit .env with your API keys

# Run
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Visit http://127.0.0.1:8000 to use the app.
