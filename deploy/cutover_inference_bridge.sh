#!/bin/sh
# 板上切换到“旧稳定 NCNN + inference-bridge”。
# 必须先部署当前仓库的新 Python / Qt / 安装脚本，再执行本脚本。
# 不要用旧稳定包覆盖新代码后再跑旧安装脚本。

set -e

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
INSTALL_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
DATA_ROOT=/data/warehousekeeper
BACKUP_ROOT=/data/warehousekeeper-backup-$(date +%Y%m%d-%H%M%S)
OLD_STABLE_ROOT=${1:-}

stop_warehouse_services() {
    for service_name in \
        qt-frontend \
        inference-bridge \
        ai-service-cpp \
        ai-service \
        camera-service \
        env-service \
        api-service
    do
        systemctl stop "$service_name" 2>/dev/null || true
        systemctl disable "$service_name" 2>/dev/null || true
    done
}

echo "==> 1. 备份 /opt/warehousekeeper 和 /data/warehousekeeper"
stop_warehouse_services
mkdir -p "$BACKUP_ROOT"
if [ -d /opt/warehousekeeper ]; then
    cp -a /opt/warehousekeeper "$BACKUP_ROOT/opt-warehousekeeper"
fi
if [ -d "$DATA_ROOT" ]; then
    cp -a "$DATA_ROOT" "$BACKUP_ROOT/data-warehousekeeper"
fi
echo "    备份目录: $BACKUP_ROOT"

if [ ! -f "$INSTALL_ROOT/backend/inference_bridge/main.py" ]; then
    echo "==> 当前目录缺少新的 inference-bridge，请先部署当前仓库的新 Python/Qt/安装脚本。" >&2
    exit 1
fi
if [ ! -f "$INSTALL_ROOT/deploy/install_on_device.sh" ]; then
    echo "==> 缺少新的安装脚本。" >&2
    exit 1
fi

if [ -n "$OLD_STABLE_ROOT" ]; then
    echo "==> 3. 只从旧稳定包回填二进制、模型和运行库: $OLD_STABLE_ROOT"
    if [ ! -x "$OLD_STABLE_ROOT/bin/warehouse-ai-service" ]; then
        echo "==> 旧稳定包缺少可执行的 bin/warehouse-ai-service" >&2
        exit 1
    fi
    mkdir -p "$INSTALL_ROOT/bin" "$INSTALL_ROOT/models"
    cp -a "$OLD_STABLE_ROOT/bin/warehouse-ai-service" "$INSTALL_ROOT/bin/warehouse-ai-service"
    chmod 755 "$INSTALL_ROOT/bin/warehouse-ai-service"
    if [ -d "$OLD_STABLE_ROOT/models/best_ncnn_model" ]; then
        rm -rf "$INSTALL_ROOT/models/best_ncnn_model"
        cp -a "$OLD_STABLE_ROOT/models/best_ncnn_model" "$INSTALL_ROOT/models/best_ncnn_model"
    fi
    if [ -d "$OLD_STABLE_ROOT/models/shufflenet_v2_freshness_ncnn_model" ]; then
        rm -rf "$INSTALL_ROOT/models/shufflenet_v2_freshness_ncnn_model"
        cp -a "$OLD_STABLE_ROOT/models/shufflenet_v2_freshness_ncnn_model" \
            "$INSTALL_ROOT/models/shufflenet_v2_freshness_ncnn_model"
    fi
    if [ -d "$OLD_STABLE_ROOT/lib" ]; then
        mkdir -p "$INSTALL_ROOT/lib"
        cp -a "$OLD_STABLE_ROOT/lib/." "$INSTALL_ROOT/lib/"
    fi
    echo "    已跳过旧包中的 Python、Qt、systemd 和安装脚本。"
else
    echo "==> 未提供旧稳定包路径。请确认 $INSTALL_ROOT/bin/warehouse-ai-service 已是旧稳定程序。"
    echo "    用法: sh deploy/cutover_inference_bridge.sh /path/to/old-stable-warehousekeeper"
fi

echo "==> 5. 初始化工作库并执行新的安装脚本"
mkdir -p "$DATA_ROOT/frames"
cd "$INSTALL_ROOT"
python3 -m backend.common.init_db --db-path "$DATA_ROOT/warehousekeeper.db"
python3 -m backend.common.init_db --db-path "$DATA_ROOT/inference-worker.db"
sh "$INSTALL_ROOT/deploy/install_on_device.sh"
