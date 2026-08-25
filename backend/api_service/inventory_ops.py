"""手动出入库、AI 识别结果确认/纠正接口。

这些是小程序需要、但此前后端完全没有的写操作：入库/出库写 inventory_log
并维护 stock_summary；确认/纠正针对已有的 inventory_log 行。纯服务端业务
逻辑，不涉及 camera_service / env_service / sync_service。
"""

from __future__ import annotations

from datetime import date, timedelta
import os
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException

from backend.api_service import ws_hub
from backend.api_service.auth import get_current_user_or_demo
from backend.api_service.helpers import (
    DB_PATH,
    allocate_local_id,
    connection_scope,
    inventory_rows,
    ok,
    query_one,
    recognition_row_by_id,
    safe_float,
)
from backend.sync_service.push import queue_board_operation

router = APIRouter()
BOARD_SOURCE_URL = os.environ.get("WAREHOUSE_BOARD_SOURCE_URL", "").strip()


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


def _resolve_inbound_produce(conn: Any, payload: dict[str, Any]) -> int:
    produce_id = payload.get("produceId") or payload.get("id")
    if produce_id:
        produce_id = int(produce_id)
        if not conn.execute(
            "SELECT id FROM produce_info WHERE id = ?", (produce_id,)
        ).fetchone():
            raise HTTPException(status_code=404, detail="果蔬信息不存在")
        return produce_id

    name = str(payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="缺少 produceId 或果蔬名称")
    category = str(payload.get("category") or "").strip()
    existing = conn.execute(
        "SELECT id FROM produce_info WHERE name = ? AND category = ? ORDER BY id LIMIT 1",
        (name, category),
    ).fetchone()
    if existing:
        return int(existing["id"])

    shelf_life = int(payload.get("shelfLife") or payload.get("shelfLifeDays") or 0)
    storage_advice = str(
        payload.get("storageAdvice") or payload.get("idealTempRange") or ""
    )
    produce_id = allocate_local_id(conn, "produce_info")
    conn.execute(
        """
        INSERT INTO produce_info
            (id, name, category, shelf_life_days, ideal_temp_range, icon_url,
             unit, location)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            produce_id,
            name,
            category,
            shelf_life,
            storage_advice,
            str(payload.get("iconUrl") or ""),
            str(payload.get("unit") or "件"),
            str(payload.get("location") or "本地库存"),
        ),
    )
    return produce_id


def _update_produce_fields(conn: Any, produce_id: int, payload: dict[str, Any]) -> None:
    current = conn.execute(
        """
        SELECT name, category, shelf_life_days, ideal_temp_range, icon_url,
               unit, location
        FROM produce_info
        WHERE id = ?
        """,
        (produce_id,),
    ).fetchone()
    if not current:
        raise HTTPException(status_code=404, detail="果蔬信息不存在")
    conn.execute(
        """
        UPDATE produce_info
        SET name = ?, category = ?, shelf_life_days = ?,
            ideal_temp_range = ?, icon_url = ?, unit = ?, location = ?
        WHERE id = ?
        """,
        (
            str(payload.get("name") or current["name"]).strip(),
            str(payload.get("category") or current["category"] or ""),
            int(
                payload.get("shelfLife")
                or payload.get("shelfLifeDays")
                or current["shelf_life_days"]
                or 0
            ),
            str(
                payload.get("storageAdvice")
                or payload.get("idealTempRange")
                or current["ideal_temp_range"]
                or ""
            ),
            str(payload.get("iconUrl") or current["icon_url"] or ""),
            str(payload.get("unit") or current["unit"] or "件"),
            str(payload.get("location") or current["location"] or "本地库存"),
            produce_id,
        ),
    )


def _sync_payload(
    conn: Any,
    produce_id: int,
    inventory_log_id: int | None = None,
) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT p.id, p.name, p.category, p.shelf_life_days,
               p.ideal_temp_range, p.icon_url, p.unit, p.location,
               COALESCE(s.current_qty, 0) AS current_qty,
               COALESCE(s.earliest_expire_date, '') AS earliest_expire_date
        FROM produce_info p
        LEFT JOIN stock_summary s ON s.produce_id = p.id
        WHERE p.id = ?
        """,
        (produce_id,),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="果蔬信息不存在")
    payload: dict[str, Any] = {
        "produce": {
            "id": int(row["id"]),
            "name": row["name"],
            "category": row["category"] or "",
            "shelfLifeDays": int(row["shelf_life_days"] or 0),
            "storageAdvice": row["ideal_temp_range"] or "",
            "iconUrl": row["icon_url"] or "",
            "unit": row["unit"] or "件",
            "location": row["location"] or "本地库存",
        },
        "stock": {
            "currentQty": float(row["current_qty"] or 0),
            "earliestExpireDate": row["earliest_expire_date"] or "",
        },
    }
    if inventory_log_id is not None:
        log = conn.execute(
            """
            SELECT id, action_type, quantity, freshness_level,
                   freshness_score, confidence, image_path, created_at
            FROM inventory_log
            WHERE id = ?
            """,
            (inventory_log_id,),
        ).fetchone()
        if log:
            payload["inventoryLog"] = {
                "id": int(log["id"]),
                "actionType": log["action_type"],
                "quantity": float(log["quantity"] or 0),
                "freshnessLevel": log["freshness_level"],
                "freshnessScore": log["freshness_score"],
                "confidence": log["confidence"],
                "imagePath": log["image_path"],
                "createdAt": log["created_at"],
            }
    return payload


