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
    def __init__(self, db_path: str, frame_save_dir: str):
        self.db_path = db_path
        self.frame_save_dir = Path(frame_save_dir)
        self.frame_save_dir.mkdir(parents=True, exist_ok=True)

    def save_and_register(self, frame: np.ndarray, change_ratio: float) -> int:
        """保存图片并写入pending_frames，返回新记录id。"""
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
