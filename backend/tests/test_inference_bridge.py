from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.common.db import connection_scope, get_connection
from backend.common.init_db import init_db
from backend.inference_bridge.config import BridgeConfig, default_produce_catalog
from backend.inference_bridge.instance_lock import InstanceLock, InstanceLockError
from backend.inference_bridge.service import InferenceBridge, WorkerOutcome


class InferenceBridgeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        root = Path(self.directory.name)
        self.main_db = str(root / "main.db")
        self.worker_db = str(root / "worker.db")
        init_db(self.main_db)
        init_db(self.worker_db)
        self.bridge = InferenceBridge(
            BridgeConfig(
                main_db_path=Path(self.main_db),
                worker_db_path=Path(self.worker_db),
                lock_path=root / "bridge.lock",
                poll_interval_sec=0.01,
                worker_timeout_sec=0.2,
                lease_renew_sec=0.05,
                stale_claim_minutes=5,
                max_attempts=3,
                model_version="test-bridge",
                produce_catalog=default_produce_catalog(),
            ),
            sleep=lambda _: None,
        )

    def tearDown(self) -> None:
        self.directory.cleanup()

    def _stock(self, name: str) -> float:
        with connection_scope(self.main_db) as conn:
            row = conn.execute(
                """
                SELECT COALESCE(s.current_qty, 0) AS qty
                FROM produce_info p
                LEFT JOIN stock_summary s ON s.produce_id = p.id
                WHERE p.name = ?
                ORDER BY p.id
                LIMIT 1
                """,
                (name,),
            ).fetchone()
            return float(row["qty"]) if row else -1

    def _movements(self, name: str) -> list[tuple[str, float]]:
        with connection_scope(self.main_db) as conn:
            rows = conn.execute(
                """
                SELECT l.action_type, l.quantity
                FROM inventory_log l
                JOIN produce_info p ON p.id = l.produce_id
                WHERE p.name = ? AND COALESCE(l.bbox_json, '') = ''
                ORDER BY l.id
                """,
                (name,),
            ).fetchall()
        return [(str(row["action_type"]), float(row["quantity"])) for row in rows]

    def _queue_main_frame(self, cycle_id: int, frame_id: int, image_name: str) -> None:
        image_path = str(Path(self.directory.name) / image_name)
        Path(image_path).write_bytes(b"fake-jpg")
        with connection_scope(self.main_db) as conn:
            conn.execute(
                """
                INSERT INTO door_cycle (id, status, frame_id)
                VALUES (?, 'processing', ?)
                """,
                (cycle_id, frame_id),
            )
            conn.execute(
                """
                INSERT INTO pending_frames
                    (id, image_path, change_ratio, status, door_cycle_id)
                VALUES (?, ?, 1.0, 'pending', ?)
                """,
                (frame_id, image_path, cycle_id),
            )

    def _simulate_old_ai(
        self,
        worker_frame_id: int,
        produce_names: list[str],
        status: str = "processed",
        attempt_count: int = 0,
        with_bbox: bool = True,
    ) -> None:
        with connection_scope(self.worker_db) as conn:
            conn.execute(
                """
                UPDATE pending_frames
                SET status = ?, attempt_count = ?,
                    processed_at = datetime('now', 'localtime')
                WHERE id = ?
                """,
                (status, attempt_count, worker_frame_id),
            )
            for index, name in enumerate(produce_names):
                produce = conn.execute(
                    "SELECT id FROM produce_info WHERE name = ?",
                    (name,),
                ).fetchone()
                bbox = (
                    '{"x1":1,"y1":1,"x2":10,"y2":10,"image_width":640,"image_height":480}'
                    if with_bbox
                    else ""
                )
                conn.execute(
                    """
                    INSERT INTO inventory_log
                        (produce_id, action_type, quantity, freshness_level,
                         confidence, source_frame_id, detector_label, bbox_json)
                    VALUES (?, 'IN', 1, 'fresh', 0.9, ?, ?, ?)
                    """,
                    (int(produce["id"]), worker_frame_id, f"{name}-{index}", bbox),
                )

    def _process_with_old_ai(
        self,
        produce_names: list[str],
        status: str = "processed",
        attempt_count: int = 0,
        with_bbox: bool = True,
    ) -> None:
        job = self.bridge.next_job()
        self.assertIsNotNone(job)
        assert job is not None
        self._simulate_old_ai(
            job.worker_frame_id,
            produce_names,
            status=status,
            attempt_count=attempt_count,
            with_bbox=with_bbox,
        )
        outcome = self.bridge.wait_for_worker(job)
        self.bridge.apply_outcome(job, outcome)

    def test_init_creates_inference_job_table(self) -> None:
        with connection_scope(self.main_db) as conn:
            names = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
        self.assertIn("inference_job", names)

    def test_worker_in1_does_not_copy_to_main_movements(self) -> None:
        self._queue_main_frame(1, 101, "frame-101.jpg")
        self._process_with_old_ai(["苹果", "苹果"])
        self.assertEqual(self._stock("苹果"), 2)
        self.assertEqual(self._movements("苹果"), [])
        with connection_scope(self.worker_db) as conn:
            worker_ins = conn.execute(
                "SELECT COUNT(*) FROM inventory_log WHERE action_type='IN'"
            ).fetchone()[0]
        with connection_scope(self.main_db) as conn:
            main_movements = conn.execute(
                "SELECT COUNT(*) FROM inventory_log WHERE COALESCE(bbox_json, '')=''"
            ).fetchone()[0]
        self.assertEqual(int(worker_ins), 2)
        self.assertEqual(int(main_movements), 0)

    def test_baseline_then_delta_and_same_count_has_no_movement(self) -> None:
        self._queue_main_frame(1, 101, "frame-101.jpg")
        self._process_with_old_ai(["苹果", "苹果", "香蕉"])
        self.assertEqual(self._stock("苹果"), 2)
        self.assertEqual(self._movements("苹果"), [])

        self._queue_main_frame(2, 102, "frame-102.jpg")
        self._process_with_old_ai(["苹果", "香蕉"])
        self.assertEqual(self._stock("苹果"), 1)
        self.assertEqual(self._movements("苹果"), [("OUT", 1.0)])

        self._queue_main_frame(3, 103, "frame-103.jpg")
        self._process_with_old_ai(["苹果", "香蕉"])
        self.assertEqual(self._stock("苹果"), 1)
        self.assertEqual(self._movements("苹果"), [("OUT", 1.0)])

        self._queue_main_frame(4, 104, "frame-104.jpg")
        self._process_with_old_ai(["苹果", "苹果", "香蕉"])
        self.assertEqual(self._movements("苹果"), [("OUT", 1.0), ("IN", 1.0)])

    def test_empty_result_requests_recapture_then_clears_stock(self) -> None:
        self._queue_main_frame(1, 201, "frame-201.jpg")
        self._process_with_old_ai(["苹果"])
        self._queue_main_frame(2, 202, "frame-202.jpg")
        self._process_with_old_ai([], status="discarded", attempt_count=0)
        with connection_scope(self.main_db) as conn:
            cycle = conn.execute(
                "SELECT status, retry_count FROM door_cycle WHERE id=2"
            ).fetchone()
        self.assertEqual((cycle["status"], cycle["retry_count"]), ("recapture_requested", 1))
        self.assertEqual(self._stock("苹果"), 1)

        with connection_scope(self.main_db) as conn:
            conn.execute(
                "UPDATE door_cycle SET status='processing', frame_id=203 WHERE id=2"
            )
            conn.execute(
                """
                INSERT INTO pending_frames
                    (id, image_path, change_ratio, status, door_cycle_id)
                VALUES (203, ?, 1.0, 'pending', 2)
                """,
                (str(Path(self.directory.name) / "frame-203.jpg"),),
            )
        self._process_with_old_ai([], status="discarded", attempt_count=0)
        self.assertEqual(self._stock("苹果"), 0)
        self.assertEqual(self._movements("苹果"), [("OUT", 1.0)])

    def test_worker_failures_do_not_clear_stock(self) -> None:
        self._queue_main_frame(1, 301, "frame-301.jpg")
        self._process_with_old_ai(["苹果"])
        self._queue_main_frame(2, 302, "frame-302.jpg")
        self._process_with_old_ai([], status="discarded", attempt_count=3)
        self.assertEqual(self._stock("苹果"), 1)
        with connection_scope(self.main_db) as conn:
            cycle = conn.execute(
                "SELECT status FROM door_cycle WHERE id=2"
            ).fetchone()
            job = conn.execute(
                "SELECT status FROM inference_job WHERE main_frame_id=302"
            ).fetchone()
        self.assertEqual(cycle["status"], "failed")
        self.assertEqual(job["status"], "failed")

    def test_apply_is_idempotent_in_one_transaction(self) -> None:
        self._queue_main_frame(1, 401, "frame-401.jpg")
        job = self.bridge.next_job()
        assert job is not None
        self._simulate_old_ai(job.worker_frame_id, ["苹果", "苹果"])
        outcome = self.bridge.wait_for_worker(job)
        self.bridge.apply_outcome(job, outcome)
        self.bridge.apply_outcome(job, outcome)
        self.assertEqual(self._stock("苹果"), 2)
        with connection_scope(self.main_db) as conn:
            snapshots = conn.execute(
                """
                SELECT COUNT(*) FROM inventory_log
                WHERE source_frame_id=401 AND COALESCE(bbox_json, '')<>''
                """
            ).fetchone()[0]
            job_row = conn.execute(
                "SELECT status FROM inference_job WHERE main_frame_id=401"
            ).fetchone()
        self.assertEqual(int(snapshots), 2)
        self.assertEqual(job_row["status"], "done")

    def test_results_and_job_rollback_together(self) -> None:
        self._queue_main_frame(1, 409, "frame-409.jpg")
        job = self.bridge.next_job()
        assert job is not None
        self._simulate_old_ai(job.worker_frame_id, ["苹果"])
        outcome = self.bridge.wait_for_worker(job)
        conn = get_connection(self.main_db)
        try:
            conn.execute("BEGIN")
            self.bridge.repository.save_results_on_connection(
                conn, job.main_frame_id, job.image_path, outcome.detections
            )
            conn.execute(
                """
                UPDATE inference_job
                SET status = 'done', finished_at = datetime('now', 'localtime')
                WHERE main_frame_id = ?
                """,
                (job.main_frame_id,),
            )
            conn.rollback()
        finally:
            conn.close()
        self.assertEqual(self._stock("苹果"), 0)
        with connection_scope(self.main_db) as db:
            job_row = db.execute(
                "SELECT status FROM inference_job WHERE main_frame_id=409"
            ).fetchone()
            cycle = db.execute("SELECT status FROM door_cycle WHERE id=1").fetchone()
        self.assertEqual(job_row["status"], "waiting")
        self.assertEqual(cycle["status"], "processing")

    def test_same_main_frame_is_not_claimed_twice(self) -> None:
        self._queue_main_frame(1, 501, "frame-501.jpg")
        first = self.bridge.claim_next_frame()
        second = self.bridge.claim_next_frame()
        self.assertEqual(first["id"], 501)
        self.assertIsNone(second)

    def test_failed_door_cycle_frame_is_not_claimed(self) -> None:
        self._queue_main_frame(1, 551, "frame-551.jpg")
        with connection_scope(self.main_db) as conn:
            conn.execute("UPDATE door_cycle SET status='failed' WHERE id=1")
        self.assertIsNone(self.bridge.claim_next_frame())
        with connection_scope(self.worker_db) as conn:
            worker_frames = conn.execute(
                "SELECT COUNT(*) FROM pending_frames"
            ).fetchone()[0]
        self.assertEqual(int(worker_frames), 0)

    def test_legacy_frame_without_door_cycle_is_discarded_not_inferred(self) -> None:
        with connection_scope(self.main_db) as conn:
            conn.execute(
                """
                INSERT INTO pending_frames (id, image_path, change_ratio, status)
                VALUES (553, ?, 0.5, 'pending')
                """,
                (str(Path(self.directory.name) / "legacy.jpg"),),
            )
        self.assertIsNone(self.bridge.claim_next_frame())
        self.assertEqual(self.bridge.discard_legacy_pending_frames(), 1)
        with connection_scope(self.main_db) as conn:
            frame = conn.execute(
                "SELECT status, last_error FROM pending_frames WHERE id=553"
            ).fetchone()
        self.assertEqual(frame["status"], "discarded")
        self.assertIn("遗留帧", frame["last_error"])

    def test_result_is_ignored_if_cycle_failed_while_worker_was_running(self) -> None:
        self._queue_main_frame(1, 552, "frame-552.jpg")
        job = self.bridge.next_job()
        assert job is not None
        self._simulate_old_ai(job.worker_frame_id, ["苹果"])
        outcome = self.bridge.wait_for_worker(job)
        with connection_scope(self.main_db) as conn:
            conn.execute("UPDATE door_cycle SET status='failed' WHERE id=1")
        self.bridge.apply_outcome(job, outcome)
        self.assertEqual(self._stock("苹果"), 0)
        with connection_scope(self.main_db) as conn:
            job_row = conn.execute(
                "SELECT status FROM inference_job WHERE main_frame_id=552"
            ).fetchone()
            logs = conn.execute(
                "SELECT COUNT(*) FROM inventory_log WHERE source_frame_id=552"
            ).fetchone()[0]
        self.assertEqual(job_row["status"], "failed")
        self.assertEqual(int(logs), 0)

    def test_lease_renewal_prevents_reclaim(self) -> None:
        self._queue_main_frame(1, 601, "frame-601.jpg")
        claimed = self.bridge.claim_next_frame()
        self.assertIsNotNone(claimed)
        with connection_scope(self.main_db) as conn:
            conn.execute(
                """
                UPDATE pending_frames
                SET claimed_at = datetime('now', 'localtime', '-10 minutes')
                WHERE id = 601
                """
            )
        self.assertTrue(self.bridge.renew_lease(601))
        self.assertIsNone(self.bridge.claim_next_frame())

    def test_timeout_does_not_change_stock(self) -> None:
        self._queue_main_frame(1, 701, "frame-701.jpg")
        self._process_with_old_ai(["苹果"])
        self._queue_main_frame(2, 702, "frame-702.jpg")
        job = self.bridge.next_job()
        assert job is not None
        outcome = self.bridge.wait_for_worker(job)
        self.assertEqual(outcome.kind, "timeout")
        self.bridge.apply_outcome(job, outcome)
        self.assertEqual(self._stock("苹果"), 1)
        with connection_scope(self.main_db) as conn:
            cycle = conn.execute("SELECT status FROM door_cycle WHERE id=2").fetchone()
        self.assertEqual(cycle["status"], "processing")

    def test_old_ai_without_bbox_still_counts_in1_rows(self) -> None:
        self._queue_main_frame(1, 801, "frame-801.jpg")
        self._process_with_old_ai(["香蕉", "香蕉"], with_bbox=False)
        self.assertEqual(self._stock("香蕉"), 2)

    def test_instance_lock_is_exclusive(self) -> None:
        lock_path = Path(self.directory.name) / "exclusive.lock"
        first = InstanceLock(lock_path)
        first.acquire()
        try:
            second = InstanceLock(lock_path)
            with self.assertRaises(InstanceLockError):
                second.acquire()
        finally:
            first.release()

    def test_main_and_worker_paths_must_differ(self) -> None:
        with self.assertRaises(ValueError):
            InferenceBridge(
                BridgeConfig(
                    main_db_path=Path(self.main_db),
                    worker_db_path=Path(self.main_db),
                    lock_path=Path(self.directory.name) / "bad.lock",
                    poll_interval_sec=0.01,
                    worker_timeout_sec=0.2,
                    lease_renew_sec=0.05,
                    stale_claim_minutes=5,
                    max_attempts=3,
                    model_version="test-bridge",
                    produce_catalog=default_produce_catalog(),
                )
            )


if __name__ == "__main__":
    unittest.main()
