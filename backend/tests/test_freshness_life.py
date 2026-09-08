import unittest
from datetime import date
from pathlib import Path
import tempfile

from backend.api_service import helpers
from backend.common.freshness_life import predict_freshness_and_shelf_life
from backend.common.db import connection_scope
from backend.common.init_db import init_db


class FreshnessLifeTest(unittest.TestCase):
    def test_fresh_produce_uses_environment_and_storage_days(self) -> None:
        result = predict_freshness_and_shelf_life(
            item_name="苹果",
            shelf_life_days=14,
            freshness="fresh",
            freshness_score=0.9,
            temperature=4,
            humidity=85,
            inbound_at="2026-09-04",
            today=date(2026, 9, 6),
        )
        self.assertEqual(result["freshness"], "fresh")
        self.assertEqual(result["storedDays"], 2)
        self.assertEqual(result["remainingDays"], 12.0)
        self.assertEqual(result["environmentFactor"], 1.0)

    def test_mild_and_hot_environment_shortens_life_and_warns(self) -> None:
        result = predict_freshness_and_shelf_life(
            item_name="香蕉",
            shelf_life_days=7,
            freshness="轻度不新鲜",
            temperature=9,
            humidity=96,
            today=date(2026, 9, 6),
        )
        self.assertEqual(result["freshness"], "warning")
        self.assertLess(result["remainingDays"], 2.1)
        self.assertEqual(len(result["deviceAlarms"]), 2)

    def test_spoiled_produce_is_immediately_expired(self) -> None:
        result = predict_freshness_and_shelf_life(
            item_name="黄瓜",
            shelf_life_days=7,
            freshness="腐败变质",
            temperature=4,
            humidity=85,
            today=date(2026, 9, 6),
        )
        self.assertEqual(result["remainingDays"], 0.0)
        self.assertEqual(result["statusLabel"], "已过期")

    def test_inventory_uses_prediction_without_manual_expiry_date(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = str(Path(directory) / "shelf-life.db")
            init_db(db_path)
            original_db_path = helpers.DB_PATH
            helpers.DB_PATH = db_path
            try:
                with connection_scope(db_path) as conn:
                    cursor = conn.execute(
                        "INSERT INTO produce_info (name, category, shelf_life_days, unit) VALUES ('测试苹果', '水果', 10, '个')"
                    )
                    produce_id = cursor.lastrowid
                    conn.execute(
                        "INSERT INTO stock_summary (produce_id, current_qty, earliest_expire_date) VALUES (?, 2, '')",
                        (produce_id,),
                    )
                    conn.execute(
                        """
                        INSERT INTO inventory_log
                            (produce_id, action_type, quantity, freshness_level, freshness_score, created_at)
                        VALUES (?, 'IN', 2, 'fresh', 0.9, datetime('now', 'localtime', '-2 days'))
                        """,
                        (produce_id,),
                    )
                    conn.execute(
                        "INSERT INTO env_log (temperature, humidity, recorded_at, is_abnormal) VALUES (4, 85, datetime('now', 'localtime'), 0)"
                    )

                item = next(row for row in helpers.inventory_rows() if row["name"] == "测试苹果")
                self.assertEqual(item["remainingDays"], 8.0)
                self.assertEqual(item["freshness"], "fresh")
                self.assertIn("预计还能保存 8.0 天", item["storageAdvice"])
            finally:
                helpers.DB_PATH = original_db_path


if __name__ == "__main__":
    unittest.main()
