#!/bin/sh
# 用 flock 保证旧 NCNN 只有一个实例，无论 systemd 还是手工启动。
# 该进程只能打开工作库，绝不能打开主库。

set -e

LOCK_FILE=${WAREHOUSE_AI_LOCK:-/data/warehousekeeper/warehouse-ai-service.lock}
mkdir -p "$(dirname "$LOCK_FILE")"
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
    echo "warehouse-ai-service 已在运行（$LOCK_FILE）" >&2
    exit 1
fi

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
INSTALL_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
exec "$INSTALL_ROOT/bin/warehouse-ai-service" "$@"
