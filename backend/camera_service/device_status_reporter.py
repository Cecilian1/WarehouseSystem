"""定时写入 device_status 表：摄像头子系统的心跳与状态。"""

import logging
import shutil

from backend.common.db import connection_scope

logger = logging.getLogger("camera_service.device_status_reporter")


class DeviceStatusReporter:
    def __init__(self, db_path: str, device_id: str, storage_path: str = "/"):
        self.db_path = db_path
        self.device_id = device_id
        self.storage_path = storage_path

    def report(self, camera_ok: bool) -> None:
        status = "ok" if camera_ok else "error"
        try:
            storage_free = shutil.disk_usage(self.storage_path).free
        except OSError:
            storage_free = None

        with connection_scope(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO device_status (device_id, camera_status, storage_free, last_heartbeat)
                VALUES (?, ?, ?, datetime('now', 'localtime'))
                ON CONFLICT(device_id) DO UPDATE SET
                    camera_status = excluded.camera_status,
                    storage_free = excluded.storage_free,
                    last_heartbeat = excluded.last_heartbeat
                """,
                (self.device_id, status, storage_free),
            )
        logger.debug("device_status上报: camera_status=%s", status)
