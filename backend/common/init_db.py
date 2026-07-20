"""初始化本地SQLite数据库：执行 schema.sql 建表，幂等可重复执行。

用法（在开发板上，两个服务启动前各自调用一次即可，重复调用无副作用）：
    python3 -m backend.common.init_db --db-path /data/warehousekeeper/warehousekeeper.db
"""

import argparse
import sqlite3
from pathlib import Path

from backend.common.db import get_connection

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def init_db(db_path: str) -> None:
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    conn = get_connection(db_path)
    try:
        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        conn.executescript(schema_sql)

        # 表升级：为已有的device_status表添加frontend_active列（如果不存在）
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(device_status)")
        columns = {row[1] for row in cursor.fetchall()}
        if 'frontend_active' not in columns:
            cursor.execute("ALTER TABLE device_status ADD COLUMN frontend_active INTEGER DEFAULT 0")
            print("已为device_status表添加frontend_active列")

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
