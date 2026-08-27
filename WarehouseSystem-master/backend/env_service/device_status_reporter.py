"""定时写入 device_status 表：温湿度传感器子系统的心跳与状态。"""

import logging

from backend.common.db import connection_scope

logger = logging.getLogger("env_service.device_status_reporter")


class DeviceStatusReporter:
    def __init__(self, db_path: str, device_id: str):
        self.db_path = db_path
        self.device_id = device_id

    def report(self, sensor_ok: bool) -> None:
        status = "ok" if sensor_ok else "error"
        with connection_scope(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO device_status (device_id, sensor_status, last_heartbeat)
                VALUES (?, ?, datetime('now', 'localtime'))
                ON CONFLICT(device_id) DO UPDATE SET
                    sensor_status = excluded.sensor_status,
                    last_heartbeat = excluded.last_heartbeat
                """,
                (self.device_id, status),
            )
        logger.debug("device_status上报: sensor_status=%s", status)
