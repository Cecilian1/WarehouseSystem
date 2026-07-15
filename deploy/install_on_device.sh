#!/bin/sh
# 在ATK-DL2K0300B开发板上执行的安装脚本。
# 前提：项目源码已通过scp/git等方式拷贝到 /opt/warehousekeeper（本脚本假定该路径）。
#
# 用法（在开发板上，以root执行）：
#   cd /opt/warehousekeeper && sh deploy/install_on_device.sh

set -e

INSTALL_ROOT=/opt/warehousekeeper
DATA_ROOT=/data/warehousekeeper

echo "==> 检查Python依赖..."
pip3 install -r "$INSTALL_ROOT/backend/requirements.txt"

echo "==> 创建数据目录..."
mkdir -p "$DATA_ROOT/frames"

echo "==> 初始化SQLite数据库..."
cd "$INSTALL_ROOT"
python3 -m backend.common.init_db --db-path "$DATA_ROOT/warehousekeeper.db"

echo "==> 安装systemd服务单元..."
cp "$INSTALL_ROOT/deploy/systemd/camera-service.service" /etc/systemd/system/
cp "$INSTALL_ROOT/deploy/systemd/env-service.service" /etc/systemd/system/
systemctl daemon-reload

echo "==> 启用并启动服务..."
systemctl enable --now camera-service
systemctl enable --now env-service

echo "==> 完成。用以下命令检查状态："
echo "    systemctl status camera-service"
echo "    systemctl status env-service"
echo "    journalctl -u camera-service -f"
echo "    journalctl -u env-service -f"
