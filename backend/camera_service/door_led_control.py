"""通过 Linux LED 子系统控制板载门状态指示灯。"""

import logging
from pathlib import Path


logger = logging.getLogger("camera_service.door_led_control")


class DoorLedControl:
    """板载 LED：亮表示门开，灭表示门关。"""

    def __init__(self, brightness_path: str):
        self.brightness_path = Path(brightness_path)
        self._available = self.brightness_path.is_file()
        self._on_value = 1
        if not self._available:
            logger.warning("板载门状态 LED 不存在: %s", self.brightness_path)
            return
        max_path = self.brightness_path.with_name("max_brightness")
        try:
            if max_path.is_file():
                self._on_value = max(1, int(max_path.read_text().strip()))
        except (OSError, ValueError):
            logger.warning("读取 LED 最大亮度失败，使用亮度 1", exc_info=True)

    def _write(self, value: int) -> None:
        if not self._available:
            return
        try:
            self.brightness_path.write_text(str(value))
        except OSError:
            logger.warning("写入板载 LED 失败: %s", self.brightness_path, exc_info=True)

    def turn_on(self) -> None:
        self._write(self._on_value)

    def turn_off(self) -> None:
        self._write(0)

