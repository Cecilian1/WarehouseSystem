"""系统设置的持久化：把此前的 POST /api/settings 空实现换成真正落库 + 回显。"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Body

from backend.api_service.helpers import DB_PATH, connection_scope, ok, query_one

router = APIRouter()

SETTINGS_KEY = "global"


@router.get("/api/settings")
def get_settings() -> dict[str, Any]:
    row = query_one("SELECT value FROM app_setting WHERE key = ?", (SETTINGS_KEY,))
    if not row:
        return ok({})
    try:
        return ok(json.loads(row["value"]))
    except (TypeError, ValueError):
        return ok({})


@router.post("/api/settings")
def save_settings(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    with connection_scope(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO app_setting (key, value, updated_at)
            VALUES (?, ?, datetime('now', 'localtime'))
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (SETTINGS_KEY, json.dumps(payload, ensure_ascii=False)),
        )
    return ok(payload)
