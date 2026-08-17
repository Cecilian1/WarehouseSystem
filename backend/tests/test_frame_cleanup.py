from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from backend.common.db import connection_scope
from backend.common.frame_cleanup import (
    FrameRetentionCleaner,
    FrameRetentionPolicy,
)
from backend.common.init_db import init_db


class FrameRetentionCleanerTest(unittest.TestCase):
    def _temporary_directory(self) -> tempfile.TemporaryDirectory[str]:
        workspace_tmp = Path(
            os.environ.get(
                "WAREHOUSE_TEST_TMP",
                Path(__file__).resolve().parents[2] / "data",
            )
        )
        workspace_tmp.mkdir(parents=True, exist_ok=True)
        return tempfile.TemporaryDirectory(dir=workspace_tmp)

    def _insert_frame(
        self,
        db_path: Path,
        frame_id: int,
        image_path: Path,
        status: str,
        created_at: str,
    ) -> None:
        image_path.write_bytes(b"jpeg")
        with connection_scope(str(db_path)) as conn:
            conn.execute(
                """
                INSERT INTO pending_frames
                    (id, image_path, status, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (frame_id, str(image_path), status, created_at),
            )

    def test_cleanup_applies_age_and_count_limits(self) -> None:
        with self._temporary_directory() as directory:
            root = Path(directory)
            db_path = root / "cleanup.db"
            frame_root = root / "frames"
            frame_root.mkdir()
            init_db(str(db_path))

            self._insert_frame(
                db_path,
                1,
                frame_root / "processed-old.jpg",
                "processed",
                "2026-08-01 10:00:00",
            )
            self._insert_frame(
                db_path,
                2,
                frame_root / "processed-1.jpg",
                "processed",
                "2026-08-16 10:00:00",
            )
            self._insert_frame(
                db_path,
                3,
                frame_root / "processed-2.jpg",
                "discarded",
                "2026-08-16 11:00:00",
            )
            self._insert_frame(
                db_path,
                4,
                frame_root / "processed-3.jpg",
                "processed",
                "2026-08-16 12:00:00",
            )
            self._insert_frame(
                db_path,
                5,
                frame_root / "pending-old.jpg",
                "pending",
                "2026-08-01 10:00:00",
            )
            self._insert_frame(
                db_path,
                6,
                frame_root / "pending-new.jpg",
                "pending",
                "2026-08-16 12:00:00",
            )

            cleaner = FrameRetentionCleaner(
                db_path=db_path,
                frame_root=frame_root,
                policy=FrameRetentionPolicy(
                    completed_retention_days=7,
                    pending_retention_days=7,
                    max_completed_frames=2,
                    max_pending_frames=1,
                ),
            )
            result = cleaner.cleanup(datetime(2026, 8, 17, 12, 0, 0))

            with connection_scope(str(db_path)) as conn:
                remaining_ids = {
                    int(row["id"])
                    for row in conn.execute(
                        "SELECT id FROM pending_frames ORDER BY id"
                    ).fetchall()
                }

            self.assertEqual(remaining_ids, {3, 4, 6})
            self.assertEqual(result.records_deleted, 3)
            self.assertEqual(result.files_deleted, 3)
            self.assertFalse((frame_root / "processed-old.jpg").exists())
            self.assertFalse((frame_root / "processed-1.jpg").exists())
            self.assertFalse((frame_root / "pending-old.jpg").exists())

    def test_cleanup_preserves_latest_and_inventory_images(self) -> None:
        with self._temporary_directory() as directory:
            root = Path(directory)
            db_path = root / "cleanup.db"
            frame_root = root / "frames"
            frame_root.mkdir()
            init_db(str(db_path))

            latest_path = frame_root / "latest.jpg"
            inventory_path = frame_root / "recognized.jpg"
            self._insert_frame(
                db_path, 1, latest_path, "processed", "2026-08-01 10:00:00"
            )
            self._insert_frame(
                db_path, 2, inventory_path, "processed", "2026-08-01 10:00:00"
            )
            with connection_scope(str(db_path)) as conn:
                conn.execute(
                    """
                    INSERT INTO inventory_log
                        (action_type, quantity, image_path)
                    VALUES ('IN', 1, ?)
                    """,
                    (str(inventory_path),),
                )

            cleaner = FrameRetentionCleaner(
                db_path=db_path,
                frame_root=frame_root,
                policy=FrameRetentionPolicy(
                    completed_retention_days=1,
                    pending_retention_days=1,
                    max_completed_frames=1000,
                    max_pending_frames=1000,
                ),
            )
            result = cleaner.cleanup(datetime(2026, 8, 17, 12, 0, 0))

            self.assertTrue(latest_path.exists())
            self.assertTrue(inventory_path.exists())
            self.assertEqual(result.records_deleted, 1)
            self.assertEqual(result.files_preserved, 1)
            with connection_scope(str(db_path)) as conn:
                remaining_id = conn.execute(
                    "SELECT id FROM pending_frames"
                ).fetchone()["id"]
            self.assertEqual(remaining_id, 2)

    def test_cleanup_never_deletes_files_outside_frame_root(self) -> None:
        with self._temporary_directory() as directory:
            root = Path(directory)
            db_path = root / "cleanup.db"
            frame_root = root / "frames"
            frame_root.mkdir()
            init_db(str(db_path))

            outside_path = root / "outside.jpg"
            self._insert_frame(
                db_path, 1, outside_path, "processed", "2026-08-01 10:00:00"
            )
            self._insert_frame(
                db_path,
                2,
                frame_root / "newest.jpg",
                "processed",
                "2026-08-16 10:00:00",
            )
            cleaner = FrameRetentionCleaner(
                db_path=db_path,
                frame_root=frame_root,
                policy=FrameRetentionPolicy(completed_retention_days=1),
            )
            result = cleaner.cleanup(datetime(2026, 8, 17, 12, 0, 0))

            with connection_scope(str(db_path)) as conn:
                row_count = conn.execute(
                    "SELECT COUNT(*) AS count FROM pending_frames"
                ).fetchone()["count"]

            self.assertTrue(outside_path.exists())
            self.assertEqual(row_count, 2)
            self.assertEqual(result.unsafe_paths, 1)


if __name__ == "__main__":
    unittest.main()
