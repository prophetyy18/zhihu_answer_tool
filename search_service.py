import requests
from config import Config

def search_web(query, limit=5, question_url=None):
    """使用 SearXNG 搜索网上信息"""
    try:
        if Config.SEARXNG_URL:
            # 拼接搜索query，加入问题URL增强搜索
            search_query = query
            if question_url:
                search_query = f"{query} site:zhihu.com {question_url}"

            response = requests.get(
                f"{Config.SEARXNG_URL}/search",
                params={"q": search_query, "format": "json", "limit": limit},
                timeout=15
            )
            if response.status_code == 200:
                results = response.json().get("results", [])
                return format_search_results(results)
        return "搜索引擎不可用"
    except Exception as e:
        return f"搜索失败: {str(e)}"

def format_search_results(results):
    """格式化搜索结果"""
    if not results:
        return "未找到相关结果"

    formatted = []
    for r in results[:5]:
        title = r.get("title", "")
        content = r.get("content", "")[:200]
        url = r.get("url", "")
        formatted.append(f"- {title}: {content}... (来源: {url})")

    return "\n".join(formatted)

async def crawl_page(url):
    """使用 Crawl4ai 抓取页面"""
    try:
        from crawl4ai import WebCrawler
        crawler = WebCrawler()
        result = await crawler.crawl(url)
        return result.markdown if hasattr(result, 'markdown') else str(result)
    except Exception as e:
        return f"抓取失败: {str(e)}"
