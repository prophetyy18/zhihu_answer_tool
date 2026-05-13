"""
知乎 OAuth 2.0 处理模块
"""
import requests
from config import Config

ZHIHU_OAUTH_BASE = "https://openapi.zhihu.com"
ZHIHU_ACCESS_TOKEN_URL = "https://openapi.zhihu.com/access_token"


def get_authorize_url():
    """生成知乎授权 URL"""
    return (
        f"{ZHIHU_OAUTH_BASE}/authorize"
        f"?redirect_uri={Config.ZHIHU_OAUTH_REDIRECT_URI}"
        f"&app_id={Config.ZHIHU_OAUTH_APP_ID}"
        f"&response_type=code"
    )


def exchange_code_for_token(code):
    """用授权码换取 access_token"""
    url = ZHIHU_ACCESS_TOKEN_URL
    data = {
        "grant_type": "authorization_code",
        "app_id": Config.ZHIHU_OAUTH_APP_ID,
        "app_key": Config.ZHIHU_OAUTH_APP_KEY,
        "code": code,
        "redirect_uri": Config.ZHIHU_OAUTH_REDIRECT_URI,
    }
    try:
        response = requests.post(url, data=data, timeout=15)
        if response.status_code == 200:
            return response.json()
        return {"error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"error": str(e)}


def get_user_info(access_token):
    """获取当前授权用户基本信息"""
    url = f"{ZHIHU_OAUTH_BASE}/user"
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json()
        return {"error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"error": str(e)}


def get_followers(access_token, page=0, per_page=10):
    """获取粉丝列表"""
    url = f"{ZHIHU_OAUTH_BASE}/followers"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"page": page, "per_page": per_page}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            return response.json()
        return {"error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"error": str(e)}


def get_following(access_token, page=0, per_page=10):
    """获取关注列表"""
    url = f"{ZHIHU_OAUTH_BASE}/following"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"page": page, "per_page": per_page}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            return response.json()
        return {"error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"error": str(e)}


def get_activities(access_token, page=0, per_page=10):
    """获取关注动态"""
    url = f"{ZHIHU_OAUTH_BASE}/activities"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"page": page, "per_page": per_page}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            return response.json()
        return {"error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"error": str(e)}
