from __future__ import annotations

import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from backend.common.db import connection_scope
from backend.common.init_db import init_db
from backend.sync_service.push import (
    apply_remote_operation,
    push_pending_operations,
    queue_board_operation,
)


class BidirectionalSyncTest(unittest.TestCase):
    def test_pending_operation_reaches_board_exactly_once(self) -> None:
        workspace_tmp = Path(
            os.environ.get(
                "WAREHOUSE_TEST_TMP",
                Path(__file__).resolve().parents[2] / "data",
            )
        )
        workspace_tmp.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=workspace_tmp) as directory:
            pc_db = str(Path(directory) / "pc.db")
            board_db = str(Path(directory) / "board.db")
            init_db(pc_db)
            init_db(board_db)

            payload = {
                "produce": {
                    "id": -1,
                    "name": "双向同步测试香蕉",
                    "category": "水果",
                    "shelfLifeDays": 7,
                    "storageAdvice": "2-8°C",
                    "iconUrl": "",
                    "unit": "个",
                    "location": "A-02",
                },
                "stock": {"currentQty": 2, "earliestExpireDate": "2026-08-05"},
                "inventoryLog": {
                    "id": -1,
                    "actionType": "IN",
                    "quantity": 2,
                    "createdAt": "2026-07-29 23:00:00",
                },
            }
            with connection_scope(pc_db) as conn:
                conn.execute(
                    """
                    INSERT INTO inventory_log
                        (id, action_type, quantity, sync_status)
                    VALUES (-1, 'IN', 2, 'local')
                    """
                )
                queue_board_operation(
                    conn,
                    "inventory.inbound",
                    payload,
                    inventory_log_id=-1,
                )

            class Handler(BaseHTTPRequestHandler):
                def do_POST(self) -> None:  # noqa: N802
                    length = int(self.headers.get("Content-Length", "0"))
                    body = json.loads(self.rfile.read(length).decode("utf-8"))
                    result = apply_remote_operation(board_db, body)
                    response = json.dumps(
                        {"code": 0, "message": "ok", "data": result}
                    ).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(response)))
                    self.end_headers()
                    self.wfile.write(response)

                def log_message(self, format: str, *args: object) -> None:
                    return

            server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                board_url = f"http://127.0.0.1:{server.server_port}"
                first = push_pending_operations(board_url, pc_db)
                second = push_pending_operations(board_url, pc_db)
            finally:
                server.shutdown()
                server.server_close()

            self.assertEqual(first["pushed"], 1)
            self.assertEqual(second["pushed"], 0)
            with connection_scope(pc_db) as conn:
                outbox = conn.execute(
                    "SELECT status FROM board_sync_outbox"
                ).fetchone()
                log = conn.execute(
                    "SELECT sync_status FROM inventory_log WHERE id = -1"
                ).fetchone()
            self.assertEqual(outbox["status"], "synced")
            self.assertEqual(log["sync_status"], "synced")

            with connection_scope(board_db) as conn:
                stock = conn.execute(
                    """
                    SELECT p.name, p.unit, p.location, s.current_qty
                    FROM produce_info p
                    JOIN stock_summary s ON s.produce_id = p.id
                    WHERE p.id = -1
                    """
                ).fetchone()
                applied_count = conn.execute(
                    "SELECT COUNT(*) AS count FROM applied_remote_operation"
                ).fetchone()["count"]
            self.assertEqual(stock["name"], "双向同步测试香蕉")
            self.assertEqual(stock["unit"], "个")
            self.assertEqual(stock["location"], "A-02")
            self.assertEqual(stock["current_qty"], 2)
            self.assertEqual(applied_count, 1)


if __name__ == "__main__":
    unittest.main()
