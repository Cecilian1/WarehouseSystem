from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from backend.camera_service.pending_frame_writer import PendingFrameWriter
from backend.common.db import connection_scope
from backend.common.frame_cleanup import FrameRetentionCleaner, FrameRetentionPolicy
from backend.common.init_db import init_db


class BoardRetentionContractTest(unittest.TestCase):
    def _temporary_directory(self) -> tempfile.TemporaryDirectory[str]:
        workspace_tmp = Path(
            os.environ.get(
                "WAREHOUSE_TEST_TMP",
                Path(__file__).resolve().parents[2] / "data",
            )
        )
        workspace_tmp.mkdir(parents=True, exist_ok=True)
        return tempfile.TemporaryDirectory(dir=workspace_tmp)

    def test_cleanup_module_entrypoint_initializes_board_database(self) -> None:
        with self._temporary_directory() as directory:
            root = Path(directory)
            db_path = root / "new-board.db"
            frame_root = root / "frames"
            frame_root.mkdir()
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "backend.common.frame_cleanup",
                    "--db-path",
                    str(db_path),
                    "--frame-root",
                    str(frame_root),
                    "--completed-retention-days",
                    "7",
                    "--pending-retention-days",
                    "7",
                    "--max-completed-frames",
                    "1000",
                    "--max-pending-frames",
                    "1000",
                ],
                cwd=Path(__file__).resolve().parents[2],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(db_path.is_file())
            with connection_scope(str(db_path)) as conn:
                table = conn.execute(
                    """
                    SELECT name FROM sqlite_master
                    WHERE type = 'table' AND name = 'pending_frames'
                    """
                ).fetchone()
            self.assertIsNotNone(table)

    def test_init_db_upgrades_legacy_board_schema(self) -> None:
        with self._temporary_directory() as directory:
            db_path = Path(directory) / "legacy-board.db"
            conn = sqlite3.connect(db_path)
            try:
                conn.executescript(
                    """
                    CREATE TABLE inventory_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        produce_id INTEGER,
                        action_type TEXT NOT NULL,
                        quantity REAL,
                        freshness_level TEXT,
                        freshness_score REAL,
                        confidence REAL,
                        image_path TEXT,
                        created_at TEXT NOT NULL DEFAULT '',
                        sync_status TEXT DEFAULT 'local'
                    );
                    CREATE TABLE pending_frames (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        image_path TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'pending',
                        created_at TEXT NOT NULL,
                        processed_at TEXT
                    );
                    """
                )
                conn.commit()
            finally:
                conn.close()

            init_db(str(db_path))

            with connection_scope(str(db_path)) as upgraded:
                inventory_columns = {
                    str(row["name"])
                    for row in upgraded.execute(
                        "PRAGMA table_info(inventory_log)"
                    ).fetchall()
                }
                pending_columns = {
                    str(row["name"])
                    for row in upgraded.execute(
                        "PRAGMA table_info(pending_frames)"
                    ).fetchall()
                }

            self.assertTrue(
                {
                    "source_frame_id",
                    "detector_label",
                    "bbox_json",
                    "inference_latency_ms",
                    "model_version",
                }.issubset(inventory_columns)
            )
            self.assertTrue(
                {"attempt_count", "last_error"}.issubset(pending_columns)
            )

    def test_writer_stops_registering_when_pending_queue_is_full(self) -> None:
        with self._temporary_directory() as directory:
            root = Path(directory)
            db_path = root / "board.db"
            frame_root = root / "frames"
            init_db(str(db_path))
            writer = PendingFrameWriter(
                db_path=str(db_path),
                frame_save_dir=str(frame_root),
                max_pending_frames=2,
            )
            with connection_scope(str(db_path)) as conn:
                conn.executemany(
                    """
                    INSERT INTO pending_frames (image_path, status)
                    VALUES (?, 'pending')
                    """,
                    ((str(frame_root / "1.jpg"),), (str(frame_root / "2.jpg"),)),
                )

            with patch(
                "backend.camera_service.pending_frame_writer.cv2.imwrite"
            ) as image_write:
                frame_id = writer.save_and_register(None, 0.5)  # type: ignore[arg-type]
            self.assertIsNone(frame_id)
            image_write.assert_not_called()
            with connection_scope(str(db_path)) as conn:
                conn.execute(
                    "UPDATE pending_frames SET status = 'processed' WHERE id = 1"
                )
            self.assertTrue(writer._has_pending_capacity())

    def test_periodic_board_cleanup_only_removes_completed_frames(self) -> None:
        with self._temporary_directory() as directory:
            root = Path(directory)
            db_path = root / "board.db"
            frame_root = root / "frames"
            frame_root.mkdir()
            init_db(str(db_path))

            rows = (
                (1, frame_root / "pending.jpg", "pending", "2026-08-01 10:00:00"),
                (2, frame_root / "processing.jpg", "processing", "2026-08-01 10:00:00"),
                (3, frame_root / "processed-old.jpg", "processed", "2026-08-01 10:00:00"),
                (4, frame_root / "processed-new.jpg", "processed", "2026-08-02 10:00:00"),
            )
            with connection_scope(str(db_path)) as conn:
                for frame_id, image_path, status, created_at in rows:
                    image_path.write_bytes(b"jpeg")
                    conn.execute(
                        """
                        INSERT INTO pending_frames
                            (id, image_path, status, created_at)
                        VALUES (?, ?, ?, ?)
                        """,
                        (frame_id, str(image_path), status, created_at),
                    )

            cleaner = FrameRetentionCleaner(
                db_path=db_path,
                frame_root=frame_root,
                policy=FrameRetentionPolicy(
                    completed_retention_days=7,
                    pending_retention_days=0,
                    max_completed_frames=1000,
                    max_pending_frames=0,
                ),
            )
            cleaner.cleanup(datetime(2026, 8, 17, 12, 0, 0))

            with connection_scope(str(db_path)) as conn:
                remaining = {
                    str(row["status"])
                    for row in conn.execute(
                        "SELECT status FROM pending_frames"
                    ).fetchall()
                }

            self.assertEqual(remaining, {"pending", "processing", "processed"})
            self.assertTrue((frame_root / "pending.jpg").exists())
            self.assertTrue((frame_root / "processing.jpg").exists())
            self.assertFalse((frame_root / "processed-old.jpg").exists())


if __name__ == "__main__":
    unittest.main()
