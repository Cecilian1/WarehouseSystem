"""USB UVC摄像头采集封装（V4L2，通过OpenCV cv2.VideoCapture）。

摄像头句柄常驻打开，主循环按周期调用一次 read_frame()。每次正式取帧前
丢弃少量V4L2缓冲帧，避免低频读取时拿到旧画面；不做连续read()空转，
把CPU占用集中在取帧与差分的短暂窗口内。
"""

import logging

import cv2

logger = logging.getLogger("camera_service.camera_capture")


class CameraCapture:
    def __init__(
        self,
        device: str,
        resolution: tuple[int, int],
        discard_frames_before_capture: int = 4,
    ):
        self.device = device
        self.resolution = resolution
        self.discard_frames_before_capture = max(0, discard_frames_before_capture)
        self.cap: cv2.VideoCapture | None = None

    def open(self) -> None:
        self.cap = cv2.VideoCapture(self.device, cv2.CAP_V4L2)
        if not self.cap.isOpened():
            raise RuntimeError(f"无法打开摄像头设备: {self.device}")
        width, height = self.resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        logger.info("摄像头已打开: %s (%dx%d)", self.device, width, height)

    def read_frame(self):
        """返回一帧BGR图像（numpy数组），失败返回None。"""
        if self.cap is None or not self.cap.isOpened():
            logger.warning("摄像头句柄未打开，尝试重新打开")
            self.open()
        if self.discard_frames_before_capture <= 0:
            ok, frame = self.cap.read()
        else:
            ok = True
            for _ in range(self.discard_frames_before_capture):
                ok = self.cap.grab()
                if not ok:
                    break
            ok, frame = self.cap.retrieve() if ok else (False, None)
        if not ok:
            logger.warning("读取摄像头帧失败")
            return None
        return frame

    def close(self) -> None:
        if self.cap is not None:
            self.cap.release()
            self.cap = None
