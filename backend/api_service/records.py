"""小程序"记录"接口：复用 inventory_log 的识别/出入库数据，不新建表。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from backend.api_service.helpers import ok, recognition_rows

router = APIRouter()


def _to_record(item: dict[str, Any]) -> dict[str, Any]:
    is_inbound = item["action"] == "IN"
    sign = "+" if is_inbound else "-"
    return {
        "id": item["id"],
        "time": item["time"],
        "produceId": item.get("produceId"),
        "name": item["name"],
        "type": "inbound" if is_inbound else "outbound",
        "action": "自动入库" if is_inbound else "自动出库",
        "quantity": item["quantity"],
        "detail": f"{item['name']} {sign}{item['quantity']}件",
        "operator": "Edge AI",
        "status": "success",
        "confidence": item["confidence"],
        "snapshot": item.get("image"),
        "latency": item.get("latency", 0),
    }


@router.get("/api/records")
def records(type: str = "", keyword: str = "") -> dict[str, Any]:
    items = [_to_record(item) for item in recognition_rows(200)]
    if type and type != "全部":
        items = [item for item in items if item["type"] == type]
    if keyword:
        items = [
            item for item in items if keyword.lower() in f"{item['name']}{item['detail']}".lower()
        ]
    return ok(items)
