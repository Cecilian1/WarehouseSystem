"""根据识别新鲜度、环境和入库时间估算果蔬剩余保存期。

模型只负责判断当前外观的新鲜度；本模块不加载模型，而是将模型输出和
SHT3x 温湿度采样组合成可供库存、日报和预警复用的业务结论。
"""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta
from typing import Any


LEVEL_RATIO = {
    "fresh": 1.0,
    "warning": 0.3,
    "spoiled": 0.0,
}

LEVEL_LABEL = {
    "fresh": "新鲜",
    "warning": "轻度不新鲜",
    "spoiled": "腐败变质",
}


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    text = str(value or "").strip()
    if not text:
        return None
    for pattern in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:19], pattern)
        except ValueError:
            continue
    return None


def freshness_level(level: Any, score: Any = None) -> str:
    """Map Chinese/English model labels and confidence scores to one stable level."""
    text = str(level or "").lower()
    if any(word in text for word in ("腐", "坏", "spoiled", "rotten", "expired")):
        return "spoiled"
    if any(word in text for word in ("临", "轻", "warning", "warn", "mild")):
        return "warning"
    if any(word in text for word in ("新鲜", "fresh")):
        return "fresh"

    numeric = _as_float(score)
    if numeric is None:
        # 手工录入和历史库存没有模型输出时，不应凭空降级为临期；仍由
        # 入库日期、人工过期日和环境公式决定其保存期。
        return "fresh"
    numeric = numeric * 100 if 0 <= numeric <= 1 else numeric
    if numeric < 40:
        return "spoiled"
    if numeric < 75:
        return "warning"
    return "fresh"


def predict_freshness_and_shelf_life(
    *,
    item_name: str,
    shelf_life_days: Any,
    freshness: Any,
    freshness_score: Any = None,
    temperature: Any = None,
    humidity: Any = None,
    inbound_at: Any = None,
    today: date | None = None,
) -> dict[str, Any]:
    """Return a transparent, bounded shelf-life estimate.

    The formula follows the supplied prototype: freshness level controls the
    usable-life ratio, while warmer and more humid environments shorten it.
    Missing environment data uses the design storage reference (4°C/85%RH),
    so a temporary sensor outage does not falsely accelerate spoilage.
    """
    reference_day = today or date.today()
    level = freshness_level(freshness, freshness_score)
    base_days = max(0.0, _as_float(shelf_life_days) or 0.0)
    current_temp = _as_float(temperature)
    current_humidity = _as_float(humidity)
    temp_for_formula = 4.0 if current_temp is None else current_temp
    humidity_for_formula = 85.0 if current_humidity is None else current_humidity

    # Clamp only pathological sensor values; normal measurements retain the
    # original formula exactly and cannot make the estimate negative/infinite.
    temp_factor = math.exp(0.08 * max(-30.0, min(50.0, temp_for_formula - 4.0)))
    humidity_factor = max(0.2, 1.0 + 0.003 * (humidity_for_formula - 85.0))
    environment_factor = max(0.2, min(5.0, temp_factor * humidity_factor))
    theoretical_days = base_days * LEVEL_RATIO[level] / environment_factor

    inbound_datetime = _as_datetime(inbound_at)
    stored_days: int | None = None
    if inbound_datetime is not None:
        stored_days = max(0, (reference_day - inbound_datetime.date()).days)
    remaining = max(0.0, theoretical_days - (stored_days or 0))

    status = level
    if remaining <= 0:
        status = "spoiled"
    status_label = "已过期" if remaining <= 0 else LEVEL_LABEL[status]

    if remaining <= 0:
        warning = f"{item_name}预计已过期，请立即处理。"
    elif stored_days is None:
        warning = f"{item_name}预计还能保存 {remaining:.1f} 天。"
    elif remaining <= 1:
        warning = f"{item_name}已存放 {stored_days} 天，预计 {remaining:.1f} 天内过期，请尽快食用。"
    elif remaining <= 3:
        warning = f"{item_name}已存放 {stored_days} 天，预计还能保存 {remaining:.1f} 天，请注意保鲜。"
    else:
        warning = f"{item_name}已存放 {stored_days} 天，预计还能保存 {remaining:.1f} 天。"

    device_alarms: list[str] = []
    if current_temp is not None and current_temp > 8.0:
        device_alarms.append(f"设备异常：当前温度 {current_temp:.1f}℃ 过高，请检查制冷系统。")
    if current_humidity is not None and current_humidity > 95.0:
        device_alarms.append(f"环境预警：当前湿度 {current_humidity:.1f}%RH 过高，请检查排水与通风。")

    estimated_expire = reference_day + timedelta(days=math.ceil(remaining))
    return {
        "freshness": status,
        "statusLabel": status_label,
        "storedDays": stored_days,
        "remainingDays": round(remaining, 1),
        "warningMessage": warning,
        "environmentFactor": round(environment_factor, 2),
        "estimatedExpireDate": estimated_expire.isoformat(),
        "deviceAlarms": device_alarms,
    }
