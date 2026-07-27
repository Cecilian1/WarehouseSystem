# 开发板数据库同步到 Windows 本机

## 当前数据链路

```text
开发板 SQLite
  /data/warehousekeeper/warehousekeeper.db
          │
          │ Windows 每 5 秒拉取增量
          ▼
Windows 本机 SQLite
  data/warehousekeeper-server.db
          │
          ├── REST API: http://127.0.0.1:8000/api
          └── WebSocket: ws://127.0.0.1:8000/ws/notify
                          │
                          ▼
                       Web 前端
```

开发板和 Windows 均连接当前热点：

- 开发板：`10.141.97.252`
- Windows：`10.141.97.161`

本机主动连接开发板，因此不需要开放 Windows 防火墙入站端口。

## 同步范围

以下 SQLite 表会同步：

- `produce_info`
- `inventory_log`
- `stock_summary`
- `alert_record`
- `device_status`
- `env_log`
- `pending_frames`

`inventory_log`、`alert_record`、`env_log`、`pending_frames` 使用自增 ID
游标做增量同步；另外三张状态表每轮上传当前快照。服务端按主键执行幂等
写入，相同数据重复传输不会产生重复记录。

数据库中的 `image_path` 字段会同步，但图片文件本身不会长期复制到 Windows。
Web 通过本机 `/api/frames/latest/image` 获取最新画面；本机没有对应文件时，
该接口会代理读取开发板 `/api/frames/{frame_id}/image`，并以 `no-store`
方式返回 JPEG。这样可以直接查看真实画面，同时避免本机重复保存大量帧文件。

## 启动本机服务器

在 PowerShell 中执行：

```powershell
cd "C:\Users\Lenovo\Desktop\新建文件夹 (2)\WarehouseSystem"
powershell -ExecutionPolicy Bypass -File .\deploy\run_server_on_windows.ps1
```

该脚本会：

1. 初始化 `data/warehousekeeper-server.db`；
2. 启动本机 FastAPI 服务（端口 8000）；
3. 每 5 秒从开发板读取新增数据；
4. 把数据写入本机 SQLite，供 Web 前端读取。

## 验证

浏览器或 PowerShell 可访问：

```text
http://127.0.0.1:8000/api/health
http://127.0.0.1:8000/api/sync/status
http://127.0.0.1:8000/api/dashboard
http://127.0.0.1:8000/api/frames/latest/image
```

Web 前端的 `.env.local` 已配置为访问本机服务：

```dotenv
VITE_USE_MOCK=false
VITE_API_BASE_URL=http://127.0.0.1:8000/api
VITE_WS_URL=ws://127.0.0.1:8000/ws/notify
```

## IP 变化

手机热点重新连接后，开发板 IP 可能变化。此时需要修改：

```powershell
$env:WAREHOUSE_BOARD_SOURCE_URL = "http://新的开发板IP:8000"
```

对应文件是 `deploy/run_server_on_windows.ps1`，修改后重新启动本机服务器。
