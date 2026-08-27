from __future__ import annotations

import time
from pathlib import Path

import cv2
import numpy as np

from backend.ai_service.config import AIServiceConfig
from backend.ai_service.contracts import Detection, RecognitionResult
from backend.ai_service.detector import YoloDetector
from backend.ai_service.freshness_classifier import FreshnessClassifier


class InferencePipeline:
    def __init__(self, config: AIServiceConfig) -> None:
        self.config = config
        self.detector = YoloDetector(
            config.detector_model,
            config.detector_confidence,
            config.detector_iou,
            config.detector_image_size,
            config.onnx_threads,
        )
        self.classifier = FreshnessClassifier(
            config.freshness_model,
            config.onnx_threads,
        )
        config.crop_dir.mkdir(parents=True, exist_ok=True)

    def _crop(self, image, detection: Detection):
        image_height, image_width = image.shape[:2]
        x1, y1, x2, y2 = detection.bbox
        padding_x = round((x2 - x1) * self.config.bbox_padding_ratio)
        padding_y = round((y2 - y1) * self.config.bbox_padding_ratio)
        left = max(0, x1 - padding_x)
        top = max(0, y1 - padding_y)
        right = min(image_width, x2 + padding_x)
        bottom = min(image_height, y2 + padding_y)
        return image[top:bottom, left:right]

    @staticmethod
    def _write_image(path: Path, image) -> bool:
        if cv2.imwrite(str(path), image):
            return True
        suffix = path.suffix or ".jpg"
        encoded, buffer = cv2.imencode(suffix, image)
        if not encoded:
            return False
        buffer.tofile(path)
        return True

    def process(self, frame_id: int, image_path: str | Path) -> list[RecognitionResult]:
        image_path = Path(image_path)
        image = cv2.imread(str(image_path))
        if image is None and image_path.is_file():
            image = cv2.imdecode(
                np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR
            )
        if image is None:
            raise ValueError(f"图片无法读取: {image_path}")
        image_height, image_width = image.shape[:2]

        detector_started = time.perf_counter()
        detections = self.detector.detect(image)
        detector_latency_ms = (time.perf_counter() - detector_started) * 1000
        results: list[RecognitionResult] = []
        supported = self.config.produce_catalog
        for index, detection in enumerate(detections):
            if detection.species not in supported:
                continue
            crop = self._crop(image, detection)
            if crop.size == 0 or min(crop.shape[:2]) < 16:
                continue
            prediction = self.classifier.predict(crop)
            crop_path = self.config.crop_dir / (
                f"frame_{frame_id}_target_{index}_{detection.species}.jpg"
            )
            if not self._write_image(crop_path, crop):
                raise OSError(f"裁剪图保存失败: {crop_path}")
            results.append(
                RecognitionResult(
                    detection=detection,
                    freshness=prediction,
                    crop_path=crop_path,
                    image_width=image_width,
                    image_height=image_height,
                    inference_latency_ms=detector_latency_ms + prediction.latency_ms,
                )
            )
        return results
