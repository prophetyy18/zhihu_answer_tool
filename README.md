# 知乎问答拆解分析系统

> 基于 AI 的知乎内容深度分析与知识卡片生成工具

[在线演示](https://nhs-percentage-kansas-competent.trycloudflare.com) | [Karpatkey](https://karpatkey.com)

---

## 功能特点

### 1. 知乎热榜实时获取
- 自动抓取知乎热榜前 3 条热门问题
- 本地缓存 24 小时，减少重复请求
- 支持一键刷新获取最新数据

### 2. 智能问答分析
输入任意知乎问题，AI 自动帮你拆解分析：

- **知识卡片生成** - 将复杂内容拆解为结构化的知识卡片
  - 核心概念卡：主题、定义、关键要点
  - 背景信息卡：时间线、涉及人物/机构、相关事件
  - 分析维度卡：多角度深度分析
  - 模板样文：可参考的写作框架

- **新角度推荐** - 基于全网搜索，给你一个独特的回答切入点

### 3. 并行搜索 + 流式响应
- 知乎搜索与全网搜索并行执行，速度提升约 50%
- 实时进度反馈，搜索状态一目了然
- AI 生成过程全程可见

### 4. 知乎 OAuth 登录
- 支持知乎账号授权登录
- 登录后显示用户头像和昵称

---

## 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                      前端 (HTML/CSS/JS)               │
│  · 终端风格界面  · 响应式布局  · SSE 流式接收        │
└─────────────────────┬───────────────────────────────┘
                      │ HTTP / SSE
┌─────────────────────▼───────────────────────────────┐
│                   Flask 后端                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐  │
│  │ 知乎 OAuth │ │ 知乎搜索API │ │ SearXNG    │  │
│  │   登录      │ │  热榜/问答  │ │  全网搜索   │  │
│  └─────────────┘ └─────────────┘ └─────────────┘  │
│                       │                               │
│              ┌───────▼───────┐                    │
│              │  ThreadPool   │                    │
│              │  并行执行      │                    │
│              └───────┬───────┘                    │
│                      │                            │
│              ┌───────▼───────┐                    │
│              │  MiniMax LLM  │                    │
│              │  知识卡片生成  │                    │
│              │  新角度推荐    │                    │
│              └───────────────┘                    │
└───────────────────────────────────────────────────┘
```

### 核心模块

| 模块 | 文件 | 说明 |
|------|------|------|
| Web 服务 | `app.py` | Flask 主应用，处理所有路由和业务逻辑 |
| 知乎 API | `zhihu_api.py` | 知乎搜索、热榜、问题详情接口 |
| 知乎 OAuth | `zhihu_oauth.py` | 知乎第三方登录授权 |
| 全网搜索 | `search_service.py` | SearXNG 搜索 + Crawl4ai 页面抓取 |
| LLM 服务 | `llm_service.py` | MiniMax API 调用，生成知识卡片 |
| 配置管理 | `config.py` | API Keys 和配置项 |

### API 设计

```
GET  /                          # 首页
GET  /auth/zhihu                # 跳转知乎授权
GET  /auth/zhihu/callback       # 授权回调
POST /auth/logout               # 退出登录

GET  /api/hot                   # 获取热榜
GET  /api/question?q=           # 搜索问题
POST /api/analyze                # 分析问题（串行备用）
POST /api/analyze/stream        # 分析问题（SSE流式）

GET  /api/me                    # 当前用户信息
GET  /api/followers             # 粉丝列表
GET  /api/following             # 关注列表
GET  /api/activities            # 关注动态
```

---

## 快速部署

### 环境要求
- Python 3.8+
- Redis 或自建 SearXNG 实例（可选）

### 安装步骤

```bash
# 克隆项目
git clone https://github.com/prophetyy18/zhihu_answer_tool.git
cd zhihu_answer_tool

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 API Keys

# 启动服务
python app.py
```

### 配置说明

在 `.env` 或 `config.py` 中配置：

```python
# 知乎 OAuth（需在知乎开放平台申请）
ZHIHU_OAUTH_APP_ID = "your_app_id"
ZHIHU_OAUTH_APP_KEY = "your_app_key"
ZHIHU_OAUTH_REDIRECT_URI = "https://your-domain.com/auth/zhihu/callback"

# 知乎开发者 API
ZHIHU_API_KEY = "your_zhihu_api_key"

# MiniMax LLM API
MINIMAX_API_KEY = "your_minimax_api_key"

# SearXNG 搜索（可选，自建或使用公共实例）
SEARXNG_URL = "http://localhost:8888"
```

---

## 使用示例

### 分析一个问题

1. 在搜索框输入问题，如"为什么年轻人不愿意结婚？"
2. 点击 ANALYZE 按钮
3. 系统自动完成：
   - 并行搜索知乎回答 + 全网相关内容
   - AI 生成结构化知识卡片
   - AI 推荐独特回答角度
4. 查看分析结果，复制使用

### 热榜分析

1. 首页展示知乎热榜前 3
2. 点击问题卡片展开详情
3. 点击 ANALYZE 深入分析

---

## 项目截图

```
┌────────────────────────────────────────────────┐
│ [ SYSTEM ] 知乎问答拆解分析                      │
│ > Karpatkey LLM WIKI · 智能拆解 · 新角度推荐     │
│                              [用户头像] 张三 [LOGOUT]│
├────────────────────────────────────────────────┤
│ HOT LIST // 前3                      [ REFRESH ] │
│ ┌──────────────────────────────────────────┐   │
│ │ 职场中，为什么有些能力最强的人...          │   │
│ │ LINK: zhihu.com/question/...   [ANALYZE] │   │
│ └──────────────────────────────────────────┘   │
│ ┌──────────────────────────────────────────┐   │
│ │ 为什么说年轻人不应该躺平？                │   │
│ │ LINK: zhihu.com/question/...   [ANALYZE] │   │
│ └──────────────────────────────────────────┘   │
├────────────────────────────────────────────────┤
│ > 搜索问题                                    │
│ [ 输入问题...                         ] [SEARCH] │
└────────────────────────────────────────────────┘
```

---

## License

MIT License - By [Karpatkey](https://karpatkey.com)
