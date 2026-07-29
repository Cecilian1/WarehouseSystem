"""Validate and idempotently apply data pulled from a development board."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from backend.common.db import connection_scope
from backend.common.init_db import init_db


TABLE_COLUMNS: dict[str, tuple[str, ...]] = {
    "produce_info": (
        "id",
        "name",
        "category",
        "shelf_life_days",
        "ideal_temp_range",
        "icon_url",
        "unit",
        "location",
    ),
    "inventory_log": (
        "id",
        "produce_id",
        "action_type",
        "quantity",
        "freshness_level",
        "freshness_score",
        "confidence",
        "image_path",
        "created_at",
        "sync_status",
    ),
    "stock_summary": (
        "produce_id",
        "current_qty",
        "earliest_expire_date",
        "last_updated",
    ),
    "alert_record": (
        "id",
        "produce_id",
        "alert_type",
        "expire_date",
        "is_read",
        "created_at",
    ),
    "device_status": (
        "device_id",
        "camera_status",
        "sensor_status",
        "storage_free",
        "last_heartbeat",
    ),
    "env_log": (
        "id",
        "temperature",
        "humidity",
        "recorded_at",
        "is_abnormal",
    ),
    "pending_frames": (
        "id",
        "image_path",
        "change_ratio",
        "status",
        "created_at",
        "processed_at",
    ),
}

PRIMARY_KEYS = {
    "produce_info": "id",
    "inventory_log": "id",
    "stock_summary": "produce_id",
    "alert_record": "id",
    "device_status": "device_id",
    "env_log": "id",
    "pending_frames": "id",
}


def _upsert_rows(conn: Any, table: str, rows: list[dict[str, Any]]) -> int:
    columns = TABLE_COLUMNS[table]
    primary_key = PRIMARY_KEYS[table]
    update_columns = [column for column in columns if column != primary_key]
    placeholders = ", ".join("?" for _ in columns)
    updates = ", ".join(
        f"{column}=excluded.{column}" for column in update_columns
    )
    sql = (
        f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders}) "
        f"ON CONFLICT({primary_key}) DO UPDATE SET {updates}"
    )

    values: list[tuple[Any, ...]] = []
    for row in rows[:1000]:
        if not isinstance(row, dict) or primary_key not in row:
            continue
        values.append(tuple(row.get(column) for column in columns))
    if values:
        conn.executemany(sql, values)
    return len(values)


def _reapply_local_inventory(
    conn: Any, board_stock_rows: list[dict[str, Any]]
) -> None:
    """Keep server-side manual operations on top of the board stock snapshot."""
    board_quantities = {
        int(row["produce_id"]): float(row.get("current_qty") or 0)
        for row in board_stock_rows
        if isinstance(row, dict) and row.get("produce_id") is not None
    }
    local_deltas = conn.execute(
        """
        SELECT
            produce_id,
            SUM(
                CASE action_type
                    WHEN 'IN' THEN COALESCE(quantity, 0)
                    WHEN 'OUT' THEN -COALESCE(quantity, 0)
                    ELSE 0
                END
            ) AS quantity_delta
        FROM inventory_log
        WHERE
            sync_status = 'local'
            AND (id < 0 OR id >= 1000000000)
            AND produce_id IS NOT NULL
        GROUP BY produce_id
        """
    ).fetchall()
    for row in local_deltas:
        produce_id = int(row["produce_id"])
        base_quantity = board_quantities.get(produce_id, 0.0)
        combined_quantity = max(
            0.0, base_quantity + float(row["quantity_delta"] or 0)
        )
        existing = conn.execute(
            """
            SELECT earliest_expire_date
            FROM stock_summary
            WHERE produce_id = ?
            """,
            (produce_id,),
        ).fetchone()
        expire_date = existing["earliest_expire_date"] if existing else ""
        conn.execute(
            """
            INSERT INTO stock_summary
                (produce_id, current_qty, earliest_expire_date, last_updated)
            VALUES (?, ?, ?, datetime('now', 'localtime'))
            ON CONFLICT(produce_id) DO UPDATE SET
                current_qty = excluded.current_qty,
                last_updated = excluded.last_updated
            """,
            (produce_id, combined_quantity, expire_date or ""),
        )


def apply_sync_payload(db_path: str, payload: dict[str, Any]) -> dict[str, int]:
    init_db(db_path)
    source_device_id = str(payload.get("sourceDeviceId") or "unknown").strip()
    tables = payload.get("tables")
    if not isinstance(tables, dict):
        raise ValueError("tables must be an object")

    counts: dict[str, int] = {}
    with connection_scope(db_path) as conn:
        for table in TABLE_COLUMNS:
            rows = tables.get(table, [])
            if not isinstance(rows, list):
                raise ValueError(f"{table} must be a list")
            counts[table] = _upsert_rows(conn, table, rows)

        _reapply_local_inventory(conn, tables.get("stock_summary", []))

        conn.execute(
            """
            INSERT INTO sync_source_status
                (source_device_id, last_sync_at, last_counts_json)
            VALUES (?, ?, ?)
            ON CONFLICT(source_device_id) DO UPDATE SET
                last_sync_at=excluded.last_sync_at,
                last_counts_json=excluded.last_counts_json
            """,
            (
                source_device_id,
                datetime.now().isoformat(timespec="seconds"),
                json.dumps(counts, ensure_ascii=False),
            ),
        )
    return counts
