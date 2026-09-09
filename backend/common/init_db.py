"""初始化本地SQLite数据库：执行 schema.sql 建表，幂等可重复执行。

用法（在开发板上，两个服务启动前各自调用一次即可，重复调用无副作用）：
    python3 -m backend.common.init_db --db-path /data/warehousekeeper/warehousekeeper.db
"""

import argparse
import sqlite3
from pathlib import Path

from backend.common.catalog import PRODUCE_CATALOG
from backend.common.db import get_connection

SCHEMA_PATH = Path(__file__).parent / "schema.sql"
AI_STOCK_TRIGGER = "inventory_log_ai_stock_after_insert"


def _ensure_column(
    conn: sqlite3.Connection,
    table: str,
    column: str,
    definition: str,
) -> None:
    columns = {
        str(row["name"])
        for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
    }
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _seed_produce_catalog(conn: sqlite3.Connection) -> None:
    """预置五种果蔬；已有同名行复用，缺库存汇总时补 0，绝不按识别流水回填。"""
    for item in PRODUCE_CATALOG:
        row = conn.execute(
            """
            SELECT id FROM produce_info
            WHERE name = ?
            ORDER BY id
            LIMIT 1
            """,
            (item.name,),
        ).fetchone()
        if row:
            produce_id = int(row["id"])
        else:
            cursor = conn.execute(
                """
                INSERT INTO produce_info
                    (name, category, shelf_life_days, unit, location)
                VALUES (?, ?, ?, ?, '本地库存')
                """,
                (item.name, item.category, item.shelf_life_days, item.unit),
            )
            produce_id = int(cursor.lastrowid)
        conn.execute(
            """
            INSERT INTO stock_summary
                (produce_id, current_qty, earliest_expire_date, last_updated)
            SELECT ?, 0, '', datetime('now', 'localtime')
            WHERE NOT EXISTS (
                SELECT 1 FROM stock_summary WHERE produce_id = ?
            )
            """,
            (produce_id, produce_id),
        )


def init_db(db_path: str) -> None:
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    conn = get_connection(db_path)
    try:
        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        conn.executescript(schema_sql)
        _ensure_column(conn, "produce_info", "unit", "TEXT DEFAULT '件'")
        _ensure_column(
            conn,
            "produce_info",
            "location",
            "TEXT DEFAULT '本地库存'",
        )
        inventory_columns = {
            "source_frame_id": "INTEGER",
            "detector_label": "TEXT",
            "detector_confidence": "REAL",
            "freshness_confidence": "REAL",
            "bbox_json": "TEXT",
            "freshness_probabilities_json": "TEXT",
            "inference_latency_ms": "REAL",
            "model_version": "TEXT",
        }
        for column, definition in inventory_columns.items():
            _ensure_column(conn, "inventory_log", column, definition)
        _ensure_column(
            conn,
            "pending_frames",
            "attempt_count",
            "INTEGER NOT NULL DEFAULT 0",
        )
        _ensure_column(
            conn,
            "pending_frames",
            "last_error",
            "TEXT DEFAULT ''",
        )
        _ensure_column(
            conn,
            "pending_frames",
            "door_cycle_id",
            "INTEGER REFERENCES door_cycle(id)",
        )
        _ensure_column(conn, "pending_frames", "claimed_by", "TEXT")
        _ensure_column(conn, "pending_frames", "claimed_at", "TEXT")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_pending_frames_door_cycle "
            "ON pending_frames(door_cycle_id)"
        )
        conn.execute(f"DROP TRIGGER IF EXISTS {AI_STOCK_TRIGGER}")
        _seed_produce_catalog(conn)
        # 零库存没有可过期的批次。升级旧数据库时一并清理历史残留日期，
        # 避免库存面板把保质期日期误显示成识别时间。
        conn.execute(
            """
            UPDATE stock_summary
            SET earliest_expire_date = NULL
            WHERE COALESCE(current_qty, 0) <= 0
              AND COALESCE(earliest_expire_date, '') <> ''
            """
        )
        conn.commit()
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="初始化芯鲜管家本地SQLite数据库")
    parser.add_argument(
        "--db-path",
        default="/data/warehousekeeper/warehousekeeper.db",
        help="SQLite数据库文件路径",
    )
    args = parser.parse_args()
    init_db(args.db_path)
    print(f"数据库已初始化: {args.db_path}")


if __name__ == "__main__":
    main()
