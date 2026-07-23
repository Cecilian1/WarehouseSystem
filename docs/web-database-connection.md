# Web端连接开发板SQLite实施步骤

目标：不改变现有表结构，让Web端通过后端API读取开发板上的同一份
`/data/warehousekeeper/warehousekeeper.db`。

## 1. 开发板数据源

Qt前端、camera_service、env_service 已经共用同一个SQLite文件：

```text
/data/warehousekeeper/warehousekeeper.db
```

继续保持以下配置一致：

- `qt-frontend/config/frontend.ini` 的 `database/path`
- `backend/camera_service/config/camera_service.yaml` 的 `db_path`
- `backend/env_service/config/env_service.yaml` 的 `db_path`
- `api-service.service` 的 `WAREHOUSE_DB_PATH`

## 2. 启动API服务

开发板执行安装脚本后会自动安装并启动 `api-service`：

```bash
cd /opt/warehousekeeper
sh deploy/install_on_device.sh
systemctl status api-service
```

API默认监听：

```text
http://开发板IP:8000/api
```

健康检查：

```bash
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/dashboard
```

## 3. Web端切换真实接口

开发联调时在 `web-frontend/.env.local` 中使用：

```env
VITE_USE_MOCK=false
VITE_API_BASE_URL=/api
VITE_DEV_API_TARGET=http://开发板IP:8000
```

然后启动Web端：

```bash
cd web-frontend
npm run dev
```

Vite 会把 `/api/*` 代理到 `VITE_DEV_API_TARGET`，浏览器实际仍访问
`http://本机IP:5173`，避免开发阶段跨域问题。

## 4. 生产部署建议

如果Web静态资源部署在开发板上，建议用Nginx或同类服务：

- `/` 指向 `web-frontend/dist`
- `/api/` 反向代理到 `http://127.0.0.1:8000/api/`

如果Web部署在云端或PC上，`VITE_API_BASE_URL` 可直接设置为：

```env
VITE_USE_MOCK=false
VITE_API_BASE_URL=http://开发板IP:8000/api
```

正式公网访问时需要HTTPS和鉴权；比赛局域网演示阶段可以先使用HTTP。

## 5. 当前接口范围

已接入现有Web端需要的读取接口：

- `GET /api/dashboard`
- `GET /api/inventory`
- `GET /api/recognitions`
- `GET /api/environment`
- `GET /api/environment/latest`
- `GET /api/produce`
- `POST /api/produce`
- `PUT /api/produce/{id}`
- `GET /api/alerts`
- `GET /api/devices`
- `GET /api/history`
- `GET /api/analytics`
- `GET /api/frames/{frame_id}/image`

说明：Web端当前“新增/编辑/删除库存”和“确认预警”仍是前端占位交互；
需要真实写数据库时，再补 `POST/PUT/DELETE` 接口。
