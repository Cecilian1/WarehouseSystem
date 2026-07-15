"""帧间差分：灰度化 + 高斯模糊 + absdiff + 阈值二值化 + 变化像素占比。

不使用复杂的背景建模（如MOG2），简单差分足以满足"画面内容物是否发生变动"
的触发判断需求，且计算量对单核1GHz CPU更友好。
"""

import cv2
import numpy as np


class FrameDiffDetector:
    def __init__(
        self,
        downsample_size: tuple[int, int] = (320, 240),
        diff_threshold: int = 25,
    ):
        self.downsample_size = downsample_size
        self.diff_threshold = diff_threshold
        self._prev_gray: np.ndarray | None = None

    def _preprocess(self, frame: np.ndarray) -> np.ndarray:
        small = cv2.resize(frame, self.downsample_size)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        return gray

    def compute_change_ratio(self, frame: np.ndarray) -> float:
        """返回本帧相对上一帧的变化像素占比 [0, 1]。首帧返回0.0并记录基准帧。"""
        gray = self._preprocess(frame)

        if self._prev_gray is None:
            self._prev_gray = gray
            return 0.0

        diff = cv2.absdiff(self._prev_gray, gray)
        _, thresh = cv2.threshold(diff, self.diff_threshold, 255, cv2.THRESH_BINARY)
        changed_ratio = cv2.countNonZero(thresh) / thresh.size

        self._prev_gray = gray
        return changed_ratio
