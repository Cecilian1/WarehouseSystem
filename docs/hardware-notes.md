# 硬件事实摘录

本文档摘录本次任务用到的、易被后续任务重复踩坑的硬件事实，来源均为正点原子
官方PDF手册（用户手册/文档教程目录）。

## LCD与触摸

- LCD：7寸IPS RGB并口屏，1024×600（另有4.3寸800×480屏可选），通过LS2K0300B
  的RGB并口接入。**该芯片无GPU、无3D图形加速能力，仅集成LCD显示时序控制器**——
  这是本项目Qt前端选择Widgets而非QML的关键依据（见 `qt-frontend/` 设计说明）。
- 触摸：GT911电容触控芯片，**I2C2总线，地址0x14**，中断/复位通过GPIO
  （irq-gpios=`<&gpio 74>`，reset-gpios=`<&gpio 75>`），设备树节点位于
  `arch/loongarch/boot/dts/loongson/ls2k300_alientek.dts` 的 `&i2c2` 节点，
  `compatible = "goodix,gt911"`。

## I2C总线分配（重要：避免误判总线冲突）

LS2K0300B共有 **I2C0~I2C3** 四条总线，内核已启用
`CONFIG_I2C_CHARDEV`/`CONFIG_I2C_GPIO`/`CONFIG_I2C_LSFS`
（位于`arch/loongarch/configs/loongson_2k300_alientek_defconfig`）。

| 总线 | 占用设备 | 地址 |
|---|---|---|
| I2C2 | GT911触摸屏 | 0x14 |
| I2C3 | ES8388音频codec | 约0x10（需开发者对照ES8388 datasheet核实） |
| I2C0/I2C1 | 未被板载外设占用 | — |

**此前项目实现方案文档（docx）曾担心"触摸屏与温湿度传感器共享I2C总线导致
地址冲突"，经核实该担心不成立**：触摸屏在I2C2，音频codec在I2C3，二者本就
不是同一条总线；本次env_service选择复用I2C3接入SHT30，与ES8388地址不同
（SHT30通常0x44/0x45），理论不冲突，但仍需上板后用`i2cdetect -y 3`实测确认。

用户态调试I2C的标准工具是`i2c-tools`（`i2cdetect`/`i2cget`/`i2cset`/`i2cdump`），
例如探测I2C3总线上的从机地址：

```bash
i2cdetect -y 3
```

## GPIO

- 板载LED（DS0/DS1）走标准Linux LED子系统，`/sys/class/leds/{sys-led,user-led}`，
  写`brightness`文件控制亮灭（0=灭，非0=亮，部分为PWM调光）。这与外接的冰箱内
  补光LED（走GPIO而非LED子系统）是两回事，不要混淆。
- 外接GPIO走标准sysfs接口（`arch/.../第17章`记载）：
  ```bash
  echo <N> > /sys/class/gpio/export
  echo out > /sys/class/gpio/gpio<N>/direction
  echo 1 > /sys/class/gpio/gpio<N>/value   # 输出高电平
  ```
- JP7扩展排针提供14个GPIO脚位（2×7P），可用于外接自定义传感器/执行器。
  本项目camera_service的补光LED默认走该sysfs接口，具体GPIO编号需开发者
  按JP7实测选定，写入`backend/camera_service/config/camera_service.yaml`
  的`led_gpio`项。

## 摄像头

- USB免驱UVC协议摄像头，Linux下走V4L2框架，设备节点形如`/dev/video-camera0`
  （udev别名，实际名称需上板后用`ls /dev/video*`核实，可能因固件版本不同而变化）。
- 官方Qt示例"06_qcamera"演示了`QCamera`+`QCameraImageCapture`+`QVideoWidget`
  的标准用法（Qt5.15旧版QtMultimedia API），本项目未直接照搬该UI示例（本项目
  camera_service是Python后台daemon而非Qt前端直接控制摄像头），但采集参数
  （640×480分辨率）与其保持一致。

## Qt5交叉工具链

- 安装包`atk-dl2k0300-toolchain-qt5-loongarch64-buildroot-linux-gnu-x86_64-20250328-v1.1.run`
  位于资料盘"06、开发工具.zip"内，约449MB，默认装到`/opt/atk-dl2k0300-toolchain`。
- 详细搭建步骤见 [qt5-setup-guide.md](qt5-setup-guide.md)。
