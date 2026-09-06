from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.ai_service.config import AIServiceConfig, ProduceDefinition
from backend.ai_service.contracts import Detection, FreshnessPrediction, RecognitionResult
from backend.ai_service.result_writer import RecognitionRepository
from backend.api_service import helpers
from backend.api_service.records import _to_record
from backend.common.catalog import PRODUCE_CATALOG
from backend.common.db import connection_scope
from backend.common.init_db import AI_STOCK_TRIGGER, init_db


def _config(db_path: str, crop_dir: Path) -> AIServiceConfig:
    return AIServiceConfig(
        db_path=Path(db_path),
        detector_model=Path("unused.onnx"),
        freshness_model=Path("unused.onnx"),
        crop_dir=crop_dir,
        detector_confidence=0.35,
        detector_iou=0.45,
        detector_image_size=640,
        bbox_padding_ratio=0.05,
        poll_interval_sec=1.0,
        max_attempts=3,
        onnx_threads=1,
        inventory_action="IN",
        update_stock_summary=False,
        model_version="test-model",
        produce_catalog={
            "apple": ProduceDefinition("苹果", "水果", 14, "个"),
            "banana": ProduceDefinition("香蕉", "水果", 7, "根"),
        },
    )


def _result(species: str, crop_path: Path) -> RecognitionResult:
    return RecognitionResult(
        detection=Detection((0, 0, 10, 10), species, species.title(), 0.9),
        freshness=FreshnessPrediction(
            "fresh",
            0.8,
            0.9,
            {"fresh": 0.8, "mild": 0.1, "rotten": 0.1},
            1.0,
        ),
        crop_path=crop_path,
        image_width=640,
        image_height=640,
        inference_latency_ms=12.0,
    )


class RecognitionStockTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.directory.name) / "stock.db")
        self.crop_dir = Path(self.directory.name) / "crops"
        self.crop_dir.mkdir()
        init_db(self.db_path)
        self.original_db_path = helpers.DB_PATH
        helpers.DB_PATH = self.db_path
        self.repository = RecognitionRepository(_config(self.db_path, self.crop_dir))

    def tearDown(self) -> None:
        helpers.DB_PATH = self.original_db_path
        self.directory.cleanup()

    def _stock(self, name: str) -> float:
        with connection_scope(self.db_path) as conn:
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

    def _queue_frame(self, frame_id: int = 1) -> None:
        with connection_scope(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO pending_frames (id, image_path, change_ratio, status)
                VALUES (?, ?, 0.4, 'pending')
                """,
                (frame_id, str(self.crop_dir / "frame.jpg")),
            )

    def test_init_seeds_catalog_and_drops_increment_trigger(self) -> None:
        with connection_scope(self.db_path) as conn:
            names = {
                row["name"]
                for row in conn.execute(
                    "SELECT name FROM produce_info ORDER BY id"
                ).fetchall()
            }
            zeros = conn.execute(
                """
                SELECT COUNT(*) AS total
                FROM produce_info p
                JOIN stock_summary s ON s.produce_id = p.id
                WHERE p.name IN (?, ?, ?, ?, ?) AND s.current_qty = 0
                """,
                tuple(item.name for item in PRODUCE_CATALOG),
            ).fetchone()["total"]
            trigger = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='trigger' AND name=?",
                (AI_STOCK_TRIGGER,),
            ).fetchone()
            conn.execute(
                f"""
                CREATE TRIGGER {AI_STOCK_TRIGGER}
                AFTER INSERT ON inventory_log
                BEGIN
                    SELECT 1;
                END
                """
            )
        self.assertEqual(names, {item.name for item in PRODUCE_CATALOG})
        self.assertEqual(zeros, 5)
        self.assertIsNone(trigger)

        init_db(self.db_path)
        with connection_scope(self.db_path) as conn:
            trigger = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='trigger' AND name=?",
                (AI_STOCK_TRIGGER,),
            ).fetchone()
        self.assertIsNone(trigger)

    def test_init_keeps_existing_qty_and_does_not_backfill_from_logs(self) -> None:
        with connection_scope(self.db_path) as conn:
            apple_id = conn.execute(
                "SELECT id FROM produce_info WHERE name='苹果' ORDER BY id LIMIT 1"
            ).fetchone()["id"]
            conn.execute(
                "UPDATE stock_summary SET current_qty = 9 WHERE produce_id = ?",
                (apple_id,),
            )
            conn.execute(
                """
                INSERT INTO produce_info (name, category)
                VALUES ('草莓', '水果')
                """
            )
            berry_id = conn.execute(
                "SELECT id FROM produce_info WHERE name='草莓'"
            ).fetchone()["id"]
            conn.execute(
                """
                INSERT INTO inventory_log
                    (produce_id, action_type, quantity, model_version)
                VALUES (?, 'IN', 8, 'test-model')
                """,
                (berry_id,),
            )

        init_db(self.db_path)
        self.assertEqual(self._stock("苹果"), 9)
        with connection_scope(self.db_path) as conn:
            berry_stock = conn.execute(
                "SELECT current_qty FROM stock_summary WHERE produce_id = "
                "(SELECT id FROM produce_info WHERE name='草莓')"
            ).fetchone()
        self.assertIsNone(berry_stock)

    def test_frame_count_sets_stock_instead_of_incrementing(self) -> None:
        apples = [_result("apple", self.crop_dir / "a1.jpg") for _ in range(2)]
        self._queue_frame(1)
        self.repository.save_results(1, self.crop_dir / "frame.jpg", apples)
        self.assertEqual(self._stock("苹果"), 2)

        self._queue_frame(2)
        self.repository.save_results(2, self.crop_dir / "frame.jpg", apples)
        self.assertEqual(self._stock("苹果"), 2)

        self._queue_frame(3)
        self.repository.save_results(
            3, self.crop_dir / "frame.jpg", [_result("banana", self.crop_dir / "b.jpg")]
        )
        self.assertEqual(self._stock("香蕉"), 1)
        self.assertEqual(self._stock("苹果"), 2)

    def test_resolve_reuses_existing_name_even_if_category_differs(self) -> None:
        with connection_scope(self.db_path) as conn:
            apple_id = conn.execute(
                "SELECT id FROM produce_info WHERE name='苹果' ORDER BY id LIMIT 1"
            ).fetchone()["id"]
            conn.execute(
                "UPDATE produce_info SET category='果类' WHERE id=?",
                (apple_id,),
            )

        self._queue_frame(1)
        self.repository.save_results(
            1, self.crop_dir / "frame.jpg", [_result("apple", self.crop_dir / "a.jpg")]
        )
        with connection_scope(self.db_path) as conn:
            names = [
                row["name"]
                for row in conn.execute(
                    "SELECT name FROM produce_info WHERE name='苹果' ORDER BY id"
                ).fetchall()
            ]
            used = conn.execute(
                "SELECT produce_id FROM inventory_log ORDER BY id DESC LIMIT 1"
            ).fetchone()["produce_id"]
        self.assertEqual(names, ["苹果"])
        self.assertEqual(used, apple_id)
        self.assertEqual(self._stock("苹果"), 1)

    def _movements(self, name: str) -> list[tuple[str, float]]:
        with connection_scope(self.db_path) as conn:
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

    def _today_inbound(self) -> float:
        today = helpers.query_one(
            """
            SELECT SUM(COALESCE(quantity, 0)) AS total
            FROM inventory_log
            WHERE action_type = 'IN'
              AND date(created_at) = date('now', 'localtime')
              AND COALESCE(bbox_json, '') = ''
            """
        )
        return helpers.safe_float(today.get("total") if today else None)

    def test_metrics_count_delta_and_manual_but_ignore_boxes(self) -> None:
        self._queue_frame(1)
        self.repository.save_results(
            1,
            self.crop_dir / "frame.jpg",
            [_result("apple", self.crop_dir / "a.jpg")],
        )
        with connection_scope(self.db_path) as conn:
            apple_id = conn.execute(
                "SELECT id FROM produce_info WHERE name='苹果' ORDER BY id LIMIT 1"
            ).fetchone()["id"]
            conn.execute(
                """
                INSERT INTO inventory_log
                    (produce_id, action_type, quantity, created_at)
                VALUES (?, 'IN', 4, datetime('now', 'localtime'))
                """,
                (apple_id,),
            )

        recognition = next(
            row for row in helpers.recognition_rows(10) if row.get("isRecognition")
        )
        movement = next(
            row for row in helpers.recognition_rows(10) if not row.get("isRecognition")
        )
        self.assertEqual(self._today_inbound(), 5)
        self.assertEqual(_to_record(recognition)["action"], "自动识别")
        self.assertEqual(_to_record(movement)["action"], "自动入库")
        self.assertIn("识别", _to_record(recognition)["detail"])

    def test_frame_delta_decides_inbound_and_outbound(self) -> None:
        apples = [_result("apple", self.crop_dir / "a1.jpg") for _ in range(2)]
        self._queue_frame(1)
        self.repository.save_results(1, self.crop_dir / "frame.jpg", apples)
        self.assertEqual(self._stock("苹果"), 2)
        self.assertEqual(self._movements("苹果"), [("IN", 2.0)])
        self.assertEqual(self._today_inbound(), 2)

        self._queue_frame(2)
        self.repository.save_results(2, self.crop_dir / "frame.jpg", apples)
        self.assertEqual(self._stock("苹果"), 2)
        self.assertEqual(self._movements("苹果"), [("IN", 2.0)])
        self.assertEqual(self._today_inbound(), 2)

        self._queue_frame(3)
        self.repository.save_results(
            3, self.crop_dir / "frame.jpg", [_result("apple", self.crop_dir / "a2.jpg")]
        )
        self.assertEqual(self._stock("苹果"), 1)
        self.assertEqual(self._movements("苹果"), [("IN", 2.0), ("OUT", 1.0)])

        self._queue_frame(4)
        self.repository.save_results(
            4, self.crop_dir / "frame.jpg", [_result("banana", self.crop_dir / "b.jpg")]
        )
        self.assertEqual(self._stock("香蕉"), 1)
        self.assertEqual(self._stock("苹果"), 1)
        self.assertEqual(self._movements("香蕉"), [("IN", 1.0)])
        self.assertEqual(self._movements("苹果"), [("IN", 2.0), ("OUT", 1.0)])


if __name__ == "__main__":
    unittest.main()
