# 芯鲜管家 — WarehouseSystem

面向家庭冰箱场景的果蔬仓储管理系统，运行于龙芯2K0300（LS2K0300B）+ 正点原子ATK-DL2K0300B开发板。

## 本次任务范围

本仓库当前只落地完整实现方案（见项目根目录外的
`芯鲜管家_实现方案_ATK-DL2K0300B.docx`）中的三个模块：

1. **6.1 本地终端屏幕**（LCD触摸屏 + Qt人机交互）—— `qt-frontend/`
2. **设备采集服务**（摄像头）—— `backend/camera_service/`
3. **环境监测服务**（温湿度传感器）—— `backend/env_service/`

**不包含**：AI推理（YOLOv11n/MobileNetV3新鲜度分类）、云同步、Web管理后台、移动端。这些是后续任务的范围。本次交付的表结构（`pending_frames`/`inventory_log`等）已为后续AI服务模块预留好对接点，约定见 [docs/interfaces.md](docs/interfaces.md)。

## 目录结构

```
WarehouseSystem/
├── docs/                # 环境搭建、部署、验证、硬件事实、接口契约文档
├── qt-frontend/         # Qt Widgets本地终端UI（qmake工程）
├── backend/
│   ├── common/          # 数据库连接/schema/配置读取等共享代码
│   ├── camera_service/  # 摄像头采集+帧间差分触发服务
│   └── env_service/     # 温湿度采集+设备异常检测服务
└── deploy/               # systemd单元、开发板安装脚本
```

## 快速开始（开发者在自己的Ubuntu主机/开发板上执行）

1. 按 [docs/qt5-setup-guide.md](docs/qt5-setup-guide.md) 搭建Qt5交叉编译环境
2. 按 [docs/build-and-deploy.md](docs/build-and-deploy.md) 交叉编译Qt前端、部署Python后端
3. 按 [docs/verification-checklist.md](docs/verification-checklist.md) 逐项验证

## 重要提醒

- 本仓库的Python/C++源码在Windows环境下编写，**未经编译/运行验证**，需要开发者在Ubuntu主机/开发板上完成交叉编译与真机测试。
- `backend/env_service/sht30_driver.py` 中的I2C测量命令字节为占位值，**必须**对照Sensirion SHT30官方datasheet核实后修改，详见该文件内的TODO注释。
- 硬件相关的关键事实（I2C总线分配、GPIO脚位等）见 [docs/hardware-notes.md](docs/hardware-notes.md)，避免后续任务重复踩坑。
