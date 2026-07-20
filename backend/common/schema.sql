-- 芯鲜管家 本地SQLite数据库schema
-- 仅建本次任务涉及的表；inventory_log为AI识别服务预留，本次两个服务均不写入。
-- 全部使用 IF NOT EXISTS，保证 init_db.py 可幂等重复执行。

PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS produce_info (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    name             TEXT NOT NULL,
    category         TEXT,
    shelf_life_days  INTEGER,
    ideal_temp_range TEXT,
    icon_url         TEXT
);

CREATE TABLE IF NOT EXISTS inventory_log (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    produce_id       INTEGER REFERENCES produce_info(id),
    action_type      TEXT NOT NULL CHECK (action_type IN ('IN', 'OUT')),
    quantity         REAL,
    freshness_level  TEXT,
    freshness_score  REAL,
    confidence       REAL,
    image_path       TEXT,
    created_at       TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    sync_status      TEXT DEFAULT 'local'
);

CREATE TABLE IF NOT EXISTS stock_summary (
    produce_id           INTEGER PRIMARY KEY REFERENCES produce_info(id),
    current_qty          REAL DEFAULT 0,
    earliest_expire_date TEXT,
    last_updated         TEXT
);

CREATE TABLE IF NOT EXISTS alert_record (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    produce_id  INTEGER REFERENCES produce_info(id),  -- device_abnormal 类型时允许 NULL
    alert_type  TEXT NOT NULL,                         -- 'expiring' / 'expired' / 'device_abnormal'
    expire_date TEXT,                                   -- device_abnormal 类型时允许 NULL
    is_read     INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS device_status (
    device_id        TEXT PRIMARY KEY,
    camera_status    TEXT,
    sensor_status    TEXT,
    storage_free     INTEGER,
    last_heartbeat   TEXT,
    frontend_active  INTEGER DEFAULT 0  -- 1=前端正在运行，0=前端未运行或已停止
);

CREATE TABLE IF NOT EXISTS env_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    temperature REAL NOT NULL,
    humidity    REAL NOT NULL,
    recorded_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    is_abnormal INTEGER NOT NULL DEFAULT 0
);

-- camera_service的轻量事件队列：变化触发后的待处理帧，供未来AI服务消费。
-- status: pending(待处理) / processed(AI服务已处理) / discarded(人工/策略丢弃)
CREATE TABLE IF NOT EXISTS pending_frames (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    image_path    TEXT NOT NULL,
    change_ratio  REAL,
    status        TEXT NOT NULL DEFAULT 'pending',
    created_at    TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    processed_at  TEXT
);

CREATE INDEX IF NOT EXISTS idx_inventory_log_created_at ON inventory_log(created_at);
CREATE INDEX IF NOT EXISTS idx_alert_record_is_read ON alert_record(is_read);
CREATE INDEX IF NOT EXISTS idx_env_log_recorded_at ON env_log(recorded_at);
CREATE INDEX IF NOT EXISTS idx_pending_frames_status ON pending_frames(status);
