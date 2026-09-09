#!/bin/sh

# 复现已在 ATK-DL2K0300B 上验证过的 NCNN 20260526 构建方式，
# 并使用该静态库交叉编译带门周期逻辑的 warehouse-ai-service。
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
TOOLCHAIN_ROOT=${WAREHOUSE_TOOLCHAIN_ROOT:-/opt/atk-dl2k0300-toolchain}
SYSROOT_DIR="$TOOLCHAIN_ROOT/loongarch64-buildroot-linux-gnu/sysroot"
NCNN_SOURCE_DIR=${WAREHOUSE_NCNN_SOURCE_DIR:-"$PROJECT_ROOT/.build/ncnn-20260526"}
NCNN_BUILD_DIR=${WAREHOUSE_NCNN_BUILD_DIR:-"$PROJECT_ROOT/.build/ncnn-stable-loongarch"}
NCNN_INSTALL_DIR=${WAREHOUSE_NCNN_INSTALL_DIR:-"$NCNN_BUILD_DIR/install"}
AI_BUILD_DIR=${WAREHOUSE_AI_BUILD_DIR:-"$PROJECT_ROOT/.build/cpp-ai-stable-loongarch"}
BUILD_JOBS=${WAREHOUSE_BUILD_JOBS:-4}
EXPECTED_NCNN_COMMIT=e54f7b1f88434e1d844ea0551b880a1cfb079ce1

if [ ! -f "$NCNN_SOURCE_DIR/CMakeLists.txt" ]; then
    echo "缺少 NCNN 20260526 源码: $NCNN_SOURCE_DIR" >&2
    echo "请先执行:" >&2
    echo "git clone --depth 1 --branch 20260526 https://github.com/Tencent/ncnn.git $NCNN_SOURCE_DIR" >&2
    exit 1
fi

if command -v git >/dev/null 2>&1 && [ -d "$NCNN_SOURCE_DIR/.git" ]; then
    actual_commit=$(git -C "$NCNN_SOURCE_DIR" rev-parse HEAD)
    if [ "$actual_commit" != "$EXPECTED_NCNN_COMMIT" ]; then
        echo "NCNN 提交不正确: $actual_commit" >&2
        echo "期望 20260526: $EXPECTED_NCNN_COMMIT" >&2
        exit 1
    fi
fi

cmake -S "$NCNN_SOURCE_DIR" -B "$NCNN_BUILD_DIR" \
    -DCMAKE_SYSTEM_NAME=Linux \
    -DCMAKE_SYSTEM_PROCESSOR=loongarch64 \
    -DCMAKE_C_COMPILER="$TOOLCHAIN_ROOT/bin/loongarch64-linux-gnu-gcc" \
    -DCMAKE_CXX_COMPILER="$TOOLCHAIN_ROOT/bin/loongarch64-linux-gnu-g++" \
    -DCMAKE_SYSROOT="$SYSROOT_DIR" \
    -DCMAKE_FIND_ROOT_PATH="$SYSROOT_DIR" \
    -DCMAKE_FIND_ROOT_PATH_MODE_PROGRAM=NEVER \
    -DCMAKE_FIND_ROOT_PATH_MODE_LIBRARY=ONLY \
    -DCMAKE_FIND_ROOT_PATH_MODE_INCLUDE=ONLY \
    -DCMAKE_FIND_ROOT_PATH_MODE_PACKAGE=ONLY \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="$NCNN_INSTALL_DIR" \
    -DNCNN_SHARED_LIB=OFF \
    -DNCNN_ENABLE_LTO=OFF \
    -DNCNN_OPENMP=OFF \
    -DNCNN_SIMPLEOMP=OFF \
    -DNCNN_SIMPLEOCV=OFF \
    -DNCNN_THREADS=ON \
    -DNCNN_RUNTIME_CPU=OFF \
    -DNCNN_LSX=ON \
    -DNCNN_LASX=OFF \
    -DNCNN_BF16=ON \
    -DNCNN_INT8=ON \
    -DNCNN_VULKAN=OFF \
    -DNCNN_PIXEL=ON \
    -DNCNN_PIXEL_ROTATE=ON \
    -DNCNN_PIXEL_AFFINE=ON \
    -DNCNN_PIXEL_DRAWING=OFF \
    -DNCNN_C_API=OFF \
    -DNCNN_BUILD_TESTS=OFF \
    -DNCNN_BUILD_TOOLS=OFF \
    -DNCNN_BUILD_EXAMPLES=OFF \
    -DNCNN_BUILD_BENCHMARK=OFF \
    -DNCNN_PYTHON=OFF \
    -DNCNN_INSTALL_SDK=ON

cmake --build "$NCNN_BUILD_DIR" -j"$BUILD_JOBS"
cmake --install "$NCNN_BUILD_DIR"

cmake -S "$PROJECT_ROOT/cpp-ai-service" -B "$AI_BUILD_DIR" \
    -DCMAKE_TOOLCHAIN_FILE="$PROJECT_ROOT/cpp-ai-service/toolchains/loongarch64-linux-gnu.cmake" \
    -DCMAKE_BUILD_TYPE=Release \
    -DWAREHOUSE_ENABLE_IPO=OFF \
    -Dncnn_DIR="$NCNN_INSTALL_DIR/lib/cmake/ncnn" \
    -DOpenCV_DIR="$SYSROOT_DIR/usr/lib/cmake/opencv4"

cmake --build "$AI_BUILD_DIR" -j"$BUILD_JOBS"

echo "构建完成: $AI_BUILD_DIR/warehouse-ai-service"
file "$AI_BUILD_DIR/warehouse-ai-service"
sha256sum "$AI_BUILD_DIR/warehouse-ai-service"
