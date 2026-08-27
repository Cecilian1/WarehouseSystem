# 温湿度传感器子系统 (SHT3x)

## 1. 简介
本文件夹包含“芯鲜管家”项目中，用于实时采集冰箱内部温湿度数据的完整底层实现。
包含 SHT3x 的 C 语言驱动源码、交叉编译生成的可执行文件，以及供上层 Python 系统调用的数据接口。

## 2. 目录结构说明
sensor/
├── sht3x_code/          <-- 原始 C 语言驱动源码（Linux I2C）
│   ├── main.c           <-- 命令入口（读取温湿度、状态等）
│   ├── sht3x.c          <-- I2C 通信、CRC校验、温湿度计算核心逻辑
│   ├── sht3x.h          <-- 接口定义与宏
│   └── Makefile         <-- 交叉编译配置文件
├── sht31e               <-- 已编译好的可执行文件（LoongArch 架构）
└── sensor.py            <-- 上层 Python 接口（调用 C 程序并解析数据）

##3. 核心参数
传感器型号：Sensirion SHT3x

通信接口：Linux I2C (/dev/i2c-0，地址 0x44)

交叉编译工具链：/opt/atk-dl2k0300-toolchain/bin/loongarch64-linux-gnu-gcc

测量精度：中等精度

##4. 编译说明（如需重新编译）
由于本文件夹已包含编译好的二进制文件，通常只需直接使用。
如果需要从源码重新编译（例如修改了 Makefile 中的工具链路径），请按以下步骤操作：（在虚拟机中）

进入 sht3x_code/ 目录。

修改 Makefile 中的 CROSS_COMPILE 路径。

执行 make clean 清除旧产物。

执行 make 完成编译，即可在当前目录生成新的 sht31e 文件。

##5. 使用方法
  5.1 在龙芯板子上运行
将 sht31e 可执行文件拷贝到板子上（与 Python 脚本在同一目录）。

确保它具有可执行权限（chmod +x sht31e），然后在终端运行：./sht31e p

参数说明：

p：读取并打印当前温度与湿度。

s：读取并打印传感器状态（包含加热器状态）。

n：读取并打印序列号。

-h：查看全部使用说明。

  5.2 在 Python 系统中调用
上层多模态融合系统只需调用 sensor.py 中的函数即可：
        from src.sensor import get_temperature_humidity
        temp, hum = get_temperature_humidity()
        print(f"当前温度: {temp} ℃, 当前湿度: {hum} %")

##6. 故障排除
找不到 sht31e：请检查可执行文件是否与 Python 脚本在同一目录，并已赋予可执行权限。

运行 ./sht31e p 报错：请确认传感器接线是否正确，以及 I2C 设备号是否匹配（当前默认为 /dev/i2c-0）。

Python 无法解析输出：请检查输出格式是否为 "Temperature xx.xx c - xx.xx f" 和 "Humidity xx.xx%"。