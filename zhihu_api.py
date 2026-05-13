import time
import requests
from bs4 import BeautifulSoup
from config import Config

ZHIHU_API_BASE = "https://developer.zhihu.com/api/v1"

def get_headers():
    return {
        "Authorization": f"Bearer {Config.ZHIHU_API_KEY}",
        "X-Request-Timestamp": str(int(time.time())),
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

def search_zhihu(query, limit=10):
    """使用知乎搜索API搜索内容"""
    try:
        import urllib.parse
        encoded_query = urllib.parse.quote(query)
        url = f"{ZHIHU_API_BASE}/content/zhihu_search?Query={encoded_query}&Count={limit}"
        response = requests.get(url, headers=get_headers(), timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get("Code") == 0:
                items = data.get("Data", {}).get("Items", [])
                results = []
                for item in items:
                    results.append({
                        "title": item.get("Title", ""),
                        "content_type": item.get("ContentType", ""),
                        "content_id": item.get("ContentID", ""),
                        "content_text": item.get("ContentText", ""),
                        "url": item.get("Url", ""),
                        "voteup_count": item.get("VoteUpCount", 0),
                        "comment_count": item.get("CommentCount", 0),
                        "author_name": item.get("AuthorName", ""),
                        "edit_time": item.get("EditTime", 0)
                    })
                return {"data": results}
        return {"data": [], "error": f"API error: {response.status_code}"}
    except Exception as e:
        return {"data": [], "error": str(e)}

def get_hot_questions(limit=3):
    """获取热榜问题"""
    try:
        response = requests.get(
            f"{ZHIHU_API_BASE}/content/hot_list",
            headers=get_headers(),
            params={"Limit": limit},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("Code") == 0:
                items = data.get("Data", {}).get("Items", [])
                questions = []
                for item in items:
                    url = item.get("Url", "")
                    qid = ""
                    if "/question/" in url:
                        qid = url.split("/question/")[-1]
                    elif "/p/" in url:
                        qid = url.split("/p/")[-1]
                    questions.append({
                        "id": qid,
                        "title": item.get("Title", ""),
                        "excerpt": item.get("Summary", ""),
                        "url": url,
                        "thumbnail": item.get("ThumbnailUrl", "")
                    })
                return {"data": questions}
        return {"data": [], "error": f"API error: {response.status_code} - {response.text}"}
    except Exception as e:
        return {"data": [], "error": str(e)}

async def crawl_zhihu_question(question_id, max_answers=10):
    """直接爬取知乎问题页面，抓取问题和回答内容"""
    import asyncio
    import os
    import signal
    url = f"https://www.zhihu.com/question/{question_id}"
    answers_url = f"https://www.zhihu.com/question/{question_id}/answers?sort_by=voteup_count"

    try:
        from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

        results = {"question": {}, "answers": []}

        # 配置爬虫参数
        crawl_config = CrawlerRunConfig(
            cache_mode="bypass",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            override_navigator=True,
            page_timeout=20000
        )

        # 爬取问题页面
        async with AsyncWebCrawler() as crawler:
            question_result = await crawler.arun(url=url, config=crawl_config)
            if question_result and question_result.markdown:
                results["question"] = {
                    "url": url,
                    "content": question_result.markdown
                }

            # 爬回答（取排序最高的几个）
            answers_result = await crawler.arun(url=answers_url, config=crawl_config)
            if answers_result and answers_result.markdown:
                results["answers"] = parse_answers_from_markdown(answers_result.markdown, max_answers)

        return results
    except asyncio.TimeoutError:
        return {"error": "爬取超时，请重试", "question": {}, "answers": []}
    except Exception as e:
        return {"error": f"爬取失败: {str(e)}", "question": {}, "answers": []}

def parse_answers_from_markdown(markdown_content, max_answers):
    """从markdown中解析回答内容"""
    answers = []
    lines = markdown_content.split("\n")
    current_answer = ""

    for line in lines:
        # 知乎回答通常以"赞同"数字开头或者是段落
        if "赞同" in line or current_answer:
            current_answer += line + "\n"
            # 检查是否结束当前回答（遇到下一个回答或者太长了）
            if len(current_answer) > 3000 or "回答" in line:
                if current_answer.strip():
                    answers.append(current_answer.strip())
                    if len(answers) >= max_answers:
                        break
                current_answer = ""

    # 如果还有剩余内容
    if current_answer.strip() and len(answers) < max_answers:
        answers.append(current_answer.strip())

    return answers

def get_question_detail(question_id):
    """获取指定问题的详情"""
    try:
        response = requests.get(
            f"https://api.zhihu.com/v4/questions/{question_id}",
            headers={
                "Authorization": f"Bearer {Config.ZHIHU_API_KEY}",
                "User-Agent": "Mozilla/5.0"
            },
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API error: {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def get_question_answers(question_id, limit=5):
    """获取问题的回答"""
    try:
        response = requests.get(
            f"https://api.zhihu.com/v4/questions/{question_id}/answers",
            headers={
                "Authorization": f"Bearer {Config.ZHIHU_API_KEY}",
                "User-Agent": "Mozilla/5.0"
            },
            params={"limit": limit, "sort_by": "voteup_count"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"data": [], "error": f"API error: {response.status_code}"}
    except Exception as e:
        return {"data": [], "error": str(e)}