def _queue_sync(
    conn: Any,
    operation_type: str,
    produce_id: int,
    inventory_log_id: int | None = None,
) -> None:
    if not BOARD_SOURCE_URL:
        return
    queue_board_operation(
        conn,
        operation_type,
        _sync_payload(conn, produce_id, inventory_log_id),
        inventory_log_id,
    )


def _inventory_item(produce_id: int) -> dict[str, Any] | None:
    return next((item for item in inventory_rows() if item["id"] == produce_id), None)


@router.post("/api/inventory/inbound")
async def inventory_inbound(
    payload: dict[str, Any] = Body(...),
    user_id: int = Depends(get_current_user_or_demo),
) -> dict[str, Any]:
    quantity = safe_float(payload.get("quantity"), 0)
    expire_date = payload.get("expireDate")
    if not expire_date:
        shelf_life = int(payload.get("shelfLife") or payload.get("shelfLifeDays") or 0)
        if shelf_life > 0:
            expire_date = (date.today() + timedelta(days=shelf_life)).isoformat()
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="quantity 必须大于 0")

    with connection_scope(DB_PATH) as conn:
        produce_id = _resolve_inbound_produce(conn, payload)
        _update_produce_fields(conn, produce_id, payload)
        log_id = allocate_local_id(conn, "inventory_log")
        conn.execute(
            """
            INSERT INTO inventory_log
                (id, produce_id, action_type, quantity, sync_status)
            VALUES (?, ?, 'IN', ?, 'local')
            """,
            (log_id, produce_id, quantity),
        )
        _upsert_stock_after_inbound(conn, produce_id, quantity, expire_date)
        _queue_sync(conn, "inventory.inbound", produce_id, log_id)

    await _broadcast_recognition(log_id)
    return ok(
        {
            "success": True,
            "produceId": produce_id,
            "data": recognition_row_by_id(log_id),
            "item": _inventory_item(produce_id),
        }
    )


@router.post("/api/inventory/outbound")
async def inventory_outbound(
    payload: dict[str, Any] = Body(...),
    user_id: int = Depends(get_current_user_or_demo),
) -> dict[str, Any]:
    produce_id = payload.get("produceId") or payload.get("id")
    quantity = safe_float(payload.get("quantity"), 0)
    if not produce_id or quantity <= 0:
        raise HTTPException(status_code=400, detail="缺少 produceId 或 quantity 非法")
    produce_id = int(produce_id)
    if not query_one("SELECT id FROM produce_info WHERE id = ?", (produce_id,)):
        raise HTTPException(status_code=404, detail="果蔬信息不存在")

    with connection_scope(DB_PATH) as conn:
        log_id = allocate_local_id(conn, "inventory_log")
        conn.execute(
            """
            INSERT INTO inventory_log
                (id, produce_id, action_type, quantity, sync_status)
            VALUES (?, ?, 'OUT', ?, 'local')
            """,
            (log_id, produce_id, quantity),
        )
        _decrement_stock_after_outbound(conn, produce_id, quantity)
        _queue_sync(conn, "inventory.outbound", produce_id, log_id)

    await _broadcast_recognition(log_id)
    return ok(
        {
            "success": True,
            "data": recognition_row_by_id(log_id),
            "item": _inventory_item(produce_id),
        }
    )


