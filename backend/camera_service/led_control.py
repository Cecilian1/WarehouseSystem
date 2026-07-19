"""LED补光灯GPIO控制。

优先尝试 gpiod（字符设备 /dev/gpiochipN，现代接口，无sysfs的export残留问题）；
若运行环境未安装 python3-gpiod / gpiod库，降级到传统 sysfs 接口
（/sys/class/gpio/export + direction + value），该接口在官方
《ATK-DL2K300嵌入式Linux C应用编程指南》第17章有文档记载，是本板已验证可用的方式。

具体GPIO编号由 camera_service.yaml 的 led_gpio 配置项提供，
需开发者依据JP7扩展排针实测确定，本模块不假设具体引脚含义。
"""

import logging
import os
import time

logger = logging.getLogger("camera_service.led_control")

try:
    import gpiod  # type: ignore

    _HAS_GPIOD = True
except ImportError:
    _HAS_GPIOD = False

_SYSFS_GPIO_ROOT = "/sys/class/gpio"


class LedControl:
    def __init__(self, gpio_num: int, warmup_sec: float = 0.08):
        self.gpio_num = gpio_num
        self.warmup_sec = warmup_sec
        self._line = None  # gpiod line，仅gpiod路径使用
        self._chip = None
        self._available = False  # LED是否可用标志

        if _HAS_GPIOD:
            try:
                self._init_gpiod()
                self._available = True
            except Exception as e:
                logger.warning(f"gpiod初始化失败: {e}，尝试sysfs...")
                try:
                    self._init_sysfs()
                    self._available = True
                except OSError as e2:
                    logger.warning(f"LED GPIO {gpio_num} 初始化失败（可能被占用或无权限），禁用LED: {e2}")
        else:
            try:
                self._init_sysfs()
                self._available = True
            except OSError as e:
                logger.warning(f"LED GPIO {gpio_num} 初始化失败（可能被占用或无权限），禁用LED: {e}")

    # ---------- gpiod 路径 ----------
    def _init_gpiod(self) -> None:
        # 假设GPIO位于gpiochip0，若实测不是该芯片号，需要开发者调整此处
        # 或改为传入 chip_name 配置项。
        self._chip = gpiod.Chip("gpiochip0")
        self._line = self._chip.get_line(self.gpio_num)
        self._line.request(consumer="camera_service_led", type=gpiod.LINE_REQ_DIR_OUT)
        logger.info("LED控制使用gpiod接口，gpio=%d", self.gpio_num)

    def _set_gpiod(self, value: int) -> None:
        self._line.set_value(value)

    # ---------- sysfs 路径 ----------
    def _init_sysfs(self) -> None:
        gpio_path = f"{_SYSFS_GPIO_ROOT}/gpio{self.gpio_num}"
        if not os.path.isdir(gpio_path):
            with open(f"{_SYSFS_GPIO_ROOT}/export", "w") as f:
                f.write(str(self.gpio_num))
            time.sleep(0.1)  # 等待sysfs节点创建
        with open(f"{gpio_path}/direction", "w") as f:
            f.write("out")
        logger.info("LED控制使用sysfs接口，gpio=%d", self.gpio_num)

    def _set_sysfs(self, value: int) -> None:
        gpio_path = f"{_SYSFS_GPIO_ROOT}/gpio{self.gpio_num}/value"
        with open(gpio_path, "w") as f:
            f.write(str(value))

    # ---------- 对外接口 ----------
    def _set(self, value: int) -> None:
        if _HAS_GPIOD:
            self._set_gpiod(value)
        else:
            self._set_sysfs(value)

    def turn_on(self) -> None:
        if not self._available:
            return
        try:
            self._set(1)
            time.sleep(self.warmup_sec)
        except Exception as e:
            logger.warning(f"LED turn_on失败: {e}")

    def turn_off(self) -> None:
        if not self._available:
            return
        try:
            self._set(0)
        except Exception as e:
            logger.warning(f"LED turn_off失败: {e}")

    def close(self) -> None:
        if _HAS_GPIOD and self._chip is not None:
            self._chip.close()
        # sysfs路径不做unexport，避免和其他并发访问者产生竞争；
        # 若需要彻底释放，可在服务停止时手动 `echo N > unexport`。
