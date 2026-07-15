"""SHT30/SHT31温湿度传感器 I2C 用户态驱动。

标准Linux用户态I2C编程模式：open("/dev/i2c-X") + ioctl(fd, I2C_SLAVE, addr)
绑定从机地址，再用 write/read 收发数据。

===================== 重要：需要开发者核实的部分 =====================
下面的测量命令字节(CMD_MEASURE_MSB/CMD_MEASURE_LSB)、CRC校验多项式、
以及测量转换等待时间，是SHT3x系列传感器的典型/通用实现结构，
但具体十六进制数值必须由开发者对照 Sensirion SHT30 官方datasheet的
"Command"表逐一核实后再确认/修改，不要直接采信本文件中的占位数值就用于生产。
本文件的目的是提供正确的读取流程骨架和CRC校验框架，而非声称给出了
已验证正确的命令字节。
======================================================================
"""

import fcntl
import logging
import os
import time

logger = logging.getLogger("env_service.sht30_driver")

# Linux ioctl常量（来自 <linux/i2c-dev.h>），标准值，跨平台通用，无需核实
I2C_SLAVE = 0x0703

# TODO: 对照SHT30 datasheet "Measurement Commands" 表核实以下命令字节。
# 此处采用的是"高重复性、禁用clock-stretching"测量模式的常见命令字示例结构，
# 实际数值请以datasheet为准后修改。
CMD_MEASURE_MSB = 0x24  # 占位，需核实
CMD_MEASURE_LSB = 0x00  # 占位，需核实

# TODO: 核实典型/最大转换等待时间（datasheet通常在数毫秒~十几毫秒量级，
# 具体因重复性模式而异），此处取一个偏保守的默认值。
MEASURE_WAIT_SEC = 0.02


def _crc8(data: bytes) -> int:
    """SHT3x使用的CRC8校验，多项式0x31，初始值0xFF（该算法为Sensirion
    数据手册中公开记载的标准CRC-8/SHT3x实现方式，可直接使用）。
    """
    crc = 0xFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0x31) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc


class SHT30ReadError(Exception):
    pass


class SHT30:
    def __init__(self, bus_path: str, address: int):
        self.bus_path = bus_path
        self.address = address
        self.fd: int | None = None

    def open(self) -> None:
        self.fd = os.open(self.bus_path, os.O_RDWR)
        fcntl.ioctl(self.fd, I2C_SLAVE, self.address)
        logger.info("SHT30已打开: bus=%s addr=0x%02x", self.bus_path, self.address)

    def read_temperature_humidity(self) -> tuple[float, float]:
        """返回 (temperature_celsius, humidity_percent)。CRC校验失败抛SHT30ReadError。"""
        if self.fd is None:
            self.open()

        os.write(self.fd, bytes([CMD_MEASURE_MSB, CMD_MEASURE_LSB]))
        time.sleep(MEASURE_WAIT_SEC)

        raw = os.read(self.fd, 6)
        if len(raw) != 6:
            raise SHT30ReadError(f"读取字节数异常: 期望6字节，实际{len(raw)}字节")

        temp_bytes, temp_crc = raw[0:2], raw[2]
        hum_bytes, hum_crc = raw[3:5], raw[5]

        if _crc8(temp_bytes) != temp_crc:
            raise SHT30ReadError("温度数据CRC校验失败")
        if _crc8(hum_bytes) != hum_crc:
            raise SHT30ReadError("湿度数据CRC校验失败")

        temp_raw = (temp_bytes[0] << 8) | temp_bytes[1]
        hum_raw = (hum_bytes[0] << 8) | hum_bytes[1]

        # 标准SHT3x换算公式（datasheet公开记载，可直接使用）
        temperature = -45 + 175 * (temp_raw / 65535.0)
        humidity = 100 * (hum_raw / 65535.0)

        return temperature, humidity

    def close(self) -> None:
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
