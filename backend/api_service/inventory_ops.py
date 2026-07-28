"""手动出入库、AI 识别结果确认/纠正接口。

这些是小程序需要、但此前后端完全没有的写操作：入库/出库写 inventory_log
并维护 stock_summary；确认/纠正针对已有的 inventory_log 行。纯服务端业务
逻辑，不涉及 camera_service / env_service / sync_service。
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException

from backend.api_service import ws_hub
from backend.api_service.auth import get_current_user
from backend.api_service.helpers import (
    DB_PATH,
    connection_scope,
    ok,
    query_one,
    recognition_row_by_id,
    safe_float,
)

router = APIRouter()


async def _broadcast_recognition(log_id: int) -> None:
    row = recognition_row_by_id(log_id)
    if row:
        await ws_hub.broadcast({"type": "recognition:new", "payload": row})


def _upsert_stock_after_inbound(conn, produce_id: int, quantity: float, expire_date: str | None) -> None:
    conn.execute(
        """
        INSERT INTO stock_summary (produce_id, current_qty, earliest_expire_date, last_updated)
        VALUES (?, ?, ?, datetime('now', 'localtime'))
        ON CONFLICT(produce_id) DO UPDATE SET
            current_qty = current_qty + excluded.current_qty,
            earliest_expire_date = CASE
                WHEN earliest_expire_date IS NULL OR earliest_expire_date = '' THEN excluded.earliest_expire_date
                WHEN excluded.earliest_expire_date IS NULL OR excluded.earliest_expire_date = '' THEN earliest_expire_date
                WHEN excluded.earliest_expire_date < earliest_expire_date THEN excluded.earliest_expire_date
                ELSE earliest_expire_date
            END,
            last_updated = datetime('now', 'localtime')
        """,
        (produce_id, quantity, expire_date or ""),
    )


def _decrement_stock_after_outbound(conn, produce_id: int, quantity: float) -> None:
    conn.execute(
        """
        UPDATE stock_summary
        SET current_qty = MAX(0, COALESCE(current_qty, 0) - ?), last_updated = datetime('now', 'localtime')
        WHERE produce_id = ?
        """,
        (quantity, produce_id),
    )


@router.post("/api/inventory/inbound")
async def inventory_inbound(
    payload: dict[str, Any] = Body(...),
    user_id: int = Depends(get_current_user),
) -> dict[str, Any]:
    produce_id = payload.get("produceId")
    quantity = safe_float(payload.get("quantity"), 0)
    expire_date = payload.get("expireDate")
    if not produce_id or quantity <= 0:
        raise HTTPException(status_code=400, detail="缺少 produceId 或 quantity 非法")
    if not query_one("SELECT id FROM produce_info WHERE id = ?", (produce_id,)):
        raise HTTPException(status_code=404, detail="果蔬信息不存在")

    with connection_scope(DB_PATH) as conn:
        cursor = conn.execute(
            """
            INSERT INTO inventory_log (produce_id, action_type, quantity, sync_status)
            VALUES (?, 'IN', ?, 'local')
            """,
            (produce_id, quantity),
        )
        log_id = int(cursor.lastrowid)
        _upsert_stock_after_inbound(conn, produce_id, quantity, expire_date)

    await _broadcast_recognition(log_id)
    return ok({"success": True, "data": recognition_row_by_id(log_id)})


@router.post("/api/inventory/outbound")
async def inventory_outbound(
    payload: dict[str, Any] = Body(...),
    user_id: int = Depends(get_current_user),
) -> dict[str, Any]:
    produce_id = payload.get("produceId")
    quantity = safe_float(payload.get("quantity"), 0)
    if not produce_id or quantity <= 0:
        raise HTTPException(status_code=400, detail="缺少 produceId 或 quantity 非法")
    if not query_one("SELECT id FROM produce_info WHERE id = ?", (produce_id,)):
        raise HTTPException(status_code=404, detail="果蔬信息不存在")

    with connection_scope(DB_PATH) as conn:
        cursor = conn.execute(
            """
            INSERT INTO inventory_log (produce_id, action_type, quantity, sync_status)
            VALUES (?, 'OUT', ?, 'local')
            """,
            (produce_id, quantity),
        )
        log_id = int(cursor.lastrowid)
        _decrement_stock_after_outbound(conn, produce_id, quantity)

    await _broadcast_recognition(log_id)
    return ok({"success": True, "data": recognition_row_by_id(log_id)})


@router.post("/api/recognitions/confirm")
def recognitions_confirm(
    payload: dict[str, Any] = Body(...),
    user_id: int = Depends(get_current_user),
) -> dict[str, Any]:
    log_id = payload.get("id")
    if log_id is None:
        raise HTTPException(status_code=400, detail="缺少识别记录 id")
    row = recognition_row_by_id(int(log_id))
    if not row:
        raise HTTPException(status_code=404, detail="识别记录不存在")
    # inventory_log 目前没有"已确认"标记列，最小实现只校验记录存在并原样回显。
    return ok({"success": True, "updated": row})


@router.put("/api/recognitions/target")
async def recognitions_update_target(
    payload: dict[str, Any] = Body(...),
    user_id: int = Depends(get_current_user),
) -> dict[str, Any]:
    log_id = payload.get("id")
    if log_id is None:
        raise HTTPException(status_code=400, detail="缺少识别记录 id")
    log_id = int(log_id)

    existing = query_one(
        "SELECT produce_id, action_type, quantity FROM inventory_log WHERE id = ?", (log_id,)
    )
    if not existing:
        raise HTTPException(status_code=404, detail="识别记录不存在")

    new_produce_id = payload.get("produceId", existing["produce_id"])
    new_freshness_level = payload.get("freshnessLevel")
    new_quantity = payload.get("quantity")

    with connection_scope(DB_PATH) as conn:
        conn.execute(
            """
            UPDATE inventory_log
            SET produce_id = ?, freshness_level = COALESCE(?, freshness_level), quantity = COALESCE(?, quantity)
            WHERE id = ?
            """,
            (new_produce_id, new_freshness_level, new_quantity, log_id),
        )

        # produce 或 quantity 变化时，先把旧值从 stock_summary 撤销，再按新值重新计入。
        quantity_changed = new_quantity is not None and safe_float(new_quantity) != safe_float(
            existing["quantity"]
        )
        if new_produce_id != existing["produce_id"] or quantity_changed:
            old_qty = safe_float(existing["quantity"])
            if existing["produce_id"]:
                if existing["action_type"] == "IN":
                    conn.execute(
                        """
                        UPDATE stock_summary
                        SET current_qty = MAX(0, COALESCE(current_qty, 0) - ?), last_updated = datetime('now', 'localtime')
                        WHERE produce_id = ?
                        """,
                        (old_qty, existing["produce_id"]),
                    )
                else:
                    conn.execute(
                        """
                        UPDATE stock_summary
                        SET current_qty = COALESCE(current_qty, 0) + ?, last_updated = datetime('now', 'localtime')
                        WHERE produce_id = ?
                        """,
                        (old_qty, existing["produce_id"]),
                    )

            new_qty = safe_float(new_quantity, old_qty)
            if new_produce_id:
                if existing["action_type"] == "IN":
                    _upsert_stock_after_inbound(conn, new_produce_id, new_qty, None)
                else:
                    _decrement_stock_after_outbound(conn, new_produce_id, new_qty)

    await _broadcast_recognition(log_id)
    return ok({"success": True, "data": recognition_row_by_id(log_id)})
