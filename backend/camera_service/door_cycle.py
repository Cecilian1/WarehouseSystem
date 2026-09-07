"""Qt、camera_service 与 AI 服务之间的 SQLite 门周期状态机。"""

from typing import Any

from backend.common.db import connection_scope


class DoorCycleRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def next_action(self) -> dict[str, Any] | None:
        with connection_scope(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT id, status, retry_count
                FROM door_cycle
                WHERE status IN ('open_requested', 'close_requested',
                                 'recapture_requested')
                ORDER BY id
                LIMIT 1
                """
            ).fetchone()
            return dict(row) if row else None

    def has_open_cycle(self) -> bool:
        with connection_scope(self.db_path) as conn:
            row = conn.execute(
                "SELECT 1 FROM door_cycle WHERE status = 'open' LIMIT 1"
            ).fetchone()
            return row is not None

    def request_toggle(self) -> tuple[str, int]:
        """由实体按键原子提交开门或关门请求。

        返回 ``(open_requested|close_requested|busy, cycle_id)``。处理中按键
        不创建重复周期，Qt 与实体按键因而可以安全混用。
        """
        with connection_scope(self.db_path) as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                """
                SELECT id, status
                FROM door_cycle
                WHERE status NOT IN ('completed', 'failed')
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()
            if row is None:
                cursor = conn.execute(
                    """
                    INSERT INTO door_cycle(status, opened_at)
                    VALUES('open_requested', datetime('now', 'localtime'))
                    """
                )
                return "open_requested", int(cursor.lastrowid)

            cycle_id = int(row["id"])
            if str(row["status"]) != "open":
                return "busy", cycle_id

            cursor = conn.execute(
                """
                UPDATE door_cycle
                SET status = 'close_requested',
                    close_requested_at = datetime('now', 'localtime'),
                    last_error = ''
                WHERE id = ? AND status = 'open'
                """,
                (cycle_id,),
            )
            if cursor.rowcount == 1:
                return "close_requested", cycle_id
            return "busy", cycle_id

    def mark_open(self, cycle_id: int) -> bool:
        with connection_scope(self.db_path) as conn:
            cursor = conn.execute(
                """
                UPDATE door_cycle
                SET status = 'open', last_error = ''
                WHERE id = ? AND status = 'open_requested'
                """,
                (cycle_id,),
            )
            return cursor.rowcount == 1

    def claim_capture(self, cycle_id: int, expected_status: str) -> bool:
        if expected_status not in {"close_requested", "recapture_requested"}:
            raise ValueError(f"不支持的拍照状态: {expected_status}")
        with connection_scope(self.db_path) as conn:
            cursor = conn.execute(
                """
                UPDATE door_cycle
                SET status = 'capturing', last_error = ''
                WHERE id = ? AND status = ?
                """,
                (cycle_id, expected_status),
            )
            return cursor.rowcount == 1

    def mark_processing(self, cycle_id: int, frame_id: int) -> None:
        with connection_scope(self.db_path) as conn:
            conn.execute(
                """
                UPDATE door_cycle
                SET status = 'processing', frame_id = ?,
                    captured_at = datetime('now', 'localtime'), last_error = ''
                WHERE id = ? AND status = 'capturing'
                """,
                (frame_id, cycle_id),
            )

    def mark_failed(self, cycle_id: int, message: str) -> None:
        with connection_scope(self.db_path) as conn:
            conn.execute(
                """
                UPDATE door_cycle
                SET status = 'failed', completed_at = datetime('now', 'localtime'),
                    last_error = ?
                WHERE id = ?
                """,
                (message[:500], cycle_id),
            )

    def recover_interrupted_capture(self) -> None:
        """服务在读帧中退出时，重启后重新执行该次关门拍照。"""
        with connection_scope(self.db_path) as conn:
            conn.execute(
                """
                UPDATE door_cycle
                SET status = CASE WHEN retry_count > 0
                                  THEN 'recapture_requested'
                                  ELSE 'close_requested' END,
                    last_error = '摄像头服务重启，自动重新拍照'
                WHERE status = 'capturing'
                """
            )
