"""FastAPI service that exposes the existing local SQLite data to Web clients.

The service intentionally maps the current schema into the Web frontend's
response shape without changing any table definition.
"""

from __future__ import annotations

import asyncio
import logging
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from fastapi import (
    Body,
    FastAPI,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response

from backend.api_service import ws_hub
from backend.api_service.alerts_engine import router as alerts_router
from backend.api_service.alerts_engine import start_alert_scan_task
from backend.api_service.ai_assistant import router as ai_assistant_router
from backend.api_service.auth import router as auth_router
from backend.api_service.daily_report import router as daily_report_router
from backend.api_service.helpers import (
    allocate_local_id,
    alert_rows,
    category_stats,
    device_statuses,
    environment_data,
    format_dt,
    freshness_stats,
    get_produce_item,
    history_rows,
    humanize_heartbeat,
    inventory_rows,
    ok,
    produce_rows,
    query_all,
    query_one,
    recognition_rows,
    safe_float,
    safe_int,
    stock_trend,
)
from backend.api_service.inventory_ops import router as inventory_ops_router
from backend.api_service.miniprogram_compat import router as miniprogram_compat_router
from backend.api_service.records import router as records_router
from backend.api_service.settings_store import router as settings_router
from backend.api_service.voice import router as voice_router
from backend.common.db import connection_scope
from backend.common.init_db import init_db
from backend.sync_service.collector import start_background_collector
from backend.sync_service.push import apply_remote_operation
from backend.sync_service.storage import TABLE_COLUMNS

# uvicorn 不会给根logger配置handler，不加这行 sync_collector 等模块的 INFO 日志
# （比如"板端数据已写入本机"）会被默默丢弃、终端上看不到任何输出。
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)

DEFAULT_DB_PATH = "/data/warehousekeeper/warehousekeeper.db"
DB_PATH = os.environ.get("WAREHOUSE_DB_PATH", DEFAULT_DB_PATH)
BOARD_SOURCE_URL = os.environ.get("WAREHOUSE_BOARD_SOURCE_URL", "")
COLLECTOR_STATE_PATH = os.environ.get(
    "WAREHOUSE_COLLECTOR_STATE_PATH", "data/collector-state.json"
)
MAX_PROXY_IMAGE_BYTES = 10 * 1024 * 1024
LATEST_FRAME_PATH = os.environ.get(
    "WAREHOUSE_LATEST_FRAME_PATH",
    "/data/warehousekeeper/frames/latest.jpg",
)

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

app.include_router(auth_router)
app.include_router(ai_assistant_router)
app.include_router(daily_report_router)
app.include_router(alerts_router)
app.include_router(inventory_ops_router)
app.include_router(miniprogram_compat_router)
app.include_router(settings_router)
app.include_router(records_router)
app.include_router(voice_router)


@app.get("/api/health")
def health() -> dict[str, Any]:
    return ok({"dbPath": DB_PATH, "dbExists": Path(DB_PATH).exists()})


@app.get("/api/sync/status")
def sync_status() -> dict[str, Any]:
    rows = query_all(
        """
        SELECT source_device_id, last_sync_at, last_counts_json
        FROM sync_source_status
        ORDER BY last_sync_at DESC
        """
    )
    outbox = query_one(
        """
        SELECT
            SUM(CASE WHEN status = 'synced' THEN 1 ELSE 0 END) AS synced,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed
        FROM board_sync_outbox
        """
    )
    return ok({"sources": rows, "outbox": outbox or {}})


@app.get("/api/sync/export")
def sync_export(
    inventory_log_after: int = Query(0, ge=0),
    alert_record_after: int = Query(0, ge=0),
    env_log_after: int = Query(0, ge=0),
    pending_frames_after: int = Query(0, ge=0),
    batch_size: int = Query(200, ge=1, le=1000),
) -> dict[str, Any]:
    after_ids = {
        "inventory_log": inventory_log_after,
        "alert_record": alert_record_after,
        "env_log": env_log_after,
        "pending_frames": pending_frames_after,
    }
    tables: dict[str, list[dict[str, Any]]] = {}
    for table in ("produce_info", "stock_summary", "device_status"):
        columns = ", ".join(TABLE_COLUMNS[table])
        tables[table] = query_all(f"SELECT {columns} FROM {table}")
    for table, last_id in after_ids.items():
        columns = ", ".join(TABLE_COLUMNS[table])
        tables[table] = query_all(
            f"SELECT {columns} FROM {table} "
            "WHERE id > ? ORDER BY id LIMIT ?",
            (last_id, batch_size),
        )
    return ok({"sourceDeviceId": "fridge-01", "tables": tables})


