#!/bin/sh
# Qt 前端在开发板上的统一运行环境。安装脚本会将本文件同步到
# /etc/profile.d/warehousekeeper-qt.sh，systemd 启动脚本也会直接加载它。
export QT_QPA_PLATFORM=linuxfb:fb=/dev/fb0
export QT_IM_MODULE=qtvirtualkeyboard
export QT_VIRTUALKEYBOARD_LOCALE=zh_CN
