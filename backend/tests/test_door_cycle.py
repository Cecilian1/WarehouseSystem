from __future__ import annotations

import tempfile
import unittest
import sqlite3
import struct
from pathlib import Path

from backend.camera_service.door_cycle import DoorCycleRepository
from backend.camera_service.door_key_input import DoorKeyInput
from backend.camera_service.door_led_control import DoorLedControl
from backend.common.db import connection_scope
from backend.common.init_db import init_db


class DoorCycleTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.directory.name) / "door.db")
        init_db(self.db_path)
        self.repository = DoorCycleRepository(self.db_path)

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_open_close_capture_state_machine(self) -> None:
        with connection_scope(self.db_path) as conn:
            cycle_id = int(
                conn.execute(
                    "INSERT INTO door_cycle(status) VALUES('open_requested')"
                ).lastrowid
            )
        self.assertEqual(self.repository.next_action()["status"], "open_requested")
        self.assertTrue(self.repository.mark_open(cycle_id))
        self.assertTrue(self.repository.has_open_cycle())

        with connection_scope(self.db_path) as conn:
            conn.execute(
                "UPDATE door_cycle SET status='close_requested' WHERE id=?",
                (cycle_id,),
            )
        self.assertTrue(self.repository.claim_capture(cycle_id, "close_requested"))
        self.assertFalse(self.repository.claim_capture(cycle_id, "close_requested"))
        with connection_scope(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO pending_frames
                    (id, image_path, status, door_cycle_id)
                VALUES (10, 'frame.jpg', 'pending', ?)
                """,
                (cycle_id,),
            )
        self.repository.mark_processing(cycle_id, 10)
        with connection_scope(self.db_path) as conn:
            row = conn.execute(
                "SELECT status, frame_id FROM door_cycle WHERE id=?", (cycle_id,)
            ).fetchone()
        self.assertEqual((row["status"], row["frame_id"]), ("processing", 10))

    def test_interrupted_capture_is_requeued(self) -> None:
        with connection_scope(self.db_path) as conn:
            conn.execute(
                "INSERT INTO door_cycle(status, retry_count) VALUES('capturing', 1)"
            )
        self.repository.recover_interrupted_capture()
        self.assertEqual(self.repository.next_action()["status"], "recapture_requested")

    def test_physical_key_toggles_open_then_close(self) -> None:
        action, cycle_id = self.repository.request_toggle()
        self.assertEqual(action, "open_requested")
        self.assertTrue(self.repository.mark_open(cycle_id))

        action, same_cycle_id = self.repository.request_toggle()
        self.assertEqual((action, same_cycle_id), ("close_requested", cycle_id))
        action, same_cycle_id = self.repository.request_toggle()
        self.assertEqual((action, same_cycle_id), ("busy", cycle_id))

    def test_physical_key_reader_filters_release_repeat_and_other_keys(self) -> None:
        event_path = Path(self.directory.name) / "event1"
        event = struct.Struct("@llHHi")
        event_path.write_bytes(
            b"".join(
                [
                    event.pack(0, 0, 1, 114, 1),
                    event.pack(0, 0, 1, 114, 0),
                    event.pack(0, 0, 1, 114, 2),
                    event.pack(0, 0, 1, 115, 1),
                ]
            )
        )
        key = DoorKeyInput(str(event_path), key_code=114)
        try:
            self.assertEqual(key.read_presses(), 1)
            self.assertEqual(key.read_presses(), 0)
        finally:
            key.close()

    def test_board_led_brightness_file(self) -> None:
        led_dir = Path(self.directory.name) / "user-led"
        led_dir.mkdir()
        brightness = led_dir / "brightness"
        brightness.write_text("0")
        (led_dir / "max_brightness").write_text("255")
        led = DoorLedControl(str(brightness))
        led.turn_on()
        self.assertEqual(brightness.read_text(), "255")
        led.turn_off()
        self.assertEqual(brightness.read_text(), "0")

    def test_existing_pending_frames_table_is_migrated_idempotently(self) -> None:
        legacy_db = Path(self.directory.name) / "legacy.db"
        conn = sqlite3.connect(legacy_db)
        try:
            conn.execute(
                """
                CREATE TABLE pending_frames (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_path TEXT NOT NULL,
                    change_ratio REAL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT,
                    processed_at TEXT,
                    attempt_count INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT DEFAULT ''
                )
                """
            )
            conn.commit()
        finally:
            conn.close()
        init_db(str(legacy_db))
        init_db(str(legacy_db))
        conn = sqlite3.connect(legacy_db)
        try:
            columns = {
                row[1] for row in conn.execute("PRAGMA table_info(pending_frames)")
            }
            index = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' "
                "AND name='idx_pending_frames_door_cycle'"
            ).fetchone()
        finally:
            conn.close()
        self.assertIn("door_cycle_id", columns)
        self.assertIn("claimed_by", columns)
        self.assertIn("claimed_at", columns)
        self.assertIsNotNone(index)


if __name__ == "__main__":
    unittest.main()
