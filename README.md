# ClipSnap 🖇️

**网页一键转 Markdown · 知识收藏从未如此简单**

点击一下，把任何网页变成干净、可搜索的 Markdown。支持微信公众号、知乎、CSDN、Medium 等平台的智能内容提取。

## ✨ 功能

- 🔌 **Chrome 扩展** — 一键抓取当前网页为 Markdown
- 🌐 **Web 管理面板** — 浏览/搜索/导出所有收藏
- 🤖 **AI 智能摘要** — 可选调用 LLM 自动生成文章摘要
- 📱 **公众号优化** — 自动转换为公众号排版格式
- 🏠 **完全自托管** — 数据在你自己的服务器上

## 🚀 快速开始

```bash
# 1. 安装后端
cd backend
pip install -r requirements.txt
python main.py

# 2. 打开 http://localhost:8710 进入管理面板

# 3. 加载 Chrome 扩展
# Chrome → 扩展程序 → 开发者模式 → 加载已解压的扩展程序 → 选择 extension/ 目录
```

## 📁 项目结构

```
clipsnap/
├── backend/          # Python FastAPI 后端
│   ├── main.py       # API 服务入口
│   ├── extractor.py  # 网页内容提取引擎
│   └── converter.py  # HTML → Markdown 转换
├── extension/        # Chrome 浏览器扩展
│   ├── manifest.json
│   ├── popup.html    # 弹出窗口
│   ├── popup.js      # 弹出逻辑
│   └── content.js    # 网页内容抓取
└── web/              # Web 管理面板前端
    └── index.html    # 单页应用
```

## 💰 变现模式

- 开源自部署免费
- 官方托管版 $5/月（无限收藏 + AI 摘要）
- Chrome Web Store 付费版 $9.99 一次性买断

## 📄 开源协议

MIT License
