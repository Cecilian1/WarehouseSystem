from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.api_service import helpers
from backend.api_service.miniprogram_compat import recognitions_latest
from backend.common.db import connection_scope
from backend.common.init_db import init_db


class RecognitionContractTest(unittest.TestCase):
    def test_inventory_logs_are_not_returned_as_detection_boxes(self) -> None:
        original_db_path = helpers.DB_PATH
        with tempfile.TemporaryDirectory() as directory:
            db_path = str(Path(directory) / "recognition.db")
            init_db(db_path)
            with connection_scope(db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO produce_info (id, name, category)
                    VALUES (1, '测试苹果', '水果')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO inventory_log
                        (produce_id, action_type, quantity, confidence, sync_status)
                    VALUES (1, 'IN', 3, 0.99, 'local')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO pending_frames
                        (id, image_path, change_ratio, status)
                    VALUES (7, '/tmp/latest.jpg', 0.4, 'pending')
                    """
                )

            helpers.DB_PATH = db_path
            try:
                data = recognitions_latest()["data"]
            finally:
                helpers.DB_PATH = original_db_path

        self.assertFalse(data["hasInference"])
        self.assertEqual(data["targets"], [])
        self.assertEqual(data["frameNo"], "FRAME-7")
        self.assertEqual(data["status"], "camera_only")
        self.assertFalse(data["pipeline"][1]["done"])


if __name__ == "__main__":
    unittest.main()
