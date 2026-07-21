# ClipSnap 🖇️

**网页一键转 Markdown · 知识收藏从未如此简单**

> 点击一下，把任何网页变成干净、可搜索的 Markdown。支持微信公众号、知乎、CSDN、Medium 等平台的智能内容提取。**开源 · 自托管 · 零依赖外部服务。**

[![GitHub stars](https://img.shields.io/badge/dynamic/json?color=blue&label=stars&query=stargazers_count&url=https://api.github.com/repos/jjjkkll157/clipsnap)](https://github.com/jjjkkll157/clipsnap)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## 📖 使用指南

### 🚀 方式一：一键安装（新手推荐，不需要懂代码）

```
1. 下载项目 ZIP
   https://github.com/jjjkkll157/clipsnap → Code → Download ZIP → 解压

2. 双击 install.bat
   ✅ 自动检查 Python
   ✅ 自动安装依赖
   ✅ 自动创建桌面快捷方式

3. 双击桌面「ClipSnap」图标 → 服务启动
```

### 🔌 方式二：加载 Chrome 扩展

```
1. 打开 Chrome → 地址栏输入 chrome://extensions → 回车

2. 右上角打开「开发者模式」开关

3. 点击「加载已解压的扩展程序」
   → 选择 clipsnap 目录下的 extension/ 文件夹

4. 浏览器右上角出现 ClipSnap 图标 🖇️
   快捷键：Ctrl+Shift+S
```

### 📥 抓取网页

```
1. 浏览任意网页（微信公众号 / 知乎 / CSDN / 掘金 / 博客园 / V2EX / Medium / GitHub）

2. 点击 ClipSnap 图标 🖇️ → 弹出面板

3. 选择标签（可选）→ 点击「📥 抓取当前网页」

4. 完成！右下角显示保存成功
```

### 📋 管理收藏

```
浏览器打开 http://localhost:8710

- 🔍 搜索：输入关键词，回车搜索标题和正文
- 👁 预览：点击卡片，弹窗展示完整 Markdown
- 📋 复制：点击「复制 Markdown」
- 📱 公众号：点击「导出公众号格式」→ 自动复制 → 打开公众号编辑器 Ctrl+V
- 🗑 删除：点击「删除」
```

### 🖥️ 方式三：命令行启动（开发者）

```bash
cd backend
pip install -r requirements.txt
python main.py
# → http://localhost:8710
```

---

## ✨ 功能

| 功能 | 说明 |
|------|------|
| 🔌 Chrome 扩展 | 一键抓取当前网页为 Markdown |
| 🌐 Web 管理面板 | 深色主题，搜索/预览/导出/删除 |
| 📱 公众号导出 | 一键转为公众号编辑器兼容格式 |
| 🏷 标签分类 | 支持自定义标签，快速归类 |
| 📊 中英文统计 | CJK 字符按字计，拉丁按词计，混合准确统计 |
| 🏠 完全自托管 | 数据保存在本地 SQLite，零隐私风险 |

### 支持的平台

| 平台 | 提取方式 |
|------|----------|
| 微信公众号 | `#js_content` 主内容区 |
| 知乎 | `.RichContent-inner` |
| CSDN | `#content_views` + 付费遮罩移除 |
| 掘金 | `article.article` |
| 博客园 | `#cnblogs_post_body` |
| V2EX | `.topic_content` |
| Medium | `article` |
| GitHub | `article.markdown-body` |
| 其他 | 智能正文提取算法 |

---

## 📁 项目结构

```
clipsnap/
├── backend/
│   ├── main.py          # FastAPI 服务（6 个 API 端点 + SQLite）
│   ├── extractor.py     # 网页内容提取引擎（8+ 平台适配）
│   ├── converter.py     # HTML→Markdown + 公众号格式
│   └── requirements.txt
├── extension/           # Chrome 浏览器扩展
│   ├── manifest.json    # Manifest V3
│   ├── popup.html       # 弹出面板 UI
│   └── popup.js         # 弹出面板逻辑
├── web/
│   └── index.html       # Web 管理面板（深色主题单页应用）
├── install.bat          # ⭐ 一键安装脚本
├── 启动 ClipSnap.bat    # 开发环境快速启动
└── README.md
```

## 🔌 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/clip` | 抓取网页 → Markdown |
| `GET` | `/api/clips?q=关键词` | 列表（支持搜索） |
| `GET` | `/api/clip/:id` | 获取单条完整内容 |
| `DELETE` | `/api/clip/:id` | 删除 |
| `POST` | `/api/clip/:id/export` | 导出公众号格式 |
| `GET` | `/api/health` | 健康检查 |

---

## 🛠 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python 3.10+ · FastAPI · SQLite · BeautifulSoup4 · httpx |
| 前端 | Vanilla JS · Chrome Extension Manifest V3 |
| 管理面板 | 纯 HTML/CSS/JS 单页应用 · 深色主题 |
| 打包 | 一键 .bat 安装器 |

---

## 📄 开源协议

MIT License — 自由使用、修改、分发。
