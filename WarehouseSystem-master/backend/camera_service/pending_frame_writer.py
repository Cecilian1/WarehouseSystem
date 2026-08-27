"""变化触发后：落盘图片 + 登记 pending_frames 表，供未来AI服务消费。

camera_service只负责INSERT，不写inventory_log（需要AI推理产出的
freshness_level/confidence等字段，职责不在本次任务范围）。
消费契约见 docs/interfaces.md。
"""

import logging
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from backend.common.db import connection_scope

logger = logging.getLogger("camera_service.pending_frame_writer")


class PendingFrameWriter:
    def __init__(
        self,
        db_path: str,
        frame_save_dir: str,
        max_pending_frames: int = 1000,
    ):
        self.db_path = db_path
        self.frame_save_dir = Path(frame_save_dir)
        self.max_pending_frames = max(0, max_pending_frames)
        self._queue_full_reported = False
        self.frame_save_dir.mkdir(parents=True, exist_ok=True)

    def _has_pending_capacity(self) -> bool:
        if self.max_pending_frames == 0:
            return True
        with connection_scope(self.db_path) as conn:
            pending_count = int(
                conn.execute(
                    """
                    SELECT COUNT(*)
                    FROM pending_frames
                    WHERE status = 'pending'
                    """
                ).fetchone()[0]
            )
        has_capacity = pending_count < self.max_pending_frames
        if not has_capacity and not self._queue_full_reported:
            logger.warning(
                "待识别图片已达上限%d，暂停新增变化帧；AI处理或服务重启清理后自动恢复",
                self.max_pending_frames,
            )
        self._queue_full_reported = not has_capacity
        return has_capacity

    def save_latest(self, frame: np.ndarray, filename: str = "latest.jpg") -> Path:
        """原子更新供Web预览的最新帧，不写入pending_frames。"""
        image_path = self.frame_save_dir / Path(filename).name
        temp_path = image_path.with_name(f".{image_path.stem}.tmp{image_path.suffix}")
        if not cv2.imwrite(str(temp_path), frame):
            raise OSError(f"最新帧写入失败: {temp_path}")
        temp_path.replace(image_path)
        return image_path

    def save_and_register(
        self,
        frame: np.ndarray,
        change_ratio: float,
    ) -> int | None:
        """保存图片并写入pending_frames，返回新记录id。"""
        if not self._has_pending_capacity():
            return None
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"frame_{timestamp}.jpg"
        image_path = str(self.frame_save_dir / filename)

        cv2.imwrite(image_path, frame)

        with connection_scope(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO pending_frames (image_path, change_ratio, status)
                VALUES (?, ?, 'pending')
                """,
                (image_path, change_ratio),
            )
            frame_id = cursor.lastrowid

        logger.info(
            "触发变化(ratio=%.3f)，已保存帧: %s (pending_frames.id=%d)",
            change_ratio,
            image_path,
            frame_id,
        )
        return frame_id
