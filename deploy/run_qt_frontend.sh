#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
FRONTEND_DIR="$PROJECT_ROOT/qt-frontend"

. "$SCRIPT_DIR/qt-frontend-env.sh"

if [ ! -e /dev/fb0 ]; then
    echo "未找到 /dev/fb0，无法启动 Qt 前端" >&2
    exit 1
fi

if [ ! -x "$FRONTEND_DIR/WarehouseKeeper" ]; then
    echo "Qt 前端不存在或不可执行: $FRONTEND_DIR/WarehouseKeeper" >&2
    exit 1
fi

# 出厂 systemui/weston 会占用 framebuffer。官方手册建议更换自定义 Qt 界面前
# 先退出这两个进程。稍等片刻，避免本服务与出厂启动脚本并行执行。
sleep 2
pkill systemui 2>/dev/null || true
pkill weston 2>/dev/null || true
sleep 1
pkill -9 systemui 2>/dev/null || true
pkill -9 weston 2>/dev/null || true
pkill WarehouseKeeper 2>/dev/null || true

cd "$FRONTEND_DIR"
exec ./WarehouseKeeper
