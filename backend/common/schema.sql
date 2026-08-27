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
    icon_url         TEXT,
    unit             TEXT DEFAULT '件',
    location         TEXT DEFAULT '本地库存'
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
    source_frame_id  INTEGER,
    detector_label   TEXT,
    detector_confidence REAL,
    freshness_confidence REAL,
    bbox_json        TEXT,
    freshness_probabilities_json TEXT,
    inference_latency_ms REAL,
    model_version    TEXT,
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
    device_id      TEXT PRIMARY KEY,
    camera_status  TEXT,
    sensor_status  TEXT,
    storage_free   INTEGER,
    last_heartbeat TEXT
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
    processed_at  TEXT,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    last_error    TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS sync_source_status (
    source_device_id TEXT PRIMARY KEY,
    last_sync_at     TEXT NOT NULL,
    last_counts_json TEXT NOT NULL
);

-- 电脑端写操作回传开发板的可靠队列。断网时保留 pending/failed，重连后重试。
CREATE TABLE IF NOT EXISTS board_sync_outbox (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_id     TEXT NOT NULL UNIQUE,
    operation_type   TEXT NOT NULL,
    payload_json     TEXT NOT NULL,
    inventory_log_id INTEGER,
    status           TEXT NOT NULL DEFAULT 'pending',
    attempts         INTEGER NOT NULL DEFAULT 0,
    last_error       TEXT DEFAULT '',
    created_at       TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    synced_at        TEXT
);

-- 开发板记录已应用的电脑端操作，保证网络重试不会重复加减库存。
CREATE TABLE IF NOT EXISTS applied_remote_operation (
    operation_id   TEXT PRIMARY KEY,
    operation_type TEXT NOT NULL,
    applied_at     TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_inventory_log_created_at ON inventory_log(created_at);
CREATE INDEX IF NOT EXISTS idx_alert_record_is_read ON alert_record(is_read);
CREATE INDEX IF NOT EXISTS idx_env_log_recorded_at ON env_log(recorded_at);
CREATE INDEX IF NOT EXISTS idx_pending_frames_status ON pending_frames(status);
CREATE INDEX IF NOT EXISTS idx_board_sync_outbox_status ON board_sync_outbox(status, id);

-- 以下为 Web/小程序客户端业务接口所需的表，均为服务端(api_service)新增，
-- 与开发板采集/同步链路（camera_service/env_service/sync_service）无关。

-- 微信用户（openid 唯一）
CREATE TABLE IF NOT EXISTS app_user (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    openid       TEXT NOT NULL UNIQUE,
    nickname     TEXT,
    avatar_url   TEXT,
    created_at   TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- 登录会话：一个不透明 token 对应一个用户，供 Bearer 鉴权使用
CREATE TABLE IF NOT EXISTS auth_session (
    token       TEXT PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES app_user(id),
    created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    expires_at  TEXT NOT NULL
);

-- 用户与设备编号的绑定关系
CREATE TABLE IF NOT EXISTS user_device (
    user_id     INTEGER NOT NULL REFERENCES app_user(id),
    device_id   TEXT NOT NULL,
    bound_at    TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    PRIMARY KEY (user_id, device_id)
);

-- 系统设置：key/value，POST /api/settings 落库，GET /api/settings 回显
CREATE TABLE IF NOT EXISTS app_setting (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    updated_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_auth_session_user_id ON auth_session(user_id);
