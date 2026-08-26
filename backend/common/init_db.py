"""初始化本地SQLite数据库：执行 schema.sql 建表，幂等可重复执行。

用法（在开发板上，两个服务启动前各自调用一次即可，重复调用无副作用）：
    python3 -m backend.common.init_db --db-path /data/warehousekeeper/warehousekeeper.db
"""

import argparse
import sqlite3
from pathlib import Path

from backend.common.db import get_connection

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


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


def _backfill_missing_stock_summaries(conn: sqlite3.Connection) -> None:
    """为历史识别日志补齐库存汇总，但绝不覆盖已有的人工库存汇总。"""
    conn.execute(
        """
        INSERT INTO stock_summary
            (produce_id, current_qty, earliest_expire_date, last_updated)
        SELECT
            l.produce_id,
            MAX(
                0,
                SUM(
                    CASE l.action_type
                        WHEN 'IN' THEN COALESCE(l.quantity, 0)
                        WHEN 'OUT' THEN -COALESCE(l.quantity, 0)
                        ELSE 0
                    END
                )
            ),
            '',
            datetime('now', 'localtime')
        FROM inventory_log l
        LEFT JOIN stock_summary s ON s.produce_id = l.produce_id
        WHERE s.produce_id IS NULL
        GROUP BY l.produce_id
        """
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
        _backfill_missing_stock_summaries(conn)
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
