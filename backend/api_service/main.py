"""FastAPI service that exposes the existing local SQLite data to Web clients.

The service intentionally maps the current schema into the Web frontend's
response shape without changing any table definition.
"""

from __future__ import annotations

import os
from datetime import date, datetime
from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.common.db import connection_scope

DEFAULT_DB_PATH = "/data/warehousekeeper/warehousekeeper.db"
DB_PATH = os.environ.get("WAREHOUSE_DB_PATH", DEFAULT_DB_PATH)

app = FastAPI(title="WarehouseKeeper API", version="1.0.0")

cors_origins = [
    item.strip()
    for item in os.environ.get("WAREHOUSE_CORS_ORIGINS", "*").split(",")
    if item.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins or ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def ok(data: Any) -> dict[str, Any]:
    return {"code": 0, "message": "ok", "data": data}


def query_all(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with connection_scope(DB_PATH) as conn:
        cursor = conn.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]


def query_one(sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    rows = query_all(sql, params)
    return rows[0] if rows else None


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
                "unit": "件",
                "shelfLife": shelf_life,
                "remainingDays": days_left,
                "freshness": freshness,
                "freshnessScore": max(0.0, min(1.0, freshness_score)),
                "storageAdvice": row.get("ideal_temp_range") or "按果蔬适宜温湿度储存",
                "inboundAt": format_dt(row.get("inbound_at"), "暂无入库记录"),
                "location": "本地库存",
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


def recognition_rows(limit: int = 30) -> list[dict[str, Any]]:
    rows = query_all(
        """
        SELECT
            l.id,
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
        ORDER BY l.created_at DESC, l.id DESC
        LIMIT ?
        """,
        (limit,),
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
                "time": format_time(row.get("created_at")),
                "name": row.get("name") or "未知果蔬",
                "category": normalize_category(row.get("category")),
                "quantity": safe_float(row.get("quantity"), 0),
                "action": row.get("action_type") or "IN",
                "confidence": max(0.0, min(1.0, confidence)),
                "freshness": freshness,
                "freshnessScore": max(0.0, min(1.0, freshness_score)),
                "image": image_url,
                "latency": 0,
            }
        )
    return records


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
    return {
        "temperature": safe_float(latest.get("temperature") if latest else None),
        "humidity": safe_float(latest.get("humidity") if latest else None),
        "temperatureState": "warning" if is_abnormal else "online",
        "humidityState": "online",
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


@app.get("/api/health")
def health() -> dict[str, Any]:
    return ok({"dbPath": DB_PATH, "dbExists": Path(DB_PATH).exists()})


@app.get("/api/dashboard")
def dashboard() -> dict[str, Any]:
    items = inventory_rows()
    total_stock = sum(safe_float(item["quantity"]) for item in items)
    today_inbound = query_one(
        """
        SELECT SUM(COALESCE(quantity, 0)) AS total
        FROM inventory_log
        WHERE action_type = 'IN' AND date(created_at) = date('now', 'localtime')
        """
    )
    alerts = alert_rows()
    env = environment_data()
    data = {
        "statuses": device_statuses(),
        "metrics": [
            {"id": "stock", "label": "库存总量", "value": total_stock, "unit": "件", "change": 0, "tone": "blue"},
            {"id": "today", "label": "今日新增", "value": safe_float(today_inbound.get("total") if today_inbound else None), "unit": "件", "change": 0, "tone": "cyan"},
            {"id": "expiring", "label": "即将过期", "value": len([item for item in items if item["freshness"] == "warning"]), "unit": "项", "change": 0, "tone": "orange"},
            {"id": "alerts", "label": "异常预警", "value": len([item for item in alerts if item["status"] == "pending"]), "unit": "项", "change": 0, "tone": "red"},
        ],
        "environment": env,
        "detections": [],
        "recognitions": recognition_rows(8),
        "categories": category_stats(items),
        "freshness": freshness_stats(items),
        "stockTrend": stock_trend(),
        "performance": {"fps": 0, "latency": 0, "model": "待接入", "power": 0},
    }
    return ok(data)


@app.get("/api/inventory")
def inventory(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    keyword: str = "",
    category: str = "",
    freshness: str = "",
) -> dict[str, Any]:
    items = inventory_rows()
    if keyword:
        items = [
            item
            for item in items
            if keyword.lower() in f"{item['name']}{item['category']}{item['location']}".lower()
        ]
    if category:
        items = [item for item in items if item["category"] == category]
    if freshness:
        items = [item for item in items if item["freshness"] == freshness]

    total = len(items)
    start = (page - 1) * pageSize
    return ok({"list": items[start : start + pageSize], "total": total, "page": page, "pageSize": pageSize})


@app.get("/api/recognitions")
def recognitions() -> dict[str, Any]:
    return ok(recognition_rows(60))


@app.get("/api/environment")
def environment() -> dict[str, Any]:
    env = environment_data()
    return ok({"temperature": env["temperature"], "humidity": env["humidity"], "trend": env["trend"]})


@app.get("/api/environment/latest")
def environment_latest() -> dict[str, Any]:
    latest = query_one(
        """
        SELECT temperature, humidity, is_abnormal, recorded_at
        FROM env_log
        ORDER BY id DESC
        LIMIT 1
        """
    )
    return ok(
        {
            "valid": latest is not None,
            "temperature": safe_float(latest.get("temperature") if latest else None),
            "humidity": safe_float(latest.get("humidity") if latest else None),
            "isAbnormal": bool(latest and latest.get("is_abnormal")),
            "recordedAt": format_dt(latest.get("recorded_at") if latest else None),
        }
    )


@app.get("/api/produce")
def produce_list() -> dict[str, Any]:
    return ok(produce_rows())


@app.post("/api/produce")
def produce_create(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    name = str(payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="果蔬名称不能为空")
    with connection_scope(DB_PATH) as conn:
        cursor = conn.execute(
            """
            INSERT INTO produce_info (name, category, shelf_life_days, ideal_temp_range, icon_url)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                name,
                payload.get("category") or "",
                safe_int(payload.get("shelfLifeDays")),
                payload.get("idealTempRange") or "",
                payload.get("iconUrl") or "",
            ),
        )
        produce_id = cursor.lastrowid
    return ok(get_produce_item(int(produce_id)))


@app.put("/api/produce/{produce_id}")
def produce_update(produce_id: int, payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    name = str(payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="果蔬名称不能为空")
    with connection_scope(DB_PATH) as conn:
        cursor = conn.execute(
            """
            UPDATE produce_info
            SET name = ?, category = ?, shelf_life_days = ?, ideal_temp_range = ?, icon_url = ?
            WHERE id = ?
            """,
            (
                name,
                payload.get("category") or "",
                safe_int(payload.get("shelfLifeDays")),
                payload.get("idealTempRange") or "",
                payload.get("iconUrl") or "",
                produce_id,
            ),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="果蔬信息不存在")
    return ok(get_produce_item(produce_id))


@app.get("/api/alerts")
def alerts(status: str = "") -> dict[str, Any]:
    items = alert_rows()
    if status:
        items = [item for item in items if item["status"] == status]
    return ok(items)


@app.get("/api/devices")
def devices() -> dict[str, Any]:
    row = query_one(
        """
        SELECT device_id, camera_status, sensor_status, storage_free, last_heartbeat
        FROM device_status
        ORDER BY last_heartbeat DESC
        LIMIT 1
        """
    )
    heartbeat = humanize_heartbeat(row.get("last_heartbeat") if row else None)
    storage_free = safe_float(row.get("storage_free") if row else None)
    return ok(
        [
            {
                "id": row.get("device_id", "fridge-01") if row else "fridge-01",
                "name": "开发板",
                "type": "边缘计算节点",
                "model": "LoongArch",
                "state": "online" if row else "offline",
                "uptime": 100 if row else 0,
                "value": "运行中" if row else "等待心跳",
                "detail": f"SQLite: {DB_PATH}",
                "lastHeartbeat": heartbeat,
            },
            {
                "id": "camera-01",
                "name": "冰箱内摄像头",
                "type": "视觉采集",
                "model": "UVC Camera",
                "state": "online" if row and row.get("camera_status") == "ok" else "warning",
                "uptime": 100 if row and row.get("camera_status") == "ok" else 0,
                "value": row.get("camera_status", "未上报") if row else "未上报",
                "detail": "camera_service",
                "lastHeartbeat": heartbeat,
            },
            {
                "id": "sensor-01",
                "name": "温湿度传感器",
                "type": "环境感知",
                "model": "SHT30",
                "state": "online" if row and row.get("sensor_status") == "ok" else "warning",
                "uptime": 100 if row and row.get("sensor_status") == "ok" else 0,
                "value": row.get("sensor_status", "未上报") if row else "未上报",
                "detail": "env_service",
                "lastHeartbeat": heartbeat,
            },
            {
                "id": "storage-01",
                "name": "本地数据库",
                "type": "数据存储",
                "model": "SQLite 3",
                "state": "online" if Path(DB_PATH).exists() else "offline",
                "uptime": 100 if Path(DB_PATH).exists() else 0,
                "value": f"{storage_free / (1024 ** 3):.1f} GB 可用" if storage_free else "未知",
                "detail": "WAL 模式",
                "lastHeartbeat": heartbeat,
            },
        ]
    )


@app.get("/api/history")
def history(page: int = Query(1, ge=1), pageSize: int = Query(10, ge=1, le=100)) -> dict[str, Any]:
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
        (pageSize, (page - 1) * pageSize),
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
    return ok(
        {
            "list": items,
            "total": safe_int(total_row.get("total") if total_row else None),
            "page": page,
            "pageSize": pageSize,
        }
    )


@app.get("/api/analytics")
def analytics() -> dict[str, Any]:
    items = inventory_rows()
    daily = query_all(
        """
        SELECT
            strftime('%d日', created_at) AS date,
            SUM(CASE WHEN action_type = 'IN' THEN COALESCE(quantity, 0) ELSE 0 END) AS inbound,
            SUM(CASE WHEN action_type = 'OUT' THEN COALESCE(quantity, 0) ELSE 0 END) AS outbound
        FROM inventory_log
        GROUP BY date(created_at)
        ORDER BY date(created_at) DESC
        LIMIT 14
        """
    )
    return ok(
        {
            "daily": [
                {
                    "date": row.get("date"),
                    "inbound": safe_float(row.get("inbound")),
                    "outbound": safe_float(row.get("outbound")),
                    "waste": 0,
                }
                for row in reversed(daily)
            ],
            "categories": category_stats(items),
            "freshness": freshness_stats(items),
            "radar": [
                {"name": "识别准确率", "value": 0},
                {"name": "库存周转率", "value": 0},
                {"name": "环境稳定度", "value": 80 if environment_data()["temperatureState"] == "online" else 40},
                {"name": "设备在线率", "value": 90 if device_statuses()[0]["state"] == "online" else 20},
                {"name": "预警及时率", "value": 80},
                {"name": "节约率", "value": 0},
            ],
            "heatmap": [],
        }
    )


@app.post("/api/settings")
def settings(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    return ok(payload)


def image_response(image_path: Any) -> FileResponse:
    if not image_path:
        raise HTTPException(status_code=404, detail="图片路径不存在")
    path = Path(str(image_path))
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"图片文件不存在: {path}")
    return FileResponse(path)


@app.get("/api/frames/{frame_id}/image")
def frame_image(frame_id: int) -> FileResponse:
    row = query_one("SELECT image_path FROM pending_frames WHERE id = ?", (frame_id,))
    return image_response(row.get("image_path") if row else None)


@app.get("/api/frames/inventory-log/{log_id}/image")
def inventory_log_image(log_id: int) -> FileResponse:
    row = query_one("SELECT image_path FROM inventory_log WHERE id = ?", (log_id,))
    return image_response(row.get("image_path") if row else None)
