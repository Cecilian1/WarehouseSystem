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

## 3. Python后端安装与systemd部署

在开发板上执行：

```bash
cd /opt/warehousekeeper
sh deploy/install_on_device.sh
```

该脚本会依次完成：安装Python依赖（`backend/requirements.txt`）、创建
`/data/warehousekeeper`数据目录、初始化SQLite数据库、安装并启动两个
systemd服务。详见 `deploy/install_on_device.sh` 源码。

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
