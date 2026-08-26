#!/bin/sh
# 在ATK-DL2K0300B开发板上执行的安装脚本。
# 前提：项目源码已通过scp/git等方式拷贝到开发板。本脚本会自动识别仓库根目录。
#
# 用法（在开发板上，以root执行）：
#   cd /opt/warehousekeeper && sh deploy/install_on_device.sh

set -e

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
INSTALL_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
DATA_ROOT=/data/warehousekeeper

install_python_dependencies() {
    requirements_without_yaml=$(mktemp)
    trap 'rm -f "$requirements_without_yaml"' EXIT

    # LoongArch/Python 3.12 通常没有 PyYAML 预编译 wheel。若 pip 的 PEP 517
    # 隔离构建环境损坏，直接安装 requirements 会在这里失败；其余依赖均为纯 Python。
    grep -v '^PyYAML' "$INSTALL_ROOT/backend/requirements.txt" > "$requirements_without_yaml"

    if ! python3 -m pip --version >/dev/null 2>&1; then
        echo "==> 修复 Python pip..."
        python3 -m ensurepip --upgrade
    fi

    python3 -m pip install --prefer-binary -r "$requirements_without_yaml"

    if python3 -c 'import yaml' >/dev/null 2>&1; then
        return
    fi

    echo "==> 安装 PyYAML（优先使用系统包）..."
    if command -v apt-get >/dev/null 2>&1; then
        apt-get update
        apt-get install -y python3-yaml
    fi

    if ! python3 -c 'import yaml' >/dev/null 2>&1; then
        echo "==> 系统包不可用，使用当前 Python 构建 PyYAML..."
        python3 -m pip install --no-build-isolation --no-deps 'PyYAML>=6,<7'
    fi

    python3 -c 'import yaml; print("PyYAML:", yaml.__version__)'
}

install_unit() {
    unit_name=$1
    sed "s|__WAREHOUSE_ROOT__|$INSTALL_ROOT|g" \
        "$INSTALL_ROOT/deploy/systemd/$unit_name" \
        > "/etc/systemd/system/$unit_name"
}

echo "==> 项目目录: $INSTALL_ROOT"
echo "==> 检查Python依赖..."
install_python_dependencies

echo "==> 创建数据目录..."
mkdir -p "$DATA_ROOT/frames"

echo "==> 初始化SQLite数据库..."
cd "$INSTALL_ROOT"
python3 -m backend.common.init_db --db-path "$DATA_ROOT/warehousekeeper.db"

echo "==> 安装systemd服务单元..."
install_unit camera-service.service
install_unit env-service.service
install_unit api-service.service
AI_SERVICE_NAME=""
if [ -x "$INSTALL_ROOT/bin/warehouse-ai-service" ]; then
    for model_file in \
        "$INSTALL_ROOT/models/best_ncnn_model/model.ncnn.param" \
        "$INSTALL_ROOT/models/best_ncnn_model/model.ncnn.bin" \
        "$INSTALL_ROOT/models/shufflenet_v2_freshness_ncnn_model/model.ncnn.param" \
        "$INSTALL_ROOT/models/shufflenet_v2_freshness_ncnn_model/model.ncnn.bin"; do
        if [ ! -f "$model_file" ]; then
            echo "==> 缺少 AI 模型文件: $model_file" >&2
            exit 1
        fi
    done
    install_unit ai-service-cpp.service
    AI_SERVICE_NAME=ai-service-cpp
else
    echo "==> 未发现 bin/warehouse-ai-service，跳过 C++ AI 推理服务。"
fi
systemctl daemon-reload

echo "==> 启用并启动服务..."
systemctl enable --now camera-service
systemctl enable --now env-service
systemctl enable --now api-service
if [ -n "$AI_SERVICE_NAME" ]; then
    # Python AI 服务与 NCNN C++ 服务不能同时消费同一批 pending_frames。
    systemctl disable --now ai-service 2>/dev/null || true
    systemctl enable --now "$AI_SERVICE_NAME"
fi

sleep 2
for service_name in camera-service env-service api-service $AI_SERVICE_NAME; do
    if ! systemctl is-active --quiet "$service_name"; then
        echo "==> $service_name 启动失败，最近日志如下：" >&2
        journalctl -u "$service_name" -n 40 --no-pager >&2 || true
        exit 1
    fi
done

echo "==> 完成。用以下命令检查状态："
echo "    systemctl status camera-service"
echo "    systemctl status env-service"
echo "    systemctl status api-service"
if [ -n "$AI_SERVICE_NAME" ]; then
    echo "    systemctl status $AI_SERVICE_NAME"
fi
echo "    journalctl -u camera-service -f"
echo "    journalctl -u env-service -f"
echo "    journalctl -u api-service -f"
