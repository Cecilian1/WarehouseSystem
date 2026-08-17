"""Compatibility endpoints used by the WeChat mini program.

The Web client keeps its existing paginated/list response shapes.  These
additional routes provide the richer single-item and trend payloads expected
by the mini program without changing the Web API contract.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from backend.api_service.helpers import (
    DB_PATH,
    environment_data,
    format_dt,
    humanize_heartbeat,
    inventory_rows,
    ok,
    query_all,
    query_one,
    recognition_rows,
    safe_float,
)

router = APIRouter()


def _percent(value: Any) -> int:
    numeric = safe_float(value)
    if numeric <= 1:
        numeric *= 100
    return max(0, min(100, round(numeric)))


def _mini_freshness(value: str) -> str:
    return "expiring" if value == "warning" else value


def _mini_inventory(item: dict[str, Any]) -> dict[str, Any]:
    expire_at = ""
    if item.get("remainingDays") is not None:
        expire_at = str(item.get("remainingDays"))
    return {
        **item,
        "freshness": _mini_freshness(str(item.get("freshness") or "fresh")),
        "freshnessScore": _percent(item.get("freshnessScore")),
        "confidence": 0,
        "updatedAt": item.get("inboundAt") or "",
        "expireAt": expire_at,
        "ideal": item.get("storageAdvice") or "",
        "advice": item.get("storageAdvice") or "",
        "exposure": "数据来自开发板与本机后端的同步记录",
        "icon": "",
    }


@router.get("/api/devices/status")
def device_status(deviceId: str = Query("fridge-01")) -> dict[str, Any]:
    row = query_one(
        """
        SELECT device_id, camera_status, sensor_status, storage_free, last_heartbeat
        FROM device_status
        WHERE device_id = ?
        ORDER BY last_heartbeat DESC
        LIMIT 1
        """,
        (deviceId,),
    )
    if not row:
        row = query_one(
            """
            SELECT device_id, camera_status, sensor_status, storage_free, last_heartbeat
            FROM device_status
            ORDER BY last_heartbeat DESC
            LIMIT 1
            """
        )
    environment = environment_data()
    return ok(
        {
            "id": row.get("device_id") if row else deviceId,
            "name": "ATK-DL2K0300 开发板",
            "code": row.get("device_id") if row else deviceId,
            "state": "online" if row else "offline",
            "lastSync": humanize_heartbeat(row.get("last_heartbeat") if row else None),
            "temperature": environment["temperature"],
            "humidity": environment["humidity"],
            "cameraStatus": row.get("camera_status") if row else "未上报",
            "sensorStatus": row.get("sensor_status") if row else "未上报",
            "firmware": "1.0",
            "model": "Loongson 2K0300",
            "storage": row.get("storage_free") if row else 0,
            "uptime": 100 if row else 0,
        }
    )


@router.get("/api/inventory/detail")
def inventory_detail(id: int = Query(...)) -> dict[str, Any]:
    item = next((row for row in inventory_rows() if int(row["id"]) == id), None)
    if not item:
        raise HTTPException(status_code=404, detail="库存不存在")

    timeline = [
        {
            "id": row["id"],
            "time": row["createdAt"],
            "action": "手动入库" if row["action"] == "IN" else "手动出库",
            "detail": f"{row['name']} {'+' if row['action'] == 'IN' else '-'}{row['quantity']}",
            "operator": "小程序" if int(row["id"]) >= 1_000_000_000 else "Edge AI",
        }
        for row in recognition_rows(200)
        if row.get("produceId") == id
    ][:10]
    latest = timeline[0] if timeline else None
    data = _mini_inventory(item)
    data["timeline"] = timeline
    data["latestSnapshot"] = (
        f"LOG-{latest['id']}" if latest else "暂无识别快照"
    )
    recognition = next(
        (row for row in recognition_rows(200) if row.get("produceId") == id),
        None,
    )
    if recognition:
        data["confidence"] = _percent(recognition.get("confidence"))
    return ok(data)


@router.get("/api/recognitions/latest")
def recognitions_latest() -> dict[str, Any]:
    # inventory_log records describe stock movements. They do not contain
    # bounding boxes and must never be painted as visual detections. Until a
    # real inference service persists target coordinates, this endpoint
    # reports an honest camera-only state.
    latest_frame = query_one(
        """
        SELECT id, created_at
        FROM pending_frames
        ORDER BY datetime(created_at) DESC, id DESC
        LIMIT 1
        """
    )
    return ok(
        {
            "id": latest_frame["id"] if latest_frame else 0,
            "frameNo": f"FRAME-{latest_frame['id']}" if latest_frame else "实时画面",
            "time": latest_frame["created_at"] if latest_frame else "",
            "status": "camera_only",
            "hasInference": False,
            "image": "/api/frames/latest/image",
            "latency": 0,
            "pipeline": [
                {"key": "capture", "name": "图像采集", "done": True, "cost": "实时画面"},
                {"key": "detect", "name": "果蔬识别", "done": False, "cost": "模型未接入"},
                {"key": "freshness", "name": "新鲜度分析", "done": False, "cost": "等待识别"},
                {"key": "done", "name": "写入库存", "done": False, "cost": "未写入"},
            ],
            "targets": [],
            "latencyTrend": [],
            "models": {
                "detect": "未接入",
                "classify": "未接入",
            },
        }
    )


def _history_days(range_value: str) -> int:
    text = str(range_value or "").lower()
    if "30" in text:
        return 30
    if "今日" in text or "today" in text or "1d" in text:
        return 1
    return 7


def _environment_history(days: int) -> list[dict[str, Any]]:
    rows = query_all(
        """
        SELECT
            date(recorded_at) AS day,
            MIN(temperature) AS temp_min,
            MAX(temperature) AS temp_max,
            MIN(humidity) AS humidity_min,
            MAX(humidity) AS humidity_max
        FROM env_log
        WHERE datetime(recorded_at) >= datetime('now', 'localtime', ?)
        GROUP BY date(recorded_at)
        ORDER BY day
        """,
        (f"-{days} days",),
    )
    return [
        {
            "date": datetime.fromisoformat(row["day"]).strftime("%m/%d")
            if row.get("day")
            else "",
            "tempMin": safe_float(row.get("temp_min")),
            "tempMax": safe_float(row.get("temp_max")),
            "humidityMin": safe_float(row.get("humidity_min")),
            "humidityMax": safe_float(row.get("humidity_max")),
            "points": [],
        }
        for row in rows
    ]


@router.get("/api/environment/current")
def environment_current(deviceId: str = Query("fridge-01")) -> dict[str, Any]:
    del deviceId
    current = environment_data()
    today_rows = _environment_history(1)
    today = today_rows[-1] if today_rows else {
        "date": datetime.now().strftime("%m/%d"),
        "tempMin": current["temperature"],
        "tempMax": current["temperature"],
        "humidityMin": current["humidity"],
        "humidityMax": current["humidity"],
        "points": current["trend"],
    }
    warning = current["temperatureState"] == "warning"
    offline = current["temperatureState"] == "offline"
    return ok(
        {
            "temperature": current["temperature"],
            "humidity": current["humidity"],
            "valid": current.get("valid", not offline),
            "state": "未上报" if offline else "异常" if warning else "适宜",
            "today": today,
            "analysis": (
                "暂无环境采集数据，请检查开发板连接。"
                if offline
                else "检测到环境异常，请检查传感器或制冷状态。"
                if warning
                else "当前数据来自开发板环境采集服务。"
            ),
        }
    )


@router.get("/api/environment/history")
def environment_history(range: str = Query("7d")) -> dict[str, Any]:
    return ok(_environment_history(_history_days(range)))
