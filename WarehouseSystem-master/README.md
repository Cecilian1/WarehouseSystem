# 芯鲜管家 — WarehouseSystem

面向家庭冰箱场景的果蔬仓储管理系统，运行于龙芯2K0300（LS2K0300B）+ 正点原子ATK-DL2K0300B开发板。

## 本次任务范围

本仓库当前只落地完整实现方案中的三个模块：

1. **6.1 本地终端屏幕**（LCD触摸屏 + Qt人机交互）—— `qt-frontend/`
2. **设备采集服务**（摄像头）—— `backend/camera_service/`
3. **环境监测服务**（温湿度传感器）—— `backend/env_service/`

**不包含**：AI推理（YOLOv11n/MobileNetV3新鲜度分类）、云同步、Web管理后台、移动端。这些是后续任务的范围。本次交付的表结构（`pending_frames`/`inventory_log`等）已为后续AI服务模块预留好对接点，约定见 [docs/interfaces.md](docs/interfaces.md)。

## 目录结构

```
WarehouseSystem/
├── docs/                     # 环境搭建、部署、验证、硬件事实、接口契约文档
├── qt-frontend/              # Qt Widgets本地终端UI（qmake工程）
├── web-frontend/             # Web管理端（Vue 3 + Vite）
├── wechat-miniprogram/       # 微信小程序前端
├── backend/
│   ├── common/               # 数据库连接/schema/配置读取等共享代码
│   ├── api_service/          # Web/小程序读取本地SQLite的FastAPI服务
│   ├── sync_service/         # 从开发板增量拉取数据到本机SQLite的采集器
│   ├── camera_service/       # 摄像头采集+帧间差分触发服务（跑在开发板上）
│   └── env_service/          # 温湿度采集+设备异常检测服务（跑在开发板上）
├── scripts/                  # 开发辅助脚本（如 .env → 小程序配置同步）
├── .env                       # 统一环境配置（后端/Web前端/小程序共用）
└── deploy/                   # systemd单元、开发板安装脚本、Windows启动脚本
```

## 快速开始 —— 开发板侧（Qt终端 + 采集服务）

1. 按 [docs/qt5-setup-guide.md](docs/qt5-setup-guide.md) 搭建Qt5交叉编译环境
2. 按 [docs/build-and-deploy.md](docs/build-and-deploy.md) 交叉编译Qt前端、部署Python后端
3. 按 [docs/verification-checklist.md](docs/verification-checklist.md) 逐项验证

## 快速开始 —— PC侧（后端 API + Web前端 + 小程序）

以下三个服务共用仓库根目录下的同一份 `.env` 配置文件（微信小程序除外，见下方说明）。

### 0. 修改 .env

仓库根目录的 `.env` 已包含可直接运行的默认配置，按需修改（各项含义详见文件内注释）：

| 变量 | 何时必须修改 |
| --- | --- |
| `WAREHOUSE_BOARD_SOURCE_URL` | 要从真实开发板同步数据时，改成开发板当前的局域网 IP；没有开发板可以不管，服务会定时重试并在日志里打印失败提示 |
| `WAREHOUSE_WECHAT_APPID` / `WAREHOUSE_WECHAT_APP_SECRET` | 小程序需要走真实微信登录（`code2Session`）时才必须填；仅做本地联调可以留空，配合 `WAREHOUSE_ALLOW_DEMO_LOGIN=true` 使用演示登录 |
| `VITE_DEV_API_TARGET` | Web前端和后端不在同一台机器/端口不是 8000 时需要改 |
| `MINIPROGRAM_APPID` | 换成自己的小程序 AppID 时修改 |
| `MINIPROGRAM_BASE_URL` / `MINIPROGRAM_WS_URL` | 微信开发者工具模拟器 + 本机后端：保持 `127.0.0.1` 即可；小程序跑在**真机手机**上时，必须改成电脑的局域网 IP（手机和电脑需在同一 Wi-Fi 下） |

其余变量（`WAREHOUSE_DB_PATH`、`WAREHOUSE_SYNC_INTERVAL_SEC` 等）保持默认即可直接运行。

### 1. 启动后端 API 服务

Windows：

```powershell
powershell -ExecutionPolicy Bypass -File deploy/run_server_on_windows.ps1
```

Linux/macOS：

```bash
bash deploy/run_backend.sh
```

两个脚本都会自动读取根目录 `.env`、初始化 SQLite、并在 `http://0.0.0.0:8000` 启动服务。健康检查：

```bash
curl http://127.0.0.1:8000/api/health
```

### 2. 启动 Web 前端

```bash
cd web-frontend
npm install
npm run dev
```

Vite 会读取根目录 `.env`（已通过 `envDir` 配置指向仓库根目录），默认在 `http://localhost:5173` 打开，`/api` 会被代理到 `VITE_DEV_API_TARGET`。

### 3. 运行微信小程序

1. 修改 `.env` 中 `MINIPROGRAM_*` 相关配置后，执行同步脚本把配置写入小程序源码：
   ```bash
   node scripts/sync-miniprogram-config.js
   ```
2. 用微信开发者工具打开 `wechat-miniprogram/` 目录
3. 首次用 `http://` 明文联调需要在 详情 → 本地设置 中勾选"不校验合法域名..."
4. 修改 `.env` 后需要重复第 1 步重新同步，并在开发者工具里重新编译才能生效

## 重要提醒

- 本仓库的Python/C++源码在Windows环境下编写，**未经编译/运行验证**，需要开发者在Ubuntu主机/开发板上完成交叉编译与真机测试。
- `backend/env_service/sht30_driver.py` 中的I2C测量命令字节为占位值，**必须**对照Sensirion SHT30官方datasheet核实后修改，详见该文件内的TODO注释。
- 硬件相关的关键事实（I2C总线分配、GPIO脚位等）见 [docs/hardware-notes.md](docs/hardware-notes.md)，避免后续任务重复踩坑。