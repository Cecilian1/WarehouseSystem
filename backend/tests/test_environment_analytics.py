import tempfile
import unittest
from pathlib import Path

from backend.api_service import helpers, main
from backend.common.db import connection_scope
from backend.common.init_db import init_db


class EnvironmentAnalyticsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.directory.name) / "environment-analytics.db")
        init_db(self.db_path)
        self.original_db_path = helpers.DB_PATH
        helpers.DB_PATH = self.db_path

        with connection_scope(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO produce_info (name, category, shelf_life_days, unit)
                VALUES ('测试草莓', '水果', 5, '盒')
                """
            )
            produce_id = cursor.lastrowid
            conn.execute(
                """
                INSERT INTO stock_summary (produce_id, current_qty, earliest_expire_date)
                VALUES (?, 3, date('now', '+3 days'))
                """,
                (produce_id,),
            )
            conn.execute(
                """
                INSERT INTO inventory_log
                    (produce_id, action_type, quantity, freshness_level, freshness_score,
                     detector_confidence, created_at)
                VALUES (?, 'IN', 5, 'fresh', 0.95, 0.93, datetime('now', 'localtime', '-20 minutes'))
                """,
                (produce_id,),
            )
            conn.execute(
                """
                INSERT INTO inventory_log
                    (produce_id, action_type, quantity, freshness_level, freshness_score,
                     detector_confidence, created_at)
                VALUES (?, 'OUT', 2, 'fresh', 0.95, 0.97, datetime('now', 'localtime', '-10 minutes'))
                """,
                (produce_id,),
            )
            conn.execute(
                """
                INSERT INTO env_log (temperature, humidity, recorded_at, is_abnormal)
                VALUES (3.4, 88.2, datetime('now', 'localtime', '-6 minutes'), 0)
                """
            )
            conn.execute(
                """
                INSERT INTO env_log (temperature, humidity, recorded_at, is_abnormal)
                VALUES (3.8, 89.1, datetime('now', 'localtime', '-3 minutes'), 0)
                """
            )

    def tearDown(self) -> None:
        helpers.DB_PATH = self.original_db_path
        self.directory.cleanup()

    def test_environment_endpoint_returns_real_history_and_summary(self) -> None:
        payload = main.environment("24h")["data"]

        self.assertTrue(payload["valid"])
        self.assertEqual(payload["temperature"], 3.8)
        self.assertEqual(payload["summary"]["sampleCount"], 2)
        self.assertEqual(payload["summary"]["abnormalCount"], 0)
        self.assertEqual(len(payload["trend"]), 2)
        self.assertAlmostEqual(payload["summary"]["temperature"]["average"], 3.6)

    def test_analytics_endpoint_returns_kpis_and_heatmap(self) -> None:
        payload = main.analytics("month")["data"]

        self.assertEqual(payload["range"], "month")
        self.assertEqual(payload["kpis"]["recognitionCount"], 2)
        self.assertEqual(payload["kpis"]["totalInbound"], 5.0)
        self.assertEqual(payload["kpis"]["totalOutbound"], 2.0)
        self.assertEqual(payload["kpis"]["accuracy"], 95.0)
        self.assertTrue(payload["daily"])
        self.assertTrue(payload["heatmap"])
        self.assertEqual(len(payload["radar"]), 6)


if __name__ == "__main__":
    unittest.main()
