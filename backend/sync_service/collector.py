"""Continuously pull incremental board records into the Windows-side database."""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from backend.sync_service.storage import apply_sync_payload
from backend.sync_service.push import push_pending_operations

INCREMENTAL_TABLES = ("inventory_log", "alert_record", "env_log", "pending_frames")
logger = logging.getLogger("sync_collector")


def _load_state(path: Path) -> dict[str, int]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {
            table: max(0, int(data.get(table, 0)))
            for table in INCREMENTAL_TABLES
        }
    except (FileNotFoundError, ValueError, TypeError, json.JSONDecodeError):
        return {table: 0 for table in INCREMENTAL_TABLES}


def _save_state(path: Path, state: dict[str, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(".tmp")
    temp_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temp_path.replace(path)


def _next_state(
    current: dict[str, int], payload: dict[str, Any]
) -> dict[str, int]:
    state = dict(current)
    tables = payload.get("tables", {})
    for table in INCREMENTAL_TABLES:
        rows = tables.get(table, [])
        if rows:
            state[table] = max(int(row["id"]) for row in rows)
    return state


def _reconcile_state(local_db_path: str, state: dict[str, int]) -> dict[str, int]:
    """Rewind a cursor if the local database was replaced or restored."""
    reconciled = dict(state)
    conn = sqlite3.connect(local_db_path, timeout=5)
    try:
        for table in INCREMENTAL_TABLES:
            # 开发板同步接口的 after 参数约束为 >= 0。历史演示/测试数据
            # 可能使用负数 ID，不能将其写入远端查询游标。
            local_max = max(
                0,
                int(
                    conn.execute(
                        f"SELECT COALESCE(MAX(id), 0) FROM {table}"
                    ).fetchone()[0]
                ),
            )
            if local_max < reconciled[table]:
                reconciled[table] = local_max
    finally:
        conn.close()
    return reconciled


def collect_once(
    board_url: str,
    local_db_path: str,
    state_path: Path,
    batch_size: int = 200,
) -> dict[str, int]:
    state = _reconcile_state(local_db_path, _load_state(state_path))
    query = urllib.parse.urlencode(
        {
            "inventory_log_after": state["inventory_log"],
            "alert_record_after": state["alert_record"],
            "env_log_after": state["env_log"],
            "pending_frames_after": state["pending_frames"],
            "batch_size": batch_size,
        }
    )
    request = urllib.request.Request(
        f"{board_url.rstrip('/')}/api/sync/export?{query}",
        method="GET",
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=15) as response:
        result = json.loads(response.read().decode("utf-8"))
    if result.get("code") != 0:
        raise RuntimeError(f"板端导出失败: {result}")

    payload = result["data"]
    counts = apply_sync_payload(local_db_path, payload)
    _save_state(state_path, _next_state(state, payload))
    return counts


def run_collector(
    board_url: str,
    local_db_path: str,
    state_path: Path,
    interval_sec: int = 5,
) -> None:
    logger.info("本机数据采集器启动: board=%s", board_url)
    while True:
        try:
            push_counts = push_pending_operations(board_url, local_db_path)
            if push_counts["pushed"] or push_counts["failed"]:
                logger.info("电脑端库存操作回传开发板: %s", push_counts)
            counts = collect_once(board_url, local_db_path, state_path)
            logger.info("板端数据已写入本机: %s", counts)
        except Exception as exc:
            logger.warning("拉取板端数据失败，稍后重试: %s", exc)
        time.sleep(max(2, interval_sec))


def start_background_collector(
    board_url: str,
    local_db_path: str,
    state_path: str,
    interval_sec: int = 5,
) -> threading.Thread:
    thread = threading.Thread(
        target=run_collector,
        args=(board_url, local_db_path, Path(state_path), interval_sec),
        name="warehouse-sync-collector",
        daemon=True,
    )
    thread.start()
    return thread
