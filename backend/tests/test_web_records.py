from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi import HTTPException

from backend.api_service import alerts_engine, helpers
from backend.api_service.main import recognitions
from backend.common.db import connection_scope
from backend.common.init_db import init_db


class WebRecordsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.directory.name) / "web-records.db")
        init_db(self.db_path)
        self.original_helpers_db = helpers.DB_PATH
        self.original_alerts_db = alerts_engine.DB_PATH
        helpers.DB_PATH = self.db_path
        alerts_engine.DB_PATH = self.db_path

    def tearDown(self) -> None:
        helpers.DB_PATH = self.original_helpers_db
        alerts_engine.DB_PATH = self.original_alerts_db
        self.directory.cleanup()

    def test_recognition_history_is_empty_with_an_empty_inbound_ledger(self) -> None:
        data = recognitions(page=1, pageSize=12)["data"]

        self.assertEqual(data["list"], [])
        self.assertEqual(data["total"], 0)

    def test_recognition_history_matches_real_inbound_movements(self) -> None:
        with connection_scope(self.db_path) as conn:
            produce_id = conn.execute(
                "SELECT id FROM produce_info ORDER BY id LIMIT 1"
            ).fetchone()["id"]
            conn.execute(
                """
                INSERT INTO inventory_log
                    (produce_id, action_type, quantity, bbox_json)
                VALUES (?, 'IN', 2, '')
                """,
                (produce_id,),
            )
            conn.execute(
                """
                INSERT INTO inventory_log
                    (produce_id, action_type, quantity, bbox_json)
                VALUES (?, 'OUT', 1, '')
                """,
                (produce_id,),
            )
            conn.execute(
                """
                INSERT INTO inventory_log
                    (produce_id, action_type, quantity, bbox_json)
                VALUES (?, 'IN', 1, '{"x1": 0}')
                """,
                (produce_id,),
            )

        data = recognitions(page=1, pageSize=12)["data"]

        self.assertEqual(data["total"], 1)
        self.assertEqual(len(data["list"]), 1)
        self.assertEqual(data["list"][0]["action"], "IN")
        self.assertFalse(data["list"][0]["isRecognition"])

    def test_alert_action_is_persisted_and_returned(self) -> None:
        with connection_scope(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO alert_record (alert_type) VALUES ('device_abnormal')"
            )
            alert_id = int(cursor.lastrowid)

        result = alerts_engine.handle_alert(
            {"id": alert_id, "action": "ignore"}, user_id=0
        )["data"]

        self.assertEqual(result["status"], "ignored")
        self.assertEqual(helpers.alert_rows()[0]["status"], "ignored")
        with connection_scope(self.db_path) as conn:
            row = conn.execute(
                "SELECT is_read, handle_action, handled_at FROM alert_record WHERE id = ?",
                (alert_id,),
            ).fetchone()
        self.assertEqual(row["is_read"], 1)
        self.assertEqual(row["handle_action"], "ignore")
        self.assertTrue(row["handled_at"])

    def test_alert_action_rejects_unknown_values(self) -> None:
        with self.assertRaises(HTTPException) as context:
            alerts_engine.handle_alert({"id": 1, "action": "delete"}, user_id=0)

        self.assertEqual(context.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