@app.post("/api/sync/import")
def sync_import(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    try:
        result = apply_remote_operation(DB_PATH, payload)
    except (TypeError, ValueError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ok(result)


@app.websocket("/ws/notify")
async def websocket_notify(websocket: WebSocket) -> None:
    """Push current board data to connected Web dashboards."""
    await websocket.accept()
    ws_hub.register(websocket)
    try:
        while True:
            items = inventory_rows()
            alerts = alert_rows()
            await websocket.send_json(
                {"type": "environment:update", "payload": environment_data()}
            )
            await websocket.send_json(
                {
                    "type": "inventory:update",
                    "payload": {
                        "stock": sum(safe_float(item["quantity"]) for item in items),
                        "alerts": len(
                            [item for item in alerts if item["status"] == "pending"]
                        ),
                    },
                }
            )
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass
    finally:
        ws_hub.unregister(websocket)


@app.on_event("startup")
def ensure_database_schema() -> None:
    init_db(DB_PATH)


if BOARD_SOURCE_URL:
    @app.on_event("startup")
    def start_board_collector() -> None:
        start_background_collector(
            BOARD_SOURCE_URL,
            DB_PATH,
            COLLECTOR_STATE_PATH,
            int(os.environ.get("WAREHOUSE_SYNC_INTERVAL_SEC", "5")),
        )


@app.on_event("startup")
def start_alert_scan() -> None:
    """预警扫描任务：与开发板采集/同步链路无关，纯服务端业务逻辑。"""
    start_alert_scan_task()


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
                payload.get("category") or "",
                safe_int(payload.get("shelfLifeDays")),
                payload.get("idealTempRange") or "",
                payload.get("iconUrl") or "",
                payload.get("unit") or "件",
                payload.get("location") or "本地库存",
            ),
        )
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
            SET name = ?, category = ?, shelf_life_days = ?,
                ideal_temp_range = ?, icon_url = ?, unit = ?, location = ?
            WHERE id = ?
            """,
            (
                name,
                payload.get("category") or "",
                safe_int(payload.get("shelfLifeDays")),
                payload.get("idealTempRange") or "",
                payload.get("iconUrl") or "",
                payload.get("unit") or "件",
                payload.get("location") or "本地库存",
                produce_id,
            ),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="果蔬信息不存在")
    return ok(get_produce_item(produce_id))


@app.get("/api/alerts")
def alerts(status: str = "", level: str = "", keyword: str = "") -> dict[str, Any]:
    items = alert_rows()
    if status and status != "all":
        items = [item for item in items if item["status"] == status]
    if level and level != "all":
        items = [item for item in items if item["level"] == level]
    if keyword:
        lowered = keyword.lower()
        items = [
            item
            for item in items
            if lowered in f"{item['title']}{item['source']}{item['description']}".lower()
        ]
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
    return ok(history_rows(page, pageSize))


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


def image_response(image_path: Any) -> FileResponse:
    if not image_path:
        raise HTTPException(status_code=404, detail="图片路径不存在")
    path = Path(str(image_path))
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"图片文件不存在: {path}")
    return FileResponse(path, headers={"Cache-Control": "no-store"})


def proxy_board_image(path: str) -> Response:
    if not BOARD_SOURCE_URL:
        raise HTTPException(status_code=404, detail="图片文件不存在，且未配置板端地址")

    url = f"{BOARD_SOURCE_URL.rstrip('/')}{path}"
    request = urllib.request.Request(url, method="GET")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(request, timeout=10) as upstream:
            media_type = upstream.headers.get_content_type()
            content = upstream.read(MAX_PROXY_IMAGE_BYTES + 1)
    except urllib.error.HTTPError as exc:
        status_code = 404 if exc.code == 404 else 502
        raise HTTPException(
            status_code=status_code,
            detail=f"读取板端图片失败: HTTP {exc.code}",
        ) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise HTTPException(status_code=502, detail=f"无法连接板端图片接口: {exc}") from exc

    if not media_type.startswith("image/"):
        raise HTTPException(status_code=502, detail="板端返回的内容不是图片")
    if len(content) > MAX_PROXY_IMAGE_BYTES:
        raise HTTPException(status_code=502, detail="板端图片超过 10 MB 限制")
    return Response(
        content=content,
        media_type=media_type,
        headers={"Cache-Control": "no-store"},
    )


def proxy_board_frame(frame_id: int) -> Response:
    return proxy_board_image(f"/api/frames/{frame_id}/image")


def frame_image_response(frame_id: int, image_path: Any) -> Response:
    if image_path:
        path = Path(str(image_path))
        if path.is_file():
            return FileResponse(path, headers={"Cache-Control": "no-store"})
    return proxy_board_frame(frame_id)


@app.get("/api/frames/latest/image")
def latest_frame_image() -> Response:
    latest_path = Path(LATEST_FRAME_PATH)
    if latest_path.is_file():
        return FileResponse(latest_path, headers={"Cache-Control": "no-store"})
    if BOARD_SOURCE_URL:
        return proxy_board_image("/api/frames/latest/image")

    row = query_one(
        """
        SELECT id, image_path
        FROM pending_frames
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """
    )
    if not row:
        raise HTTPException(status_code=404, detail="暂无摄像头图片")
    return frame_image_response(int(row["id"]), row.get("image_path"))


@app.get("/api/frames/{frame_id}/image")
def frame_image(frame_id: int) -> Response:
    row = query_one("SELECT image_path FROM pending_frames WHERE id = ?", (frame_id,))
    if not row:
        raise HTTPException(status_code=404, detail="图片记录不存在")
    return frame_image_response(frame_id, row.get("image_path"))


@app.get("/api/frames/inventory-log/{log_id}/image")
def inventory_log_image(log_id: int) -> Response:
    row = query_one("SELECT image_path FROM inventory_log WHERE id = ?", (log_id,))
    image_path = row.get("image_path") if row else None
    if image_path:
        path = Path(str(image_path))
        if path.is_file():
            return FileResponse(path, headers={"Cache-Control": "no-store"})
    if BOARD_SOURCE_URL:
        return proxy_board_image(f"/api/frames/inventory-log/{log_id}/image")
    return image_response(image_path)
