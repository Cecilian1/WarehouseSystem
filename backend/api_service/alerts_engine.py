"""预警扫描后台任务 + 预警处理/消息(别名)接口。

`alert_record` 表此前没有任何写入方——这里补上唯一的写入来源：定期扫描
`stock_summary` 的临期/过期情况和 `device_status` 的心跳新鲜度。纯服务端
业务逻辑，不涉及 camera_service / env_service / sync_service。
"""

from __future__ import annotations

import asyncio
import os
import threading
import time
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from backend.api_service import ws_hub
from backend.api_service.helpers import (
    DB_PATH,
    allocate_local_id,
    alert_rows,
    connection_scope,
    ok,
    parse_dt,
    query_all,
    query_one,
)

ALERT_SCAN_INTERVAL_SEC = int(os.environ.get("WAREHOUSE_ALERT_SCAN_INTERVAL_SEC", "60"))
EXPIRING_WINDOW_DAYS = int(os.environ.get("WAREHOUSE_ALERT_EXPIRING_WINDOW_DAYS", "3"))
DEVICE_HEARTBEAT_STALE_SEC = int(os.environ.get("WAREHOUSE_DEVICE_STALE_SEC", "60"))
ALERT_RESEND_COOLDOWN_SEC = int(os.environ.get("WAREHOUSE_ALERT_RESEND_COOLDOWN_SEC", "21600"))

router = APIRouter()


def _should_skip_alert(alert_type: str, produce_id: int | None = None) -> bool:
    """同一条件只保留一条待处理预警；处理后冷却期内不再重复插入。"""
    if produce_id is None:
        row = query_one(
            """
            SELECT is_read, created_at
            FROM alert_record
            WHERE alert_type = ?
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (alert_type,),
        )
    else:
        row = query_one(
            """
            SELECT is_read, created_at
            FROM alert_record
            WHERE produce_id = ? AND alert_type = ?
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (produce_id, alert_type),
        )
    if not row:
        return False
    if not int(row.get("is_read") or 0):
        return True
    created = parse_dt(row.get("created_at"))
    if not created:
        return True
    return (datetime.now() - created).total_seconds() < ALERT_RESEND_COOLDOWN_SEC


def scan_once() -> list[int]:
    """扫描一次临期/过期库存与设备心跳，插入去重后的新预警，返回新插入的 alert_record id。"""
    new_ids: list[int] = []
    today = datetime.now().date()

    stock_rows = query_all(
        """
        SELECT produce_id, earliest_expire_date
        FROM stock_summary
        WHERE current_qty > 0 AND earliest_expire_date IS NOT NULL AND earliest_expire_date != ''
        """
    )
    for row in stock_rows:
        expire_at = parse_dt(row.get("earliest_expire_date"))
        if not expire_at:
            continue
        days_left = (expire_at.date() - today).days
        if days_left < 0:
            alert_type = "expired"
        elif days_left <= EXPIRING_WINDOW_DAYS:
            alert_type = "expiring"
        else:
            continue

        produce_id = row["produce_id"]
        if _should_skip_alert(alert_type, produce_id):
            continue
        with connection_scope(DB_PATH) as conn:
            alert_id = allocate_local_id(conn, "alert_record")
            conn.execute(
                """
                INSERT INTO alert_record (id, produce_id, alert_type, expire_date)
                VALUES (?, ?, ?, ?)
                """,
                (alert_id, produce_id, alert_type, row.get("earliest_expire_date")),
            )
            new_ids.append(alert_id)

    heartbeat_row = query_one(
        "SELECT last_heartbeat FROM device_status ORDER BY last_heartbeat DESC LIMIT 1"
    )
    if heartbeat_row and heartbeat_row.get("last_heartbeat"):
        last_seen = parse_dt(heartbeat_row["last_heartbeat"])
        if last_seen and (datetime.now() - last_seen).total_seconds() > DEVICE_HEARTBEAT_STALE_SEC:
            if not _should_skip_alert("device_abnormal"):
                with connection_scope(DB_PATH) as conn:
                    alert_id = allocate_local_id(conn, "alert_record")
                    conn.execute(
                        """
                        INSERT INTO alert_record (id, produce_id, alert_type, expire_date)
                        VALUES (?, NULL, 'device_abnormal', NULL)
                        """,
                        (alert_id,),
                    )
                    new_ids.append(alert_id)

    return new_ids


def _scan_loop(loop: asyncio.AbstractEventLoop, interval: int) -> None:
    while True:
        try:
            new_ids = scan_once()
            if new_ids:
                current = {item["id"]: item for item in alert_rows()}
                for alert_id in new_ids:
                    alert = current.get(alert_id)
                    if alert:
                        asyncio.run_coroutine_threadsafe(
                            ws_hub.broadcast({"type": "alert:new", "payload": alert}), loop
                        )
        except Exception:
            pass
        time.sleep(interval)


def start_alert_scan_task(interval: int = ALERT_SCAN_INTERVAL_SEC) -> threading.Thread:
    loop = asyncio.get_event_loop()
    thread = threading.Thread(
        target=_scan_loop,
        args=(loop, interval),
        name="warehouse-alert-scan",
        daemon=True,
    )
    thread.start()
    return thread


def _to_message(alert: dict[str, Any]) -> dict[str, Any]:
    is_device_alert = alert["type"] in {"temperature", "device", "storage"}
    return {
        "id": alert["id"],
        "title": alert["title"],
        "type": alert["type"],
        "time": alert["time"],
        "device": "客厅智能冰箱" if is_device_alert else "",
        "produce": "" if is_device_alert else alert["source"],
        "produceId": alert.get("produceId"),
        "reason": alert["description"],
        "suggestion": "",
        "status": alert["status"],
    }


@router.get("/api/messages")
def messages() -> dict[str, Any]:
    return ok([_to_message(item) for item in alert_rows()])


@router.get("/api/messages/detail")
def message_detail(id: int = Query(...)) -> dict[str, Any]:
    for item in alert_rows():
        if item["id"] == id:
            return ok(_to_message(item))
    raise HTTPException(status_code=404, detail="消息不存在")
