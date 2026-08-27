import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.api_service import daily_report, helpers
from backend.common.db import connection_scope
from backend.common.init_db import init_db


class DailyReportTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.directory.name) / "daily-report.db")
        init_db(self.db_path)
        self.original_db_path = helpers.DB_PATH
        helpers.DB_PATH = self.db_path

    def tearDown(self) -> None:
        helpers.DB_PATH = self.original_db_path
        self.directory.cleanup()

    def test_snapshot_uses_inventory_environment_and_alert_data(self) -> None:
        with connection_scope(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO produce_info
                    (id, name, category, shelf_life_days, unit)
                VALUES (1, '草莓', '水果', 5, '盒')
                """
            )
            conn.execute(
                """
                INSERT INTO stock_summary
                    (produce_id, current_qty, earliest_expire_date)
                VALUES (1, 5, date('now', '+1 day'))
                """
            )
            conn.execute(
                """
                INSERT INTO inventory_log
                    (produce_id, action_type, quantity, freshness_level,
                     freshness_score, created_at)
                VALUES (1, 'IN', 5, 'warning', 0.6, datetime('now', 'localtime'))
                """
            )
            conn.execute(
                """
                INSERT INTO env_log
                    (temperature, humidity, recorded_at, is_abnormal)
                VALUES (9.2, 94, datetime('now', 'localtime'), 1)
                """
            )
            conn.execute(
                """
                INSERT INTO alert_record
                    (produce_id, alert_type, expire_date, is_read)
                VALUES (1, 'expiring', date('now', '+1 day'), 0)
                """
            )

        snapshot = daily_report.build_daily_snapshot()

        self.assertEqual(snapshot["riskLevel"], "high")
        self.assertEqual(snapshot["inventory"]["totalQuantity"], 5)
        self.assertEqual(snapshot["freshness"]["warning"], 5)
        self.assertEqual(snapshot["freshness"]["averageScore"], 60)
        self.assertEqual(snapshot["environment"]["temperature"], 9.2)
        self.assertEqual(snapshot["environment"]["abnormalSamples"], 1)
        self.assertEqual(snapshot["alerts"]["pending"], 1)

    def test_missing_api_key_returns_local_report_without_exposing_secret(self) -> None:
        snapshot = daily_report.build_daily_snapshot()
        with patch.object(daily_report, "QWEN_API_KEY", ""):
            report = daily_report._assemble_report(snapshot)

        self.assertEqual(report["source"], "local-fallback")
        self.assertTrue(report["highlights"])
        self.assertTrue(report["recommendations"])
        self.assertNotIn("apiKey", report)
        self.assertNotIn("QWEN_API_KEY", report)


if __name__ == "__main__":
    unittest.main()
