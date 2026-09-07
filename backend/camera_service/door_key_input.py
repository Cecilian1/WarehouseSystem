"""读取 Linux input 子系统中的板载 USER-KEY 按键事件。"""

from __future__ import annotations

import logging
import os
import struct
import time


logger = logging.getLogger("camera_service.door_key_input")

EV_KEY = 0x01
KEY_PRESSED = 1

# Linux input_event: struct timeval + type/code/value。SDK 与开发板均为 64 位。
_INPUT_EVENT = struct.Struct("@llHHi")


class DoorKeyInput:
    """非阻塞读取实体门按键；设备断开后会自动尝试重新打开。"""

    def __init__(
        self,
        event_path: str | None,
        key_code: int = 114,
        debounce_sec: float = 0.25,
        reconnect_sec: float = 2.0,
    ):
        self.event_path = event_path or ""
        self.key_code = int(key_code)
        self.debounce_sec = max(0.0, float(debounce_sec))
        self.reconnect_sec = max(0.1, float(reconnect_sec))
        self._fd: int | None = None
        self._buffer = bytearray()
        self._last_press_at = float("-inf")
        self._next_open_at = 0.0
        self._open_warning_logged = False

    @property
    def enabled(self) -> bool:
        return bool(self.event_path)

    def _open_if_needed(self) -> bool:
        if not self.enabled:
            return False
        if self._fd is not None:
            return True
        now = time.monotonic()
        if now < self._next_open_at:
            return False
        self._next_open_at = now + self.reconnect_sec
        try:
            nonblocking = getattr(os, "O_NONBLOCK", 0)
            self._fd = os.open(self.event_path, os.O_RDONLY | nonblocking)
        except OSError:
            if not self._open_warning_logged:
                logger.warning("无法打开板载 USER-KEY: %s", self.event_path, exc_info=True)
                self._open_warning_logged = True
            return False
        self._buffer.clear()
        self._open_warning_logged = False
        logger.info("板载 USER-KEY 已打开: %s (key_code=%d)", self.event_path, self.key_code)
        return True

    def _disconnect(self) -> None:
        if self._fd is not None:
            try:
                os.close(self._fd)
            except OSError:
                pass
        self._fd = None
        self._buffer.clear()
        self._next_open_at = time.monotonic() + self.reconnect_sec

    def read_presses(self) -> int:
        """返回本轮读到且通过防抖的按下次数；无事件时立即返回。"""
        if not self._open_if_needed():
            return 0

        while True:
            try:
                chunk = os.read(self._fd, _INPUT_EVENT.size * 32)
            except BlockingIOError:
                break
            except OSError:
                logger.warning("读取板载 USER-KEY 失败，稍后重连", exc_info=True)
                self._disconnect()
                return 0
            if not chunk:
                break
            self._buffer.extend(chunk)

        presses = 0
        while len(self._buffer) >= _INPUT_EVENT.size:
            raw = self._buffer[: _INPUT_EVENT.size]
            del self._buffer[: _INPUT_EVENT.size]
            _, _, event_type, code, value = _INPUT_EVENT.unpack(raw)
            if event_type != EV_KEY or code != self.key_code or value != KEY_PRESSED:
                continue
            now = time.monotonic()
            if now - self._last_press_at < self.debounce_sec:
                continue
            self._last_press_at = now
            presses += 1
        return presses

    def close(self) -> None:
        self._disconnect()