@router.put("/api/inventory/{produce_id}")
async def inventory_update(
    produce_id: int,
    payload: dict[str, Any] = Body(...),
    user_id: int = Depends(get_current_user_or_demo),
) -> dict[str, Any]:
    desired_quantity = safe_float(payload.get("quantity"), -1)
    if desired_quantity < 0:
        raise HTTPException(status_code=400, detail="quantity 不能小于 0")

    log_id: int | None = None
    with connection_scope(DB_PATH) as conn:
        stock = conn.execute(
            "SELECT current_qty FROM stock_summary WHERE produce_id = ?",
            (produce_id,),
        ).fetchone()
        if not conn.execute(
            "SELECT id FROM produce_info WHERE id = ?", (produce_id,)
        ).fetchone():
            raise HTTPException(status_code=404, detail="库存记录不存在")
        current_quantity = safe_float(stock["current_qty"] if stock else 0)
        _update_produce_fields(conn, produce_id, payload)

        delta = desired_quantity - current_quantity
        if abs(delta) > 1e-9:
            log_id = allocate_local_id(conn, "inventory_log")
            action_type = "IN" if delta > 0 else "OUT"
            conn.execute(
                """
                INSERT INTO inventory_log
                    (id, produce_id, action_type, quantity, sync_status)
                VALUES (?, ?, ?, ?, 'local')
                """,
                (log_id, produce_id, action_type, abs(delta)),
            )

        expire_date = payload.get("expireDate")
        if not expire_date:
            shelf_life = int(payload.get("shelfLife") or 0)
            if shelf_life > 0:
                expire_date = (date.today() + timedelta(days=shelf_life)).isoformat()
        conn.execute(
            """
            INSERT INTO stock_summary
                (produce_id, current_qty, earliest_expire_date, last_updated)
            VALUES (?, ?, ?, datetime('now', 'localtime'))
            ON CONFLICT(produce_id) DO UPDATE SET
                current_qty = excluded.current_qty,
                earliest_expire_date = excluded.earliest_expire_date,
                last_updated = excluded.last_updated
            """,
            (produce_id, desired_quantity, expire_date or ""),
        )
        _queue_sync(conn, "inventory.update", produce_id, log_id)

    if log_id is not None:
        await _broadcast_recognition(log_id)
    return ok({"success": True, "item": _inventory_item(produce_id)})


@router.delete("/api/inventory/{produce_id}")
async def inventory_delete(
    produce_id: int,
    user_id: int = Depends(get_current_user_or_demo),
) -> dict[str, Any]:
    log_id: int | None = None
    with connection_scope(DB_PATH) as conn:
        stock = conn.execute(
            "SELECT current_qty FROM stock_summary WHERE produce_id = ?",
            (produce_id,),
        ).fetchone()
        if not conn.execute(
            "SELECT id FROM produce_info WHERE id = ?", (produce_id,)
        ).fetchone():
            raise HTTPException(status_code=404, detail="库存记录不存在")
        current_quantity = safe_float(stock["current_qty"] if stock else 0)
        if current_quantity > 0:
            log_id = allocate_local_id(conn, "inventory_log")
            conn.execute(
                """
                INSERT INTO inventory_log
                    (id, produce_id, action_type, quantity, sync_status)
                VALUES (?, ?, 'OUT', ?, 'local')
                """,
                (log_id, produce_id, current_quantity),
            )
        conn.execute(
            """
            INSERT INTO stock_summary
                (produce_id, current_qty, earliest_expire_date, last_updated)
            VALUES (?, 0, '', datetime('now', 'localtime'))
            ON CONFLICT(produce_id) DO UPDATE SET
                current_qty = 0,
                last_updated = excluded.last_updated
            """,
            (produce_id,),
        )
        _queue_sync(conn, "inventory.delete", produce_id, log_id)

    if log_id is not None:
        await _broadcast_recognition(log_id)
    return ok({"success": True, "produceId": produce_id})


@router.post("/api/recognitions/confirm")
def recognitions_confirm(
    payload: dict[str, Any] = Body(...),
    user_id: int = Depends(get_current_user_or_demo),
) -> dict[str, Any]:
    log_id = payload.get("id") or payload.get("frameId")
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
    user_id: int = Depends(get_current_user_or_demo),
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
