# 交叉编译 / 部署 / systemd 操作速查

前提：已按 [qt5-setup-guide.md](qt5-setup-guide.md) 完成Qt5交叉编译环境搭建。
以下命令均在开发者的Ubuntu主机/开发板上执行。

## 1. Qt前端交叉编译

```bash
cd qt-frontend
source /opt/atk-dl2k0300-toolchain/environment-setup
qmake WarehouseKeeper.pro
make -j16
file WarehouseKeeper   # 确认输出为LoongArch架构ELF
```

或在Qt Creator里选择`atk-dl2K0300` Kit，Ctrl+B构建。

## 2. 部署到开发板

假定项目源码整体拷贝到开发板 `/opt/warehousekeeper`（含`qt-frontend/`
编译产物、`backend/`源码、`deploy/`脚本）：

```bash
# 在Ubuntu主机上，先scp整个项目（或只scp编译产物+源码，视网络情况）
scp -r WarehouseSystem root@<板子IP>:/opt/warehousekeeper

# 或只更新Qt前端可执行文件
scp qt-frontend/WarehouseKeeper root@<板子IP>:/opt/warehousekeeper/qt-frontend/
```

Qt前端运行时依赖`qt-frontend/config/frontend.ini`（相对工作目录路径），
确保部署时该文件与可执行文件保持相对位置一致，或在启动脚本里`cd`到
`qt-frontend/`目录后再执行。

Qt 前端的开发板运行环境集中定义在`deploy/qt-frontend-env.sh`，其中包含：

```bash
export QT_QPA_PLATFORM=linuxfb:fb=/dev/fb0
```

板端安装脚本会把该环境文件复制到`/etc/profile.d/warehousekeeper-qt.sh`，并安装
`qt-frontend.service`。服务启动时会退出占用 framebuffer 的出厂`systemui/weston`，
然后全屏启动`WarehouseKeeper`；应用首先显示欢迎页，轻触任意位置进入业务界面。

## 3. Python后端安装与systemd部署

在开发板上执行：

```bash
cd /opt/warehousekeeper
sh deploy/install_on_device.sh
```

该脚本会自动识别当前仓库目录；依次安装 Python 依赖、创建
`/data/warehousekeeper` 数据目录、初始化 SQLite 数据库，并安装和启动
摄像头、环境监测、API 和 Qt 前端 systemd 服务。若项目同时包含已授权执行的
`bin/warehouse-ai-service` 及两组 NCNN 模型，脚本还会自动启动
`ai-service-cpp`。若任一已启用服务未成功进入 active 状态，脚本会打印最近
日志并失败退出。详见 `deploy/install_on_device.sh` 源码。

Qt 前端自启动状态与日志：

```bash
systemctl status qt-frontend --no-pager
journalctl -u qt-frontend -n 80 --no-pager
```

启用 C++ AI 服务前，在开发板核对二进制架构并设置执行权限：

```bash
file bin/warehouse-ai-service  # 应显示 LoongArch ELF
chmod 755 bin/warehouse-ai-service
```

## 4. systemd常用操作

```bash
systemctl status camera-service
systemctl status env-service
systemctl restart camera-service
journalctl -u camera-service -f     # 实时查看日志
journalctl -u env-service -f
```

## 5. 数据库文件位置

三个进程（Qt前端、camera_service、env_service）共用同一个SQLite文件：
`/data/warehousekeeper/warehousekeeper.db`（路径在各自配置文件中约定，
需保持一致）。WAL模式下会产生`.db-wal`/`.db-shm`辅助文件，属正常现象。

手动查看数据：

```bash
sqlite3 /data/warehousekeeper/warehousekeeper.db "SELECT * FROM env_log ORDER BY id DESC LIMIT 5;"
```

## 6. 图片保留与清理

`camera-service`启动前会先清理超过7天或超过数量上限的历史变化帧。运行中
每小时只清理`processed`/`discarded`图片，不删除AI可能正在读取的`pending`
图片；待处理队列达到1000条后暂停新增变化帧，队列下降后自动恢复。

策略可在`backend/camera_service/config/camera_service.yaml`中调整。部署更新后
执行：

```bash
systemctl daemon-reload
systemctl restart camera-service
journalctl -u camera-service -n 100 --no-pager
```
