from __future__ import annotations

import json
import time
from pathlib import Path

import cv2
import numpy as np

from backend.ai_service.contracts import Detection


DEFAULT_CLASS_NAMES = (
    "Apple",
    "Banana",
    "Carrot",
    "Cucumber",
    "Orange",
)


def _read_onnx_model(model_path: Path) -> cv2.dnn.Net:
    try:
        return cv2.dnn.readNetFromONNX(str(model_path))
    except cv2.error:
        model_bytes = np.fromfile(model_path, dtype=np.uint8)
        if model_bytes.size == 0:
            raise RuntimeError(f"ONNX model is empty: {model_path}")
        return cv2.dnn.readNetFromONNX(model_bytes)


def _load_class_names(model_path: Path) -> tuple[str, ...]:
    manifest_path = model_path.with_name("manifest.json")
    if not manifest_path.is_file():
        return DEFAULT_CLASS_NAMES
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        class_names = manifest["detector"]["classes"]
    except (KeyError, TypeError, ValueError, OSError):
        return DEFAULT_CLASS_NAMES
    if not isinstance(class_names, list) or not all(
        isinstance(name, str) and name for name in class_names
    ):
        return DEFAULT_CLASS_NAMES
    return tuple(class_names)


class YoloDetector:
    def __init__(
        self,
        model_path: Path,
        confidence: float,
        iou: float,
        image_size: int,
        onnx_threads: int = 2,
    ) -> None:
        if model_path.suffix.lower() != ".onnx":
            raise ValueError(
                f"The board detector requires an ONNX model, received: {model_path}"
            )
        cv2.setNumThreads(max(1, onnx_threads))
        self.model = _read_onnx_model(model_path)
        self.model.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        self.model.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
        self.class_names = _load_class_names(model_path)
        self.confidence = confidence
        self.iou = iou
        self.image_size = image_size
        self.last_profile: dict[str, float] = {}

    @staticmethod
    def _species_from_label(label: str) -> str:
        # 新YOLO直接输出品类；保留分割逻辑以兼容历史的Apple_fresh标签。
        return label.split("_", 1)[0].strip().lower()

    def _letterbox(self, image: np.ndarray) -> tuple[np.ndarray, float, int, int]:
        height, width = image.shape[:2]
        scale = min(self.image_size / width, self.image_size / height)
        resized_width = max(1, round(width * scale))
        resized_height = max(1, round(height * scale))
        resized = cv2.resize(
            image,
            (resized_width, resized_height),
            interpolation=cv2.INTER_LINEAR,
        )
        padding_x = (self.image_size - resized_width) // 2
        padding_y = (self.image_size - resized_height) // 2
        canvas = np.full(
            (self.image_size, self.image_size, 3), 114, dtype=np.uint8
        )
        canvas[
            padding_y : padding_y + resized_height,
            padding_x : padding_x + resized_width,
        ] = resized
        return canvas, scale, padding_x, padding_y

    def _rows_from_output(self, output: np.ndarray) -> np.ndarray:
        rows = np.asarray(output, dtype=np.float32)
        rows = np.squeeze(rows)
        if rows.ndim != 2:
            raise RuntimeError(f"Unexpected YOLO output shape: {output.shape}")
        expected_columns = len(self.class_names) + 4
        expected_columns_with_objectness = len(self.class_names) + 5
        if rows.shape[0] in {expected_columns, expected_columns_with_objectness}:
            rows = rows.T
        if rows.shape[1] not in {
            expected_columns,
            expected_columns_with_objectness,
        }:
            raise RuntimeError(
                "YOLO output does not match detector classes: "
                f"shape={output.shape}, classes={len(self.class_names)}"
            )
        return rows

    def _class_aware_nms(
        self,
        boxes: list[list[int]],
        scores: list[float],
        class_ids: list[int],
    ) -> list[int]:
        selected: list[int] = []
        for class_id in sorted(set(class_ids)):
            candidate_indices = [
                index for index, value in enumerate(class_ids) if value == class_id
            ]
            class_boxes = [boxes[index] for index in candidate_indices]
            class_scores = [scores[index] for index in candidate_indices]
            kept = cv2.dnn.NMSBoxes(
                class_boxes,
                class_scores,
                self.confidence,
                self.iou,
            )
            for local_index in np.asarray(kept).reshape(-1):
                selected.append(candidate_indices[int(local_index)])
        return sorted(selected, key=lambda index: scores[index], reverse=True)

    def detect(self, image: np.ndarray) -> list[Detection]:
        preprocess_started = time.perf_counter()
        letterboxed, scale, padding_x, padding_y = self._letterbox(image)
        blob = cv2.dnn.blobFromImage(
            letterboxed,
            scalefactor=1.0 / 255.0,
            size=(self.image_size, self.image_size),
            swapRB=True,
            crop=False,
        )
        self.model.setInput(blob)
        preprocess_ms = (time.perf_counter() - preprocess_started) * 1000
        inference_started = time.perf_counter()
        output = self.model.forward()
        inference_ms = (time.perf_counter() - inference_started) * 1000
        postprocess_started = time.perf_counter()
        rows = self._rows_from_output(output)
        image_height, image_width = image.shape[:2]
        boxes: list[list[int]] = []
        scores: list[float] = []
        class_ids: list[int] = []

        has_objectness = rows.shape[1] == len(self.class_names) + 5
        for row in rows:
            class_start = 5 if has_objectness else 4
            class_scores = row[class_start:]
            class_id = int(np.argmax(class_scores))
            confidence = float(class_scores[class_id])
            if has_objectness:
                confidence *= float(row[4])
            if confidence < self.confidence:
                continue

            center_x, center_y, box_width, box_height = (float(v) for v in row[:4])
            left = round((center_x - box_width / 2 - padding_x) / scale)
            top = round((center_y - box_height / 2 - padding_y) / scale)
            right = round((center_x + box_width / 2 - padding_x) / scale)
            bottom = round((center_y + box_height / 2 - padding_y) / scale)
            left = max(0, min(image_width - 1, left))
            top = max(0, min(image_height - 1, top))
            right = max(0, min(image_width, right))
            bottom = max(0, min(image_height, bottom))
            if right <= left or bottom <= top:
                continue
            boxes.append([left, top, right - left, bottom - top])
            scores.append(confidence)
            class_ids.append(class_id)

        detections: list[Detection] = []
        for index in self._class_aware_nms(boxes, scores, class_ids):
            left, top, width, height = boxes[index]
            label = self.class_names[class_ids[index]]
            detections.append(
                Detection(
                    bbox=(left, top, left + width, top + height),
                    species=self._species_from_label(label),
                    detector_label=label,
                    confidence=scores[index],
                )
            )
        self.last_profile = {
            "preprocess_ms": preprocess_ms,
            "inference_ms": inference_ms,
            "postprocess_ms": (time.perf_counter() - postprocess_started) * 1000,
        }
        return detections
