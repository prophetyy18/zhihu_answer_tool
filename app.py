from flask import Flask, render_template, jsonify, request, Response, session, redirect, url_for
from config import Config
from zhihu_api import get_hot_questions, search_zhihu
from search_service import search_web
from llm_service import generate_knowledge_cards, generate_new_angle
from zhihu_oauth import get_authorize_url, exchange_code_for_token, get_user_info, get_followers, get_following, get_activities
import time
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# Thread pool for parallel execution
executor = ThreadPoolExecutor(max_workers=4)

# Server cache
_hot_cache = {"data": None, "timestamp": 0}
HOT_CACHE_TTL = 86400

MOCK_HOT_DATA = [
    {"id": "2036558081312679727", "title": "职场中，为什么有些能力最强的人往往最先离职？", "excerpt": "在职场中，我们常常会发现这样一个现象：那些能力最强、业绩最好的人，反而更容易选择离开...", "url": "https://www.zhihu.com/question/2036558081312679727"},
    {"id": "3996888392882994975", "title": "为什么说年轻人不应该躺平？", "excerpt": "躺平，这个词在2021年迅速走红，成为网络上热议的话题。年轻人选择躺平，究竟是...", "url": "https://www.zhihu.com/question/3996888392882994975"},
    {"id": "510842294288583219", "title": "月薪多少才能让你在北上广深过上体面的生活？", "excerpt": "北上广深作为中国最发达的四座城市，吸引了无数年轻人前来奋斗。但在这背后...", "url": "https://www.zhihu.com/question/510842294288583219"}
]

@app.route("/")
def index():
    # 处理 OAuth 回调（从知乎授权页回来时带 code）
    code = request.args.get("code") or request.args.get("authorization_code")
    if code and not session.get("access_token"):
        # 有 code 但没有登录态，说明是 OAuth 回调
        token_result = exchange_code_for_token(code)
        if "error" not in token_result and token_result.get("access_token"):
            access_token = token_result["access_token"]
            user_result = get_user_info(access_token)
            if "error" not in user_result:
                session["access_token"] = access_token
                session["user_info"] = user_result
                # 重定向到首页，清除 URL 中的 code
                return redirect("/")

    return render_template("index.html")

@app.route("/api/hot")
def api_hot():
    global _hot_cache
    now = time.time()
    if _hot_cache["data"] and (now - _hot_cache["timestamp"]) < HOT_CACHE_TTL:
        return jsonify({"success": True, "data": _hot_cache["data"], "mock": False, "cached": True})
    result = get_hot_questions(3)
    data = result.get("data", [])
    if data:
        _hot_cache = {"data": data, "timestamp": now}
        return jsonify({"success": True, "data": data, "mock": False, "cached": False})
    if _hot_cache["data"]:
        return jsonify({"success": True, "data": _hot_cache["data"], "mock": False, "cached": True})
    return jsonify({"success": True, "data": MOCK_HOT_DATA, "mock": True})

@app.route("/api/question")
def api_question():
    """通过知乎搜索API搜索问题"""
    import json
    import urllib.parse
    from zhihu_api import search_zhihu
    from flask import request

    # 获取查询参数
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({"success": False, "error": "查询参数不能为空"})

    # URL解码查询词
    try:
        query = urllib.parse.unquote(query)
    except:
        pass

    # 用知乎搜索API搜索
    result = search_zhihu(query, limit=10)
    items = result.get("data", [])

    if not items:
        return jsonify({
            "success": True,
            "data": {
                "title": query,
                "content": f"未找到与「{query}」相关的问题",
                "excerpt": f"未找到与「{query}」相关的问题"
            }
        })

    # 获取第一个结果
    first = items[0]
    title = first.get("title", query)
    if title.endswith(" - 知乎"):
        title = title[:-6]

    # 收集回答
    answers_content = []
    question_content = ""

    for item in items:
        if item.get("content_type") == "Answer":
            answers_content.append({
                "author": item.get("author_name", ""),
                "content": item.get("content_text", ""),
                "voteup": item.get("voteup_count", 0)
            })
        elif item.get("content_type") in ("Question", "Article"):
            if not question_content:
                question_content = item.get("content_text", "")

    return jsonify({
        "success": True,
        "data": {
            "title": title,
            "url": first.get("url", ""),
            "content": f"问题: {title}\n\n{question_content}",
            "excerpt": question_content[:300] if question_content else title,
            "answers": answers_content[:5]  # 最多返回5个回答
        }
    })

