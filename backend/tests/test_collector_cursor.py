from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.common.db import connection_scope
from backend.common.init_db import init_db
from backend.sync_service.collector import INCREMENTAL_TABLES, _reconcile_state


class CollectorCursorTest(unittest.TestCase):
    def test_negative_local_ids_never_become_board_cursors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = str(Path(directory) / "collector.db")
            init_db(db_path)
            with connection_scope(db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO alert_record (id, alert_type, is_read)
                    VALUES (-1, 'device_abnormal', 0)
                    """
                )

            reconciled = _reconcile_state(
                db_path,
                {table: 0 for table in INCREMENTAL_TABLES},
            )

        self.assertEqual(reconciled["alert_record"], 0)


if __name__ == "__main__":
    unittest.main()
