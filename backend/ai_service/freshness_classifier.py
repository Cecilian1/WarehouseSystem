from __future__ import annotations

import time
from pathlib import Path

import cv2
import numpy as np

from backend.ai_service.contracts import FreshnessPrediction
from backend.ai_service.detector import _read_onnx_model


CLASS_NAMES = ("fresh", "mild", "rotten")
IMAGENET_MEAN = np.asarray((0.485, 0.456, 0.406), dtype=np.float32)
IMAGENET_STD = np.asarray((0.229, 0.224, 0.225), dtype=np.float32)


class FreshnessClassifier:
    def __init__(self, model_path: Path, onnx_threads: int = 2) -> None:
        if model_path.suffix.lower() != ".onnx":
            raise ValueError(
                f"The board classifier requires an ONNX model, received: {model_path}"
            )
        cv2.setNumThreads(max(1, onnx_threads))
        self.model = _read_onnx_model(model_path)
        self.model.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        self.model.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

    @staticmethod
    def _preprocess(image_bgr: np.ndarray) -> np.ndarray:
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        height, width = image_rgb.shape[:2]
        if height <= width:
            resized_height = 256
            resized_width = max(256, round(width * 256 / height))
        else:
            resized_width = 256
            resized_height = max(256, round(height * 256 / width))
        resized = cv2.resize(
            image_rgb,
            (resized_width, resized_height),
            interpolation=cv2.INTER_LINEAR,
        )
        top = (resized_height - 224) // 2
        left = (resized_width - 224) // 2
        cropped = resized[top : top + 224, left : left + 224]
        normalized = (cropped.astype(np.float32) / 255.0 - IMAGENET_MEAN) / IMAGENET_STD
        return np.transpose(normalized, (2, 0, 1))[None, ...].astype(np.float32)

    def predict(self, image_bgr: np.ndarray) -> FreshnessPrediction:
        tensor = self._preprocess(image_bgr)
        started = time.perf_counter()
        self.model.setInput(tensor)
        logits = self.model.forward().reshape(-1)
        latency_ms = (time.perf_counter() - started) * 1000
        if logits.size != len(CLASS_NAMES):
            raise RuntimeError(
                f"Unexpected freshness output shape: {logits.shape}, expected 3 logits"
            )
        shifted = logits - np.max(logits)
        probabilities = np.exp(shifted) / np.exp(shifted).sum()
        class_index = int(np.argmax(probabilities))
        probability_map = {
            label: float(probabilities[index])
            for index, label in enumerate(CLASS_NAMES)
        }
        freshness_score = probability_map["fresh"] + 0.5 * probability_map["mild"]
        return FreshnessPrediction(
            label=CLASS_NAMES[class_index],
            confidence=float(probabilities[class_index]),
            score=float(freshness_score),
            probabilities=probability_map,
            latency_ms=latency_ms,
        )