@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    """分析问题 - 串行版本（保留作为后备）"""
    import logging
    from zhihu_api import search_zhihu
    data = request.get_json()
    question_title = data.get("title", "")
    question_content = data.get("content", "")

    try:
        # 使用知乎搜索API获取问题和回答
        zhihu_results = search_zhihu(question_title, limit=10)
        zhihu_items = zhihu_results.get("data", [])

        # 收集知乎上的回答内容
        answers_content = []
        for item in zhihu_items:
            if item.get("content_type") == "Answer":
                answers_content.append(f"【{item.get('author_name', '匿名')}】{item.get('content_text', '')}")

        answers_text = "\n\n".join(answers_content[:10]) if answers_content else question_content

        # 使用SearXNG进行全局搜索
        search_results = search_web(question_title, question_url=None)

        # 生成知识卡片和新角度
        cards = generate_knowledge_cards(question_title, question_content, answers_text)
        angle = generate_new_angle(question_title, question_content, search_results)

        return jsonify({
            "success": True,
            "cards": cards if isinstance(cards, str) else "",
            "new_angle": angle,
            "search_results": search_results
        })
    except Exception as e:
        logging.error(f"Analyze error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/analyze/stream", methods=["POST"])
def api_analyze_stream():
    """分析问题 - SSE流式版本，实时推送进度"""
    data = request.get_json()
    question_title = data.get("title", "")
    question_content = data.get("content", "")

    def generate():
        try:
            # Step 1: 并行执行知乎搜索 + 网络搜索
            yield _sse_event("status", "正在并行搜索知乎和全网...")

            zhihu_future = executor.submit(search_zhihu, question_title, 10)
            web_future = executor.submit(search_web, question_title, None)

            # 等待两个搜索完成
            zhihu_results = zhihu_future.result()
            search_results = web_future.result()

            # 整理回答内容
            zhihu_items = zhihu_results.get("data", [])
            answers_content = []
            for item in zhihu_items:
                if item.get("content_type") == "Answer":
                    answers_content.append(f"【{item.get('author_name', '匿名')}】{item.get('content_text', '')}")

            answers_text = "\n\n".join(answers_content[:10]) if answers_content else question_content

            # 搜索完成，推送搜索摘要
            search_snippet = search_results[:300] + "..." if search_results and len(search_results) > 300 else (search_results or "")
            yield _sse_event("search_done", search_snippet)
            yield _sse_event("search_count", str(len(answers_content)))

            # 两个 LLM 并行生成 - 使用流式推送
            yield _sse_event("status", "AI 正在生成知识卡片和新角度，请稍候...")

            def generate_with_progress(question_title, question_content, answers_text, search_results):
                """生成内容，带进度回调"""
                # 由于 MiniMax API 不支持流式，我们先生成完整结果再推送
                # 但可以先发送"思考中"状态
                cards = generate_knowledge_cards(question_title, question_content, answers_text)
                yield {"type": "cards", "content": cards}

            # 并行执行两个 LLM
            import queue
            import threading

            results_queue = queue.Queue()

            def run_cards():
                cards = generate_knowledge_cards(question_title, question_content, answers_text)
                results_queue.put(("cards", cards))

            def run_angle():
                angle = generate_new_angle(question_title, question_content, search_results)
                results_queue.put(("angle", angle))

            cards_thread = threading.Thread(target=run_cards)
            angle_thread = threading.Thread(target=run_angle)

            cards_thread.start()
            angle_thread.start()

            # 等待两个完成，每完成一个就推送
            completed = 0
            results = {}
            while completed < 2:
                try:
                    key, value = results_queue.get(timeout=120)
                    results[key] = value
                    completed += 1
                    if key == "cards":
                        yield _sse_event("cards_done", value if isinstance(value, str) else "")
                    else:
                        yield _sse_event("angle_done", value)
                except queue.Empty:
                    yield _sse_event("error", "LLM 生成超时")
                    break

            cards_thread.join()
            angle_thread.join()

            cards = results.get("cards", "")
            angle = results.get("angle", "")

            yield _sse_event("done", json.dumps({"cards": cards if isinstance(cards, str) else "", "angle": angle}))

        except Exception as e:
            logging.error(f"Stream analyze error: {str(e)}")
            yield _sse_event("error", str(e))

    return Response(generate(), mimetype='text/event-stream')

