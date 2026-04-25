# GUIDE-005: 前端页面 (index.html)

## 这块代码做了什么

创建了一个完整的前端单页应用，用户可以：
- 输入背景场景、立场、对方定位
- 调整激烈程度（1-5）、随机性（0-2）、目标字数（10-2000）
- 选择模型（MiniMax / DeepSeek / KIMI / 智谱 / 自定义中转站）
- 输入对方的话
- 点击生成，获取 AI 生成的反驳
- **中英文切换**：点击右上角按钮切换界面语言

## 核心知识点

### 1. HTML 结构

```html
<div class="container">
    <header class="header">
        <h1>反驳生成器</h1>
        <button id="langToggle" class="lang-btn">EN / 中文</button>
    </header>
    <form class="card">...</form>
    <div class="custom-proxy-card" id="customProxyCard" style="display: none;">...</div>
    <div class="loading">...</div>
    <div class="result-card">...</div>
</div>
```

- `.container`: 居中容器
- `.card`: 卡片式布局
- `.header`: 页面标题 + 语言切换按钮
- `.custom-proxy-card`: 自定义中转站配置卡（选择 custom 模型时显示）

### 2. CSS 变量

```css
:root {
    --primary-color: #4a90d9;
    --bg-color: #f5f7fa;
    --text-color: #333;
}
```

**为什么要用 CSS 变量？**
- 统一样式，一处修改处处生效
- 方便主题切换
- 比直接写颜色值更易维护

### 3. 响应式布局

```css
.slider-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
}

@media (max-width: 600px) {
    .slider-row {
        grid-template-columns: 1fr;
    }
}
```

- `grid` 布局实现双列排布
- `@media` 在屏幕宽度 < 600px 时变成单列

### 4. 表单事件处理

```javascript
form.addEventListener('submit', async (e) => {
    e.preventDefault();  // 阻止默认提交
    await callGenerateAPI(data);
});
```

- `preventDefault()` 阻止表单自动提交（页面刷新）
- `async/await` 处理异步请求

### 5. Fetch API 调用后端

```javascript
const response = await fetch('/api/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
});
const result = await response.json();
```

- `fetch()` 是浏览器内置的 HTTP 客户端
- `JSON.stringify()` 把 JS 对象转成 JSON 字符串

### 6. DOM 操作

```javascript
// 显示/隐藏元素
loadingDiv.classList.toggle('show', show);

// 设置内容
resultContent.textContent = reply;

// 获取值
sceneInput.value
```

- `classList.toggle()` 切换 CSS 类
- `.textContent` 设置文本内容
- `.value` 获取输入框的值

## 代码逐段解读

### HTML 部分

| 元素 | 作用 |
|------|------|
| `<form id="form">` | 表单容器，提交事件在这里处理 |
| `<textarea>` | 多行文本输入 |
| `<input type="range">` | 滑块 |
| `<select>` | 下拉选择 |

### CSS 部分

| 类名 | 作用 |
|------|------|
| `.card` | 白色卡片，带阴影和圆角 |
| `.btn-primary` | 主按钮样式 |
| `.loading` | 加载状态（默认隐藏） |
| `.result-card` | 结果显示区（默认隐藏） |

### JavaScript 部分

| 函数 | 作用 |
|------|------|
| `showLoading()` | 显示/隐藏加载状态 |
| `showError()` | 显示错误信息 |
| `showResult()` | 显示生成结果 |
| `loadModels()` | 页面加载时获取模型列表 |
| `callGenerateAPI()` | 调用后端 API |
| `updatePlaceholders()` | 根据语言更新占位符文本 |
| `toggleCustomProxy()` | 显示/隐藏自定义中转站配置 |
| `setLanguage()` | 切换中英文界面 |

### 语言切换功能

```javascript
const translations = {
    "zh": {
        title: "反驳生成器",
        scene: "背景场景",
        scenePlaceholder: "如: 足球 - 国家德比皇马0-4巴萨，球迷互喷",
        // ... 更多翻译
    },
    "en": {
        title: "Dispute Bot",
        scene: "Scene",
        scenePlaceholder: "e.g., Football - El Clasico Real Madrid 0-4 Barcelona",
        // ... 更多翻译
    }
};
```

通过 `translations` 对象存储所有界面文本，切换时遍历更新表单元素的 `placeholder` 和标签文本。

## 如果我想试试看

1. **修改样式**: 改 CSS 变量里的颜色值，看看效果
2. **添加字段**: 在 HTML 加一个输入框，在 JS 里读取它的值
3. **修改布局**: 改成三列布局

## 启动测试

```bash
cd D:\create\play
disputebot-venv\Scripts\uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

然后访问 http://127.0.0.1:8000 查看前端页面。

---

下一步是什么？

目前后端和前端都已经创建完成！接下来可以：
1. 创建 `.env` 文件配置 API 密钥
2. 测试完整流程
3. 根据需要扩展其他 Provider