from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.common.config import load_yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _resolve_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


@dataclass(frozen=True)
class ProduceDefinition:
    name: str
    category: str
    shelf_life_days: int
    unit: str


@dataclass(frozen=True)
class AIServiceConfig:
    db_path: Path
    detector_model: Path
    freshness_model: Path
    crop_dir: Path
    detector_confidence: float
    detector_iou: float
    detector_image_size: int
    bbox_padding_ratio: float
    poll_interval_sec: float
    max_attempts: int
    onnx_threads: int
    inventory_action: str
    update_stock_summary: bool
    model_version: str
    produce_catalog: dict[str, ProduceDefinition]

    @classmethod
    def load(cls, config_path: str | Path) -> "AIServiceConfig":
        raw = load_yaml(str(config_path))
        catalog: dict[str, ProduceDefinition] = {}
        for species, item in raw.get("produce_catalog", {}).items():
            catalog[str(species).lower()] = ProduceDefinition(
                name=str(item["name"]),
                category=str(item.get("category") or "水果"),
                shelf_life_days=int(item.get("shelf_life_days") or 0),
                unit=str(item.get("unit") or "个"),
            )

        db_path = os.environ.get("WAREHOUSE_DB_PATH") or str(raw["db_path"])
        detector_model = os.environ.get("WAREHOUSE_YOLO_MODEL_PATH") or str(
            raw["detector_model"]
        )
        freshness_model = os.environ.get(
            "WAREHOUSE_FRESHNESS_MODEL_PATH"
        ) or str(raw["freshness_model"])
        action = str(raw.get("inventory_action") or "IN").upper()
        if action not in {"IN", "OUT"}:
            raise ValueError("inventory_action 必须为 IN 或 OUT")

        config = cls(
            db_path=_resolve_path(db_path),
            detector_model=_resolve_path(detector_model),
            freshness_model=_resolve_path(freshness_model),
            crop_dir=_resolve_path(str(raw.get("crop_dir") or "data/ai_crops")),
            detector_confidence=float(raw.get("detector_confidence", 0.35)),
            detector_iou=float(raw.get("detector_iou", 0.45)),
            detector_image_size=int(raw.get("detector_image_size", 640)),
            bbox_padding_ratio=float(raw.get("bbox_padding_ratio", 0.05)),
            poll_interval_sec=float(raw.get("poll_interval_sec", 1.0)),
            max_attempts=int(raw.get("max_attempts", 3)),
            onnx_threads=max(1, int(raw.get("onnx_threads", 2))),
            inventory_action=action,
            update_stock_summary=bool(raw.get("update_stock_summary", False)),
            model_version=str(raw.get("model_version") or "yolo+shufflenet-v1"),
            produce_catalog=catalog,
        )
        config.validate()
        return config

    def validate(self) -> None:
        if not self.detector_model.is_file():
            raise FileNotFoundError(f"YOLO模型不存在: {self.detector_model}")
        if not self.freshness_model.is_file():
            raise FileNotFoundError(f"新鲜度模型不存在: {self.freshness_model}")
        if not self.produce_catalog:
            raise ValueError("produce_catalog 不能为空")

