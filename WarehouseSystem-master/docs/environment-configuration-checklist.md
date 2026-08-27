# ATK-DL2K0300B 开发环境总配置清单

本清单汇总正点原子 ATK-DL2K0300B 官方手册与本项目文档，目标是完成
`WarehouseSystem` 的交叉编译、SSH 部署和真机验证。未列为“必需”的手册内容
不应为了“全部配置”而盲目修改开发板。

## 1. 当前已确认

- [x] Windows 已安装 VMware Workstation（25.0.1）
- [x] 官方 Ubuntu 24.04 虚拟机已解压到 F 盘（约 29.3 GB）
- [x] 虚拟机配置文件 `ATK-DL2K0300.vmx` 和虚拟磁盘文件完整存在
- [x] Windows 可通过手机热点 SSH 登录开发板
- [x] 开发板 SSH 服务已启用，账号 `root`
- [x] 开发板当前项目目录 `/opt/warehousekeeper` 存在
- [x] 开发板 `camera-service`、`env-service` 处于 active

## 2. Windows 与 VMware（必需）

- [ ] 将虚拟机内存从 16 GB 调整为 8 GB，虚拟 CPU 从 16 调整为 8
- [ ] 网络适配器使用 NAT，保证 Ubuntu 可联网并可访问开发板
- [ ] USB 控制器保持 USB 3.x
- [ ] 启动虚拟机时选择“我已复制该虚拟机”
- [ ] 使用 `alientek / 123` 登录 Ubuntu
- [ ] 不升级 Ubuntu 大版本
- [ ] F 盘继续预留编译空间（官方建议至少 100 GB，当前剩余约 86 GB）

## 3. Ubuntu 基础环境（必需）

- [ ] Ubuntu 版本确认为 24.04
- [ ] Ubuntu 能访问互联网
- [ ] Ubuntu 能访问开发板当前 IP
- [ ] 安装基础依赖：

```bash
sudo apt-get update
sudo apt-get install -y gcc g++ lib32stdc++6 libglu1-mesa-dev \
  gstreamer1.0-plugins-base gstreamer1.0-plugins-bad gstreamer1.0-libav \
  gstreamer1.0-plugins-good gstreamer1.0-plugins-ugly \
  gstreamer1.0-pulseaudio cmake openssh-client net-tools \
  libxcb-xinerama0 libxcb-cursor0 libxcb-cursor-dev
```

## 4. LoongArch 交叉编译工具链（必需）

- [ ] `/opt/atk-dl2k0300-toolchain/environment-setup` 存在
- [ ] 载入工具链环境：

```bash
source /opt/atk-dl2k0300-toolchain/environment-setup
```

- [ ] `$CC`、`$CXX` 非空
- [ ] `loongarch64-loongson-linux-gnu-gcc --version` 显示 GCC 13.3.0
- [ ] 编译一个简单 C/C++ 程序并用 `file` 确认为 LoongArch

## 5. Qt 5.15.2 与 Qt Creator（项目必需）

官方 V1.1 虚拟机镜像不再预装 Qt，因此必须单独安装。

- [ ] 安装 Qt Creator 和 Qt 5.15.2 Desktop GCC 64-bit
- [ ] Qt Creator 中添加 LoongArch C/C++ 编译器
- [ ] 添加交叉工具链的 `qmake`
- [ ] 添加开发板 Remote Linux Device（SSH）
- [ ] 组合 `atk-dl2K0300` Kit
- [ ] Hello World 交叉编译、部署和运行成功
- [ ] `WarehouseKeeper.pro` 交叉编译成功

## 6. 文件传输与部署（必需）

- [ ] Ubuntu 中可执行 `ssh root@<开发板IP>`
- [ ] Ubuntu 中可通过 `scp` 向开发板传输文件
- [ ] 项目部署到 `/opt/warehousekeeper`
- [ ] Qt 程序保持 `qt-frontend/config/frontend.ini` 的相对路径
- [ ] 数据库位于 `/data/warehousekeeper/warehousekeeper.db`
- [ ] `camera-service`、`env-service` 开机自启并运行

## 7. 真机硬件验证（接好对应硬件后必需）

- [ ] LCD 与触摸导航正常
- [ ] `ls /dev/video*` 找到实际摄像头节点并更新配置
- [ ] 摄像头能够拍照并写入 `pending_frames`
- [ ] 确认补光 LED 的实际 GPIO 编号
- [ ] 使用 `i2cdetect -y 3` 验证 SHT30 地址
- [ ] 对照 SHT30 数据手册核实测量命令字节
- [ ] 温湿度数据持续写入 `env_log`
- [ ] Qt、摄像头、环境服务同时运行 30 分钟无数据库锁错误

## 8. 当前不需要配置

以下内容只在开发内核、烧写固件或采用特定网络启动方案时需要：

- TFTP
- NFS
- U-Boot 环境变量
- 固件烧写和系统更新
- 更换启动 LOGO
- Buildroot 源码定制
- 有线网口静态 IP（当前手机热点 + Wi-Fi SSH 已可用）

除非后续任务明确需要，不修改这些配置，以避免破坏当前可启动、可 SSH 的开发板系统。