def _sse_event(event_type, data):
    return f"event: {event_type}\ndata: {data}\n\n"

# ============== 知乎 OAuth 路由 ==============

@app.route("/auth/zhihu")
def auth_zhihu():
    """跳转知乎授权页"""
    authorize_url = get_authorize_url()
    return redirect(authorize_url)


@app.route("/auth/zhihu/callback")
def auth_zhihu_callback():
    """知乎授权回调"""
    code = request.args.get("code") or request.args.get("authorization_code")
    error = request.args.get("error")

    if error:
        return redirect("/?error=" + str(error))

    if not code:
        return redirect("/?error=missing_code")

    # 用 code 换取 access_token
    token_result = exchange_code_for_token(code)

    if "error" in token_result:
        return redirect("/?error=" + str(token_result["error"]))

    access_token = token_result.get("access_token")
    if not access_token:
        return redirect("/?error=no_token")

    # 获取用户信息
    user_result = get_user_info(access_token)

    if "error" in user_result:
        return redirect("/?error=" + str(user_result["error"]))

    # 存储到 session
    session["access_token"] = access_token
    session["user_info"] = user_result

    # 返回首页
    return redirect("/")


@app.route("/auth/logout", methods=["POST"])
def auth_logout():
    """退出登录"""
    session.pop("access_token", None)
    session.pop("user_info", None)
    return jsonify({"success": True})


@app.route("/api/me")
def api_me():
    """获取当前登录用户信息"""
    user_info = session.get("user_info")
    if not user_info:
        return jsonify({"success": False, "error": "Not logged in"})

    return jsonify({
        "success": True,
        "user": {
            "uid": user_info.get("uid"),
            "hash_id": user_info.get("hash_id"),
            "fullname": user_info.get("fullname"),
            "headline": user_info.get("headline"),
            "avatar_url": user_info.get("avatar_path"),
            "url": user_info.get("url"),
        }
    })


@app.route("/api/followers")
def api_followers():
    """获取粉丝列表"""
    access_token = session.get("access_token")
    if not access_token:
        return jsonify({"success": False, "error": "Not logged in"})

    page = request.args.get("page", 0, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    result = get_followers(access_token, page, per_page)
    if "error" in result:
        return jsonify({"success": False, "error": result["error"]})

    return jsonify({"success": True, "data": result})


@app.route("/api/following")
def api_following():
    """获取关注列表"""
    access_token = session.get("access_token")
    if not access_token:
        return jsonify({"success": False, "error": "Not logged in"})

    page = request.args.get("page", 0, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    result = get_following(access_token, page, per_page)
    if "error" in result:
        return jsonify({"success": False, "error": result["error"]})

    return jsonify({"success": True, "data": result})


@app.route("/api/activities")
def api_activities():
    """获取关注动态"""
    access_token = session.get("access_token")
    if not access_token:
        return jsonify({"success": False, "error": "Not logged in"})

    page = request.args.get("page", 0, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    result = get_activities(access_token, page, per_page)
    if "error" in result:
        return jsonify({"success": False, "error": result["error"]})

    return jsonify({"success": True, "data": result})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
