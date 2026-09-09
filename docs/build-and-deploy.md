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
`/data/warehousekeeper` 数据目录、初始化**主库和工作库**，并安装摄像头、
环境监测、API、Qt、旧 NCNN（`ai-service-cpp`）和 `inference-bridge`。
Python 备用 `ai-service` 保持禁用。旧 NCNN 只打开
`/data/warehousekeeper/inference-worker.db`，由桥接服务写回主库。
若任一已启用服务未成功进入 active 状态，脚本会打印最近日志并失败退出。

**不要**用旧稳定包整目录覆盖后再跑旧安装脚本。正确顺序：

1. 备份 `/opt/warehousekeeper` 和 `/data/warehousekeeper`。
2. 部署当前仓库的新 Python、Qt 和安装脚本。
3. 从旧稳定包只拿回 `bin/warehouse-ai-service`、两组 `models` 和必需运行库。
4. 不要用旧包里的 Python、Qt、systemd 和安装脚本覆盖新版本。
5. 初始化工作库并执行**新的** `deploy/install_on_device.sh`。

板上也可执行 `sh deploy/cutover_inference_bridge.sh /path/to/old-stable`。

Qt 前端自启动状态与日志：

```bash
systemctl status qt-frontend --no-pager
journalctl -u qt-frontend -n 80 --no-pager
```

### 板载 LED 门状态与自动盘点

“实时识别”页的按钮通过共享 SQLite 提交开关门请求。`camera-service` 独占
板载 LED 和摄像头：`user-led` 亮表示门开；关门后熄灯、拍摄单帧并交给 AI。
板载实体 `USER-KEY` 也接入同一状态机：第一次按下开门亮灯，第二次按下
关门熄灯并触发拍照；处理中按键会被忽略。真机默认通过稳定节点
`/dev/input/by-path/platform-gpio_keys@0-event` 读取键码 `114`。
首次成功识别只建立库存基线，后续关门结果与上一次成功盘点比较并生成
`IN/OUT` 流水。板载 LED 路径可在
`backend/camera_service/config/camera_service.yaml` 的
`door_led_brightness_path` 中修改。

不要重新编译旧 NCNN。关门拍照后由 `inference-bridge` 比较库存并生成
`IN/OUT`；旧 `warehouse-ai-service` 只负责检测框、品类、置信度和新鲜度。
每 5 秒预览只覆盖 `latest.jpg`，不入队、不推理、不改库存。

启用旧 NCNN 前，在开发板核对二进制架构并设置执行权限：

```bash
file bin/warehouse-ai-service  # 应显示 LoongArch ELF
chmod 755 bin/warehouse-ai-service
```

## 4. systemd常用操作

```bash
systemctl status camera-service
systemctl status env-service
systemctl status ai-service-cpp
systemctl status inference-bridge
systemctl restart camera-service
journalctl -u camera-service -f     # 实时查看日志
journalctl -u inference-bridge -f
journalctl -u ai-service-cpp -f
```

## 5. 数据库文件位置

Qt、camera_service、env_service、api_service 和 inference-bridge 共用主库
`/data/warehousekeeper/warehousekeeper.db`。旧 NCNN 只能打开工作库
`/data/warehousekeeper/inference-worker.db`。WAL 模式下各自会产生
`.db-wal` / `.db-shm`，属正常现象。

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
