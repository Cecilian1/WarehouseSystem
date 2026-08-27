"""Shared DB access / formatting helpers used across api_service route modules.

Extracted from main.py so new modules (auth, alerts_engine, inventory_ops,
settings_store, records) can reuse the same read helpers without importing
from main.py (which would create a circular import) and without duplicating
the query logic.
"""

from __future__ import annotations

import os
from datetime import date, datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from backend.common.db import connection_scope

DEFAULT_DB_PATH = "/data/warehousekeeper/warehousekeeper.db"
DB_PATH = os.environ.get("WAREHOUSE_DB_PATH", DEFAULT_DB_PATH)
SERVER_LOCAL_ID_BASE = 1_000_000_000


def ok(data: Any) -> dict[str, Any]:
    return {"code": 0, "message": "ok", "data": data}


def query_all(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with connection_scope(DB_PATH) as conn:
        cursor = conn.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]


def query_one(sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    rows = query_all(sql, params)
    return rows[0] if rows else None


def allocate_local_id(conn: Any, table: str) -> int:
    """Allocate negative IDs reserved for computer-originated records.

    SQLite AUTOINCREMENT only advances from positive row IDs, so negative IDs can
    be copied to the board without colliding with future board-native records.
    """
    if table not in {"produce_info", "inventory_log", "alert_record"}:
        raise ValueError(f"unsupported local-id table: {table}")
    row = conn.execute(
        f"SELECT COALESCE(MIN(id), 0) AS min_id FROM {table} WHERE id < 0",
    ).fetchone()
    return int(row["min_id"]) - 1


def parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).replace("/", "-").strip()
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        try:
            return datetime.strptime(text[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None


def format_dt(value: Any, fallback: str = "") -> str:
    dt = parse_dt(value)
    if dt:
        return dt.strftime("%Y-%m-%d %H:%M")
    return str(value or fallback)


def format_time(value: Any) -> str:
    dt = parse_dt(value)
    if dt:
        return dt.strftime("%H:%M:%S")
    return str(value or "")


def humanize_heartbeat(value: Any) -> str:
    dt = parse_dt(value)
    if not dt:
        return "暂无心跳"
    seconds = max(0, int((datetime.now() - dt).total_seconds()))
    if seconds < 60:
        return "刚刚"
    if seconds < 3600:
        return f"{seconds // 60} 分钟前"
    return dt.strftime("%m-%d %H:%M")


def normalize_category(value: Any) -> str:
    text = str(value or "").strip()
    lowered = text.lower()
    if not text:
        return "水果"
    if "蔬" in text or "菜" in text or lowered in {"vegetable", "vegetables"}:
        return "蔬菜"
    if "果" in text or lowered in {"fruit", "fruits"}:
        return "水果"
    return text


def normalize_freshness(level: Any, score: Any = None, remaining_days: int | None = None) -> str:
    text = str(level or "").lower()
    if any(word in text for word in ["腐", "坏", "spoiled", "expired"]):
        return "spoiled"
    if any(word in text for word in ["临", "警", "warning", "warn"]):
        return "warning"
    try:
        numeric_score = float(score)
    except (TypeError, ValueError):
        numeric_score = None
    if numeric_score is not None:
        if numeric_score < 0.4:
            return "spoiled"
        if numeric_score < 0.75:
            return "warning"
        return "fresh"
    if remaining_days is not None:
        if remaining_days <= 0:
            return "spoiled"
        if remaining_days <= 2:
            return "warning"
    return "fresh"


def default_freshness_score(freshness: str) -> float:
    return {"fresh": 0.92, "warning": 0.68, "spoiled": 0.28}.get(freshness, 0.9)


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def color_for(name: str, category: str) -> str:
    palette = [
        "#ef4444",
        "#22c55e",
        "#4f8cff",
        "#f59e0b",
        "#14b8a6",
        "#a3e635",
        "#f97316",
    ]
    key = sum(ord(char) for char in f"{name}{category}")
    return palette[key % len(palette)]


def remaining_days(row: dict[str, Any]) -> int:
    expire_at = parse_dt(row.get("earliest_expire_date"))
    if expire_at:
        return (expire_at.date() - date.today()).days

    shelf_life = safe_int(row.get("shelf_life_days"), 0)
    inbound_at = parse_dt(row.get("inbound_at"))
    if shelf_life and inbound_at:
        return shelf_life - (date.today() - inbound_at.date()).days
    return shelf_life


def inventory_rows() -> list[dict[str, Any]]:
    rows = query_all(
        """
        SELECT
            p.id,
            p.name,
            p.category,
            p.shelf_life_days,
            p.ideal_temp_range,
            p.icon_url,
            COALESCE(p.unit, '件') AS unit,
            COALESCE(p.location, '本地库存') AS location,
            COALESCE(s.current_qty, 0) AS current_qty,
            s.earliest_expire_date,
            (
                SELECT l.created_at
                FROM inventory_log l
                WHERE l.produce_id = p.id AND l.action_type = 'IN'
                ORDER BY l.created_at DESC, l.id DESC
                LIMIT 1
            ) AS inbound_at,
            (
                SELECT l.freshness_level
                FROM inventory_log l
                WHERE l.produce_id = p.id
                ORDER BY l.created_at DESC, l.id DESC
                LIMIT 1
            ) AS freshness_level,
            (
                SELECT l.freshness_score
                FROM inventory_log l
                WHERE l.produce_id = p.id
                ORDER BY l.created_at DESC, l.id DESC
                LIMIT 1
            ) AS freshness_score
        FROM produce_info p
        LEFT JOIN stock_summary s ON s.produce_id = p.id
        WHERE COALESCE(s.current_qty, 0) > 0
        ORDER BY p.name
        """
    )

    items: list[dict[str, Any]] = []
    for row in rows:
        category = normalize_category(row.get("category"))
        days_left = remaining_days(row)
        freshness = normalize_freshness(
            row.get("freshness_level"),
            row.get("freshness_score"),
            days_left,
        )
        freshness_score = safe_float(row.get("freshness_score"), default_freshness_score(freshness))
        shelf_life = safe_int(row.get("shelf_life_days"), max(days_left, 0))
        items.append(
            {
                "id": row["id"],
                "name": row.get("name") or "未命名果蔬",
                "category": category,
                "quantity": safe_float(row.get("current_qty")),
                "unit": row.get("unit") or "件",
                "shelfLife": shelf_life,
                "remainingDays": days_left,
                "freshness": freshness,
                "freshnessScore": max(0.0, min(1.0, freshness_score)),
                "storageAdvice": row.get("ideal_temp_range") or "按果蔬适宜温湿度储存",
                "inboundAt": format_dt(row.get("inbound_at"), "暂无入库记录"),
                "location": row.get("location") or "本地库存",
                "color": row.get("icon_url") or color_for(row.get("name") or "", category),
            }
        )
    return items


def produce_rows() -> list[dict[str, Any]]:
    rows = query_all(
        """
        SELECT
            p.id,
            p.name,
            p.category,
            p.shelf_life_days,
            p.ideal_temp_range,
            p.icon_url,
            COALESCE(p.unit, '件') AS unit,
            COALESCE(p.location, '本地库存') AS location,
            COALESCE(s.current_qty, 0) AS current_qty,
            COALESCE(s.earliest_expire_date, '') AS earliest_expire_date
        FROM produce_info p
        LEFT JOIN stock_summary s ON s.produce_id = p.id
        ORDER BY p.name
        """
    )
    return [
        {
            "id": row["id"],
            "name": row.get("name") or "",
            "category": row.get("category") or "",
            "shelfLifeDays": safe_int(row.get("shelf_life_days")),
            "idealTempRange": row.get("ideal_temp_range") or "",
            "iconUrl": row.get("icon_url") or "",
            "unit": row.get("unit") or "件",
            "location": row.get("location") or "本地库存",
            "currentQty": safe_float(row.get("current_qty")),
            "earliestExpireDate": row.get("earliest_expire_date") or "",
        }
        for row in rows
    ]


def get_produce_item(produce_id: int) -> dict[str, Any]:
    for item in produce_rows():
        if item["id"] == produce_id:
            return item
    raise HTTPException(status_code=404, detail="果蔬信息不存在")


def recognition_rows(limit: int = 30, log_id: int | None = None) -> list[dict[str, Any]]:
    where_clause = "WHERE l.id = ?" if log_id is not None else ""
    params: tuple[Any, ...] = (log_id,) if log_id is not None else (limit,)
    rows = query_all(
        f"""
        SELECT
            l.id,
            l.produce_id,
            l.action_type,
            l.quantity,
            l.freshness_level,
            l.freshness_score,
            l.confidence,
            l.image_path,
            l.created_at,
            COALESCE(p.name, '未知果蔬') AS name,
            COALESCE(p.category, '') AS category
        FROM inventory_log l
        LEFT JOIN produce_info p ON p.id = l.produce_id
        {where_clause}
        ORDER BY l.created_at DESC, l.id DESC
        {"" if log_id is not None else "LIMIT ?"}
        """,
        params,
    )
    records: list[dict[str, Any]] = []
    for row in rows:
        freshness = normalize_freshness(row.get("freshness_level"), row.get("freshness_score"))
        confidence = safe_float(row.get("confidence"), 0.0)
        freshness_score = safe_float(row.get("freshness_score"), default_freshness_score(freshness))
        image_url = f"/api/frames/inventory-log/{row['id']}/image" if row.get("image_path") else None
        records.append(
            {
                "id": row["id"],
                "produceId": row.get("produce_id"),
                "time": format_time(row.get("created_at")),
                "createdAt": row.get("created_at"),
                "name": row.get("name") or "未知果蔬",
                "category": normalize_category(row.get("category")),
                "quantity": safe_float(row.get("quantity"), 0),
                "action": row.get("action_type") or "IN",
                "type": "inbound"
                if (row.get("action_type") or "IN") == "IN"
                else "outbound",
                "confidence": max(0.0, min(1.0, confidence)),
                "freshness": freshness,
                "freshnessScore": max(0.0, min(1.0, freshness_score)),
                "image": image_url,
                "latency": 0,
            }
        )
    return records


def recognition_row_by_id(log_id: int) -> dict[str, Any] | None:
    rows = recognition_rows(log_id=log_id)
    return rows[0] if rows else None


def environment_data() -> dict[str, Any]:
    latest = query_one(
        """
        SELECT temperature, humidity, is_abnormal, recorded_at
        FROM env_log
        ORDER BY id DESC
        LIMIT 1
        """
    )
    trend_rows = query_all(
        """
        SELECT temperature, humidity, is_abnormal, recorded_at
        FROM env_log
        ORDER BY id DESC
        LIMIT 16
        """
    )
    trend = [
        {
            "time": format_time(row.get("recorded_at"))[:5],
            "temperature": safe_float(row.get("temperature")),
            "humidity": safe_float(row.get("humidity")),
        }
        for row in reversed(trend_rows)
    ]
    is_abnormal = bool(latest and latest.get("is_abnormal"))
    valid = latest is not None
    return {
        "temperature": safe_float(latest.get("temperature") if latest else None),
        "humidity": safe_float(latest.get("humidity") if latest else None),
        "valid": valid,
        "temperatureState": "offline" if not valid else "warning" if is_abnormal else "online",
        "humidityState": "offline" if not valid else "warning" if is_abnormal else "online",
        "trend": trend,
    }


def category_stats(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    totals: dict[str, float] = {}
    for item in items:
        totals[item["category"]] = totals.get(item["category"], 0.0) + safe_float(item["quantity"])
    colors = {"水果": "#4f8cff", "蔬菜": "#22c55e"}
    return [
        {"name": name, "value": value, "color": colors.get(name, color_for(name, name))}
        for name, value in totals.items()
    ]


def freshness_stats(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    labels = {"fresh": "新鲜", "warning": "临期", "spoiled": "腐败"}
    colors = {"fresh": "#22c55e", "warning": "#f59e0b", "spoiled": "#ef4444"}
    totals = {"fresh": 0.0, "warning": 0.0, "spoiled": 0.0}
    for item in items:
        totals[item["freshness"]] += safe_float(item["quantity"], 1.0)
    return [
        {"name": labels[key], "value": value, "color": colors[key]}
        for key, value in totals.items()
        if value
    ]


def stock_trend() -> list[dict[str, Any]]:
    rows = query_all(
        """
        SELECT
            date(created_at) AS day,
            SUM(CASE WHEN action_type = 'IN' THEN COALESCE(quantity, 0) ELSE 0 END) AS inbound,
            SUM(CASE WHEN action_type = 'OUT' THEN COALESCE(quantity, 0) ELSE 0 END) AS outbound
        FROM inventory_log
        GROUP BY date(created_at)
        ORDER BY date(created_at) DESC
        LIMIT 12
        """
    )
    return [
        {
            "time": row.get("day", "")[5:] if row.get("day") else "",
            "inbound": safe_float(row.get("inbound")),
            "outbound": safe_float(row.get("outbound")),
        }
        for row in reversed(rows)
    ]


def device_statuses() -> list[dict[str, Any]]:
    row = query_one(
        """
        SELECT device_id, camera_status, sensor_status, storage_free, last_heartbeat
        FROM device_status
        ORDER BY last_heartbeat DESC
        LIMIT 1
        """
    )
    db_file = Path(DB_PATH)
    db_size = db_file.stat().st_size if db_file.exists() else 0
    storage_free = safe_float(row.get("storage_free") if row else None)
    storage_value = f"{storage_free / (1024 ** 3):.1f} GB 可用" if storage_free else "未知"
    heartbeat = humanize_heartbeat(row.get("last_heartbeat") if row else None)
    camera_ok = bool(row and row.get("camera_status") == "ok")
    sensor_ok = bool(row and row.get("sensor_status") == "ok")

    return [
        {
            "id": "board",
            "label": "开发板",
            "value": "在线" if row else "等待心跳",
            "state": "online" if row else "offline",
            "detail": row.get("device_id") if row else "fridge-01",
        },
        {
            "id": "camera",
            "label": "摄像头",
            "value": "正常" if camera_ok else "异常/未上报",
            "state": "online" if camera_ok else "warning",
            "detail": heartbeat,
        },
        {
            "id": "sensor",
            "label": "温湿度传感器",
            "value": "正常" if sensor_ok else "异常/未上报",
            "state": "online" if sensor_ok else "warning",
            "detail": heartbeat,
        },
        {
            "id": "sqlite",
            "label": "SQLite",
            "value": "正常" if db_file.exists() else "未初始化",
            "state": "online" if db_file.exists() else "offline",
            "detail": f"WAL · {db_size / 1024 / 1024:.1f} MB",
        },
        {
            "id": "storage",
            "label": "存储空间",
            "value": storage_value,
            "state": "online" if storage_free else "warning",
            "detail": str(db_file.parent),
        },
    ]


def alert_rows() -> list[dict[str, Any]]:
    rows = query_all(
        """
        SELECT
            a.id,
            a.produce_id,
            a.alert_type,
            a.expire_date,
            a.is_read,
            a.created_at,
            COALESCE(p.name, '') AS produce_name
        FROM alert_record a
        LEFT JOIN produce_info p ON p.id = a.produce_id
        ORDER BY a.is_read ASC, a.created_at DESC
        """
    )
    items: list[dict[str, Any]] = []
    for row in rows:
        alert_type = str(row.get("alert_type") or "")
        produce_name = row.get("produce_name") or "设备"
        if alert_type == "device_abnormal":
            web_type = "temperature"
            title = "温度超过安全阈值"
            source = "SHT30 环境传感器"
            description = "环境监测服务检测到设备温度异常，请检查冰箱门与制冷状态。"
            level = "critical"
        elif alert_type == "expired":
            web_type = "spoiled"
            title = f"{produce_name} 已过期"
            source = produce_name
            description = f"过期日期：{row.get('expire_date') or '未知'}，建议立即处理。"
            level = "critical"
        else:
            web_type = "expiring"
            title = f"{produce_name} 即将过期"
            source = produce_name
            description = f"预计过期日期：{row.get('expire_date') or '未知'}，建议优先使用。"
            level = "warning"
        items.append(
            {
                "id": row["id"],
                "produceId": row.get("produce_id"),
                "title": title,
                "type": web_type,
                "level": level,
                "source": source,
                "description": description,
                "time": format_dt(row.get("created_at")),
                "status": "confirmed" if safe_int(row.get("is_read")) else "pending",
            }
        )
    return items


def history_rows(page: int = 1, page_size: int = 10) -> dict[str, Any]:
    total_row = query_one(
        """
        SELECT COUNT(*) AS total FROM (
            SELECT id FROM inventory_log
            UNION ALL SELECT id FROM env_log
            UNION ALL SELECT id FROM alert_record
        )
        """
    )
    rows = query_all(
        """
        SELECT * FROM (
            SELECT
                l.id,
                created_at AS time,
                'AI 识别' AS module,
                CASE action_type WHEN 'IN' THEN '自动入库' ELSE '自动出库' END AS action,
                COALESCE(p.name, '未知果蔬') || ' ' ||
                    CASE action_type WHEN 'IN' THEN '+' ELSE '-' END ||
                    COALESCE(quantity, 0) || ' 件' AS detail,
                'Edge AI' AS operator,
                'success' AS status
            FROM inventory_log l
            LEFT JOIN produce_info p ON p.id = l.produce_id
            UNION ALL
            SELECT
                id,
                recorded_at AS time,
                '环境监测' AS module,
                '环境采样' AS action,
                '温度 ' || temperature || '°C，湿度 ' || humidity || '%RH' AS detail,
                'SHT30' AS operator,
                CASE is_abnormal WHEN 1 THEN 'warning' ELSE 'success' END AS status
            FROM env_log
            UNION ALL
            SELECT
                id,
                created_at AS time,
                '预警中心' AS module,
                '生成预警' AS action,
                alert_type AS detail,
                '规则引擎' AS operator,
                'warning' AS status
            FROM alert_record
        )
        ORDER BY time DESC
        LIMIT ? OFFSET ?
        """,
        (page_size, (page - 1) * page_size),
    )
    items = [
        {
            "id": row["id"],
            "time": format_dt(row.get("time")),
            "module": row.get("module"),
            "action": row.get("action"),
            "detail": row.get("detail"),
            "operator": row.get("operator"),
            "status": row.get("status"),
        }
        for row in rows
    ]
    return {
        "list": items,
        "total": safe_int(total_row.get("total") if total_row else None),
        "page": page,
        "pageSize": page_size,
    }
