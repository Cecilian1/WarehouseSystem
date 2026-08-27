"""Reliable, idempotent computer-to-board inventory synchronization."""

from __future__ import annotations

import json
from datetime import datetime
import urllib.error
import urllib.request
import uuid
from typing import Any

from backend.common.db import connection_scope


def queue_board_operation(
    conn: Any,
    operation_type: str,
    payload: dict[str, Any],
    inventory_log_id: int | None = None,
) -> str:
    operation_id = uuid.uuid4().hex
    body = {
        **payload,
        "operationId": operation_id,
        "operationType": operation_type,
    }
    conn.execute(
        """
        INSERT INTO board_sync_outbox
            (operation_id, operation_type, payload_json, inventory_log_id)
        VALUES (?, ?, ?, ?)
        """,
        (
            operation_id,
            operation_type,
            json.dumps(body, ensure_ascii=False),
            inventory_log_id,
        ),
    )
    return operation_id


def _validated_produce(payload: dict[str, Any]) -> dict[str, Any]:
    produce = payload.get("produce")
    if not isinstance(produce, dict):
        raise ValueError("produce must be an object")
    produce_id = int(produce.get("id"))
    name = str(produce.get("name") or "").strip()
    if not name:
        raise ValueError("produce.name is required")
    return {
        "id": produce_id,
        "name": name,
        "category": str(produce.get("category") or ""),
        "shelf_life_days": int(produce.get("shelfLifeDays") or 0),
        "ideal_temp_range": str(produce.get("storageAdvice") or ""),
        "icon_url": str(produce.get("iconUrl") or ""),
        "unit": str(produce.get("unit") or "件"),
        "location": str(produce.get("location") or "本地库存"),
    }


def apply_remote_operation(db_path: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Apply one computer operation on the board exactly once."""
    operation_id = str(payload.get("operationId") or "").strip()
    operation_type = str(payload.get("operationType") or "").strip()
    if not operation_id or not operation_type:
        raise ValueError("operationId and operationType are required")

    produce = _validated_produce(payload)
    stock = payload.get("stock")
    if not isinstance(stock, dict):
        raise ValueError("stock must be an object")
    current_qty = max(0.0, float(stock.get("currentQty") or 0))
    expire_date = str(stock.get("earliestExpireDate") or "")
    inventory_log = payload.get("inventoryLog")

    with connection_scope(db_path) as conn:
        applied = conn.execute(
            "SELECT operation_id FROM applied_remote_operation WHERE operation_id = ?",
            (operation_id,),
        ).fetchone()
        if applied:
            return {"applied": False, "duplicate": True, "operationId": operation_id}

        conn.execute(
            """
            INSERT INTO produce_info
                (id, name, category, shelf_life_days, ideal_temp_range,
                 icon_url, unit, location)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                category = excluded.category,
                shelf_life_days = excluded.shelf_life_days,
                ideal_temp_range = excluded.ideal_temp_range,
                icon_url = excluded.icon_url,
                unit = excluded.unit,
                location = excluded.location
            """,
            tuple(produce.values()),
        )

        if isinstance(inventory_log, dict):
            conn.execute(
                """
                INSERT OR IGNORE INTO inventory_log
                    (id, produce_id, action_type, quantity, freshness_level,
                     freshness_score, confidence, image_path, created_at,
                     sync_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'remote')
                """,
                (
                    int(inventory_log["id"]),
                    produce["id"],
                    str(inventory_log.get("actionType") or "IN"),
                    float(inventory_log.get("quantity") or 0),
                    inventory_log.get("freshnessLevel"),
                    inventory_log.get("freshnessScore"),
                    inventory_log.get("confidence"),
                    inventory_log.get("imagePath"),
                    inventory_log.get("createdAt")
                    or datetime.now().isoformat(sep=" ", timespec="seconds"),
                ),
            )

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
            (produce["id"], current_qty, expire_date),
        )
        conn.execute(
            """
            INSERT INTO applied_remote_operation (operation_id, operation_type)
            VALUES (?, ?)
            """,
            (operation_id, operation_type),
        )

    return {"applied": True, "duplicate": False, "operationId": operation_id}


def push_pending_operations(
    board_url: str,
    local_db_path: str,
    batch_size: int = 50,
) -> dict[str, int]:
    """Push queued operations and retain failures for the next collector cycle."""
    with connection_scope(local_db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, operation_id, payload_json, inventory_log_id
            FROM board_sync_outbox
            WHERE status IN ('pending', 'failed')
            ORDER BY id
            LIMIT ?
            """,
            (batch_size,),
        ).fetchall()

    pushed = 0
    failed = 0
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for row in rows:
        request = urllib.request.Request(
            f"{board_url.rstrip('/')}/api/sync/import",
            data=str(row["payload_json"]).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with opener.open(request, timeout=12) as response:
                result = json.loads(response.read().decode("utf-8"))
            if result.get("code") != 0:
                raise RuntimeError(f"板端回传失败: {result}")
        except (
            urllib.error.URLError,
            urllib.error.HTTPError,
            TimeoutError,
            OSError,
            ValueError,
            RuntimeError,
        ) as exc:
            failed += 1
            with connection_scope(local_db_path) as conn:
                conn.execute(
                    """
                    UPDATE board_sync_outbox
                    SET status = 'failed',
                        attempts = attempts + 1,
                        last_error = ?
                    WHERE id = ?
                    """,
                    (str(exc)[:500], int(row["id"])),
                )
            continue

        pushed += 1
        with connection_scope(local_db_path) as conn:
            conn.execute(
                """
                UPDATE board_sync_outbox
                SET status = 'synced',
                    attempts = attempts + 1,
                    last_error = '',
                    synced_at = datetime('now', 'localtime')
                WHERE id = ?
                """,
                (int(row["id"]),),
            )
            if row["inventory_log_id"] is not None:
                conn.execute(
                    """
                    UPDATE inventory_log
                    SET sync_status = 'synced'
                    WHERE id = ? AND sync_status = 'local'
                    """,
                    (int(row["inventory_log_id"]),),
                )
    return {"pushed": pushed, "failed": failed, "pending": len(rows) - pushed}
