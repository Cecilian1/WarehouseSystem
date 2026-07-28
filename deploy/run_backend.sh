#!/bin/zsh
# 本地/服务端一键启动脚本：装依赖 -> 初始化SQLite -> 起 FastAPI 服务。
# 可在仓库任意目录下执行（脚本会自动切换到项目根目录）。

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${0}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

DB_PATH="$PROJECT_ROOT/data/warehousekeeper-server.db"

echo "Installing dependencies..."
python3 -m pip install -r backend/requirements.txt

echo "Initializing SQLite..."
python3 -m backend.common.init_db --db-path "$DB_PATH"

echo "Starting server..."
export WAREHOUSE_DB_PATH="$DB_PATH"
# 微信登录 (code2Session) 所需；不设置时除 /api/auth/wechat-login 外的接口仍可正常使用。
# 请通过 shell 环境变量或本地未入库的 .env 文件覆盖，不要把真实 AppSecret 写死在此脚本中。
export WAREHOUSE_WECHAT_APPID="${WAREHOUSE_WECHAT_APPID:-your-appid}"
export WAREHOUSE_WECHAT_APP_SECRET="${WAREHOUSE_WECHAT_APP_SECRET:-your-app-secret}"

python3 -m uvicorn backend.api_service.main:app --host 0.0.0.0 --port 8000 --reload
