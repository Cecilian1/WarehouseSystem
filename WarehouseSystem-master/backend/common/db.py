"""SQLite连接封装：统一WAL模式与忙等超时，供camera_service/env_service共用。

三个进程（Qt前端 + camera_service + env_service）并发访问同一个.db文件，
必须开启WAL模式并设置busy_timeout，避免"database is locked"直接报错。
"""

import sqlite3
from contextlib import contextmanager


def get_connection(db_path: str) -> sqlite3.Connection:
    """打开一个配置好WAL/busy_timeout的连接。

    调用方负责关闭连接（或使用 connection_scope）。
    """
    conn = sqlite3.connect(db_path, timeout=5.0)
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 3000;")
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def connection_scope(db_path: str):
    """with connection_scope(db_path) as conn: ... 用法，退出时自动提交/回滚并关闭。"""
    conn = get_connection(db_path)
    try:
        with conn:
            yield conn
    finally:
        conn.close()
