import time
import requests
from config import Config

MINIMAX_API_URL = "https://api.minimax.chat/v1/text/chatcompletion_v2"
MINIMAX_MODEL = "MiniMax-M2.7"

SYSTEM_PROMPT = """你是一位知识管理专家，擅长将复杂信息拆解成结构化的知识卡片。

Karpatkey 的 LLM WIKI 视角核心原则：
1. **原子化**: 每个知识点独立存在，可以单独引用
2. **关联性**: 知识点之间通过链接形成知识网络
3. **人性化解读**: 用通俗语言解释专业概念，让普通人也能理解
4. **实用性**: 知识最终要能指导实践

请根据给定的知乎问题内容，生成符合以下格式的知识卡片：

## 知识卡片格式

### 核心概念卡
- 主题：
- 定义：
- 关键要点（3-5条）：

### 背景信息卡
- 时间线：
- 涉及人物/机构：
- 相关事件：

### 分析维度卡
- 角度1：xxx
- 角度2：xxx
- 角度3：xxx

### 新视角推荐
基于网上搜索结果，推荐一个新颖的回答角度：

### 模板样文
给出一个简洁的写作模板：
"""

def generate_knowledge_cards(question_title, question_content, answers_content):
    """生成知识卡片"""
    prompt = f"""请分析以下知乎问题，生成知识卡片：

问题标题：{question_title}
问题内容：{question_content}

回答摘要：{answers_content[:2000] if answers_content else '暂无回答'}

请按照格式生成知识卡片。"""

    return chat_with_minimax(prompt, system_prompt=SYSTEM_PROMPT)

def generate_new_angle(question_title, question_content, search_results):
    """基于搜索结果生成新的回答角度"""
    prompt = f"""基于以下搜索结果，为这个问题推荐一个新颖的回答角度：

问题：{question_title}
问题详情：{question_content}

网上搜索到的相关信息：
{search_results[:3000] if search_results else '暂无搜索结果'}

请从人性化的角度，给出一个独特且有价值的回答角度，简洁有力。"""

    return chat_with_minimax(prompt, system_prompt="你是一个有深度洞察的内容策划专家，擅长发现独特的写作角度。")

def chat_with_minimax(prompt, system_prompt="", max_retries=3):
    """调用 MiniMax API with retry logic"""
    headers = {
        "Authorization": f"Bearer {Config.MINIMAX_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MINIMAX_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 4000
    }

    for attempt in range(max_retries):
        try:
            response = requests.post(
                MINIMAX_API_URL,
                headers=headers,
                json=payload,
                timeout=120
            )
            if response.status_code == 200:
                result = response.json()
                choices = result.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
                return "MiniMax API 返回格式异常"
            elif response.status_code == 429:
                # Rate limited - wait and retry
                wait_time = (attempt + 1) * 10
                time.sleep(wait_time)
                continue
            else:
                return f"MiniMax API 错误: {response.status_code} - {response.text}"
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 15
                time.sleep(wait_time)
                continue
            return "请求 MiniMax API 超时，请稍后重试"
        except requests.exceptions.ConnectionError as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                time.sleep(wait_time)
                continue
            return f"连接 MiniMax API 失败: {str(e)}"
        except Exception as e:
            return f"请求 MiniMax API 失败: {str(e)}"

    return "MiniMax API 重试次数过多，请稍后重试"
