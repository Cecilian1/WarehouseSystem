"""Qwen-Flash function-calling client for read-only refrigerator queries."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from backend.api_service.helpers import alert_rows, environment_data, inventory_rows, recognition_rows


DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
SYSTEM_PROMPT = """你是芯鲜管家的“新鲜助手”，服务于智能冰箱用户。
回答必须使用简洁自然、适合直接语音播报的中文，不要使用Markdown、表格、星号或标题符号。
涉及冰箱实时数据时必须先调用工具，不得编造库存、温湿度、新鲜度或预警。
工具没有数据时如实说明。当前工具均为只读工具，不要声称已经修改库存或设备。"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_inventory",
            "description": "查询冰箱当前库存、数量、新鲜度和剩余保鲜天数",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_environment",
            "description": "查询冰箱当前温度、湿度和环境状态",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_pending_alerts",
            "description": "查询尚未处理的过期、临期或设备异常预警",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_recognitions",
            "description": "查询最近识别到的果蔬及其新鲜度",
            "parameters": {
                "type": "object",
                "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 20}},
            },
        },
    },
]


class QwenUnavailableError(RuntimeError):
    pass


class QwenRequestError(RuntimeError):
    pass


def api_key() -> str:
    return (
        os.environ.get("WAREHOUSE_QWEN_API_KEY", "").strip()
        or os.environ.get("QWEN_API_KEY", "").strip()
        or os.environ.get("DASHSCOPE_API_KEY", "").strip()
    )


def model_name() -> str:
    return (
        os.environ.get("WAREHOUSE_QWEN_MODEL", "").strip()
        or os.environ.get("QWEN_MODEL", "").strip()
        or "qwen-flash"
    )


def status() -> dict[str, Any]:
    return {
        "configured": bool(api_key()),
        "model": model_name(),
        "provider": "DashScope OpenAI-compatible API",
    }


def _execute_tool(name: str, arguments: dict[str, Any]) -> Any:
    if name == "get_inventory":
        return inventory_rows()[:50]
    if name == "get_environment":
        return environment_data()
    if name == "get_pending_alerts":
        return [item for item in alert_rows() if item.get("status") == "pending"][:20]
    if name == "get_recent_recognitions":
        limit = max(1, min(20, int(arguments.get("limit", 8))))
        return recognition_rows(limit=limit)
    return {"error": f"未知工具：{name}"}


def _request(messages: list[dict[str, Any]]) -> dict[str, Any]:
    key = api_key()
    if not key:
        raise QwenUnavailableError("尚未配置Qwen API Key")
    payload = json.dumps(
        {
            "model": model_name(),
            "messages": messages,
            "tools": TOOLS,
            "tool_choice": "auto",
            "temperature": 0.2,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        os.environ.get("WAREHOUSE_QWEN_BASE_URL", DEFAULT_BASE_URL),
        data=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[-1000:]
        raise QwenRequestError(f"Qwen接口返回HTTP {exc.code}：{detail}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise QwenRequestError(f"无法连接Qwen接口：{exc}") from exc
    try:
        return result["choices"][0]["message"]
    except (KeyError, IndexError, TypeError) as exc:
        raise QwenRequestError("Qwen接口返回格式异常") from exc


def chat(text: str, history: list[dict[str, str]] | None = None) -> dict[str, Any]:
    messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for item in (history or [])[-8:]:
        role = item.get("role")
        content = str(item.get("content") or "").strip()
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": content[:2000]})
    messages.append({"role": "user", "content": text})

    used_tools: list[str] = []
    for _ in range(3):
        message = _request(messages)
        tool_calls = message.get("tool_calls") or []
        if not tool_calls:
            reply = str(message.get("content") or "").strip()
            if not reply:
                raise QwenRequestError("Qwen没有返回回答")
            return {
                "reply": reply,
                "model": model_name(),
                "provider": "DashScope",
                "tools": used_tools,
            }

        messages.append(message)
        for call in tool_calls:
            function = call.get("function") or {}
            name = str(function.get("name") or "")
            try:
                arguments = json.loads(function.get("arguments") or "{}")
            except json.JSONDecodeError:
                arguments = {}
            used_tools.append(name)
            result = _execute_tool(name, arguments)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.get("id"),
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )
    raise QwenRequestError("Qwen工具调用次数过多，请换一种问法")
