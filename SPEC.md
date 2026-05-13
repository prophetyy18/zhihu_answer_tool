# 知乎问答拆解分析系统 SPEC

## 1. Project Overview

- **Project Name**: 知乎 Top Writer
- **Type**: 知乎问答分析 + 生成工具 (Web App)
- **Core Functionality**: 对知乎热榜问题进行拆解、评价，并推荐新的写作角度和模板样文
- **Target Users**: 知乎内容创作者、需要分析知乎问题的人群

## 2. 技术栈

- **Frontend**: 纯 HTML + CSS + JavaScript (无框架)
- **Backend**: Python Flask
- **LLM API**: Anthropic Claude API (Karpatkey LLM WIKI 视角)
- **Search**: SearXNG + Crawl4ai
- **Zhihu API**: 知乎官方开发者 API

## 3. 功能需求

### 3.1 首页 (index.html)
- 显示知乎热榜前3问题（折叠展示）
- 点击展开为子页面，显示详细内容
- 底部搜索框：输入问题数字ID进行搜索
- 响应式设计：适配手机端和电脑端

### 3.2 问题分析页面
- **知识卡片生成**: 使用 LLM WIKI 视角总结问题相关知识点
- **人性化解读**: 从普通读者角度评价回答
- **新角度推荐**: 基于网上搜索给出新颖回答角度
- **模板样文**: 提供可参考的写作模板

### 3.3 后端 API
- `GET /api/hot` - 获取热榜前3
- `GET /api/question/<id>` - 获取指定问题详情
- `POST /api/analyze` - 分析问题，生成知识卡片和新角度

## 4. 知乎 API Key

```
key=3ca0bdca7595378836136077298bddf849dd4783
```

## 5. 页面布局

### 5.1 顶部区域
- 系统标题
- 简短描述

### 5.2 热榜区域
- 3个热榜问题卡片（折叠状态）
- 点击展开详情

### 5.3 搜索区域
- 输入框：输入问题ID
- 搜索按钮
- 位置：页面底部

## 6. 响应式设计

- **Mobile**: 单列布局，全宽卡片
- **Desktop**: 居中布局，最大宽度 800px

## 7. 文件结构

```
/home/zhihu/zhihu-top-writer/
├── app.py              # Flask 后端
├── requirements.txt    # Python 依赖
├── static/
│   └── style.css       # 样式文件
├── templates/
│   ├── index.html      # 首页
│   └── analysis.html   # 分析页面
└── SPEC.md
```
