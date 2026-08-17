from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Detection:
    bbox: tuple[int, int, int, int]
    species: str
    detector_label: str
    confidence: float


@dataclass(frozen=True)
class FreshnessPrediction:
    label: str
    confidence: float
    score: float
    probabilities: dict[str, float]
    latency_ms: float


@dataclass(frozen=True)
class RecognitionResult:
    detection: Detection
    freshness: FreshnessPrediction
    crop_path: Path
    image_width: int
    image_height: int
    inference_latency_ms: float

