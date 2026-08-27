"""微信登录 (code2Session) 与设备绑定。

纯服务端业务逻辑，与开发板采集/控制代码无关：只新增 app_user / auth_session /
user_device 三张表的读写，不涉及 camera_service / env_service / sync_service。
"""

from __future__ import annotations

import json
import os
import secrets
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, Header, HTTPException

from backend.api_service.helpers import connection_scope, ok, query_one, DB_PATH

WECHAT_APPID = os.environ.get("WAREHOUSE_WECHAT_APPID", "")
WECHAT_APP_SECRET = os.environ.get("WAREHOUSE_WECHAT_APP_SECRET", "")
ALLOW_DEMO_LOGIN = os.environ.get("WAREHOUSE_ALLOW_DEMO_LOGIN", "false").lower() in {
    "1",
    "true",
    "yes",
}
SESSION_TTL_DAYS = int(os.environ.get("WAREHOUSE_SESSION_TTL_DAYS", "7"))
WECHAT_CODE2SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session"

router = APIRouter()


def wechat_code2session(code: str) -> dict[str, Any]:
    """调用微信 code2Session 接口，用 wx.login() 拿到的 code 换取 openid。"""
    if not WECHAT_APPID or not WECHAT_APP_SECRET:
        raise HTTPException(
            status_code=500,
            detail="服务端未配置 WAREHOUSE_WECHAT_APPID / WAREHOUSE_WECHAT_APP_SECRET",
        )
    query = urllib.parse.urlencode(
        {
            "appid": WECHAT_APPID,
            "secret": WECHAT_APP_SECRET,
            "js_code": code,
            "grant_type": "authorization_code",
        }
    )
    url = f"{WECHAT_CODE2SESSION_URL}?{query}"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise HTTPException(status_code=502, detail=f"无法连接微信登录服务: {exc}") from exc

    if payload.get("errcode"):
        raise HTTPException(
            status_code=400,
            detail=f"微信登录失败: {payload.get('errcode')} {payload.get('errmsg')}",
        )
    if not payload.get("openid"):
        raise HTTPException(status_code=502, detail="微信登录服务未返回 openid")
    return payload


def get_current_user(authorization: Optional[str] = Header(None)) -> int:
    """从 Authorization: Bearer <token> 中解析出当前用户 id。"""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="缺少登录凭证")
    token = authorization.split(" ", 1)[1].strip()
    row = query_one(
        """
        SELECT user_id FROM auth_session
        WHERE token = ? AND expires_at > datetime('now', 'localtime')
        """,
        (token,),
    )
    if not row:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    return int(row["user_id"])


def get_current_user_or_demo(
    authorization: Optional[str] = Header(None),
) -> int:
    """Allow the local Web admin to write only when demo mode is enabled."""
    if not authorization and ALLOW_DEMO_LOGIN:
        return 0
    return get_current_user(authorization)


@router.post("/api/auth/wechat-login")
def wechat_login(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    code = str(payload.get("code") or "").strip()
    demo_requested = str(payload.get("scene") or "").strip().lower() == "demo"
    if demo_requested and ALLOW_DEMO_LOGIN:
        session = {"openid": "warehouse-local-demo-user"}
    else:
        if not code:
            raise HTTPException(status_code=400, detail="缺少微信登录 code")
        session = wechat_code2session(code)
    openid = session["openid"]
    nickname = str(
        payload.get("nickName")
        or ("本地演示用户" if demo_requested and ALLOW_DEMO_LOGIN else "")
    )
    avatar_url = str(payload.get("avatarUrl") or "")

    with connection_scope(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO app_user (openid, nickname, avatar_url)
            VALUES (?, ?, ?)
            ON CONFLICT(openid) DO UPDATE SET
                nickname = excluded.nickname,
                avatar_url = excluded.avatar_url
            WHERE excluded.nickname != '' OR excluded.avatar_url != ''
            """,
            (openid, nickname, avatar_url),
        )
        user_row = conn.execute(
            "SELECT id, nickname, avatar_url FROM app_user WHERE openid = ?",
            (openid,),
        ).fetchone()
        user_id = user_row["id"]

        token = secrets.token_hex(32)
        conn.execute(
            """
            INSERT INTO auth_session (token, user_id, expires_at)
            VALUES (?, ?, datetime('now', 'localtime', ?))
            """,
            (token, user_id, f"+{SESSION_TTL_DAYS} days"),
        )

    return ok(
        {
            "token": token,
            "userInfo": {
                "nickName": user_row["nickname"] or "",
                "avatarUrl": user_row["avatar_url"] or "",
                "familyName": "本地联调环境" if demo_requested and ALLOW_DEMO_LOGIN else "",
            },
        }
    )


@router.post("/api/devices/bind")
def bind_device(
    payload: dict[str, Any] = Body(...),
    user_id: int = Depends(get_current_user),
) -> dict[str, Any]:
    device_id = str(payload.get("deviceCode") or "").strip()
    if not device_id:
        raise HTTPException(status_code=400, detail="缺少设备编号")

    with connection_scope(DB_PATH) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO user_device (user_id, device_id) VALUES (?, ?)",
            (user_id, device_id),
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO device_status (device_id, camera_status, sensor_status, storage_free, last_heartbeat)
            VALUES (?, NULL, NULL, NULL, NULL)
            """,
            (device_id,),
        )

    return ok({"success": True, "deviceId": device_id})
