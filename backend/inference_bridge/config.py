from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from backend.ai_service.config import ProduceDefinition
from backend.common.catalog import PRODUCE_CATALOG
from backend.common.config import load_yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = Path(__file__).parent / "config" / "inference_bridge.yaml"

_SPECIES_BY_NAME = {
    "苹果": "apple",
    "香蕉": "banana",
    "胡萝卜": "carrot",
    "黄瓜": "cucumber",
    "橙子": "orange",
}


def _resolve_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def default_produce_catalog() -> dict[str, ProduceDefinition]:
    catalog: dict[str, ProduceDefinition] = {}
    for item in PRODUCE_CATALOG:
        species = _SPECIES_BY_NAME[item.name]
        catalog[species] = ProduceDefinition(
            name=item.name,
            category=item.category,
            shelf_life_days=item.shelf_life_days,
            unit=item.unit,
        )
    return catalog


def species_from_produce_name(name: str) -> str | None:
    return _SPECIES_BY_NAME.get(str(name).strip())


@dataclass(frozen=True)
class BridgeConfig:
    main_db_path: Path
    worker_db_path: Path
    lock_path: Path
    poll_interval_sec: float
    worker_timeout_sec: float
    lease_renew_sec: float
    stale_claim_minutes: int
    max_attempts: int
    model_version: str
    produce_catalog: dict[str, ProduceDefinition]

    @classmethod
    def load(cls, config_path: str | Path | None = None) -> "BridgeConfig":
        raw = load_yaml(str(config_path or DEFAULT_CONFIG))
        main_db = os.environ.get("WAREHOUSE_DB_PATH") or str(raw["main_db_path"])
        worker_db = os.environ.get("WAREHOUSE_INFERENCE_WORKER_DB") or str(
            raw["worker_db_path"]
        )
        lock_path = os.environ.get("WAREHOUSE_INFERENCE_BRIDGE_LOCK") or str(
            raw.get("lock_path") or "/data/warehousekeeper/inference-bridge.lock"
        )
        config = cls(
            main_db_path=_resolve_path(main_db),
            worker_db_path=_resolve_path(worker_db),
            lock_path=_resolve_path(lock_path),
            poll_interval_sec=float(raw.get("poll_interval_sec", 1.0)),
            worker_timeout_sec=float(raw.get("worker_timeout_sec", 180.0)),
            lease_renew_sec=float(raw.get("lease_renew_sec", 30.0)),
            stale_claim_minutes=int(raw.get("stale_claim_minutes", 5)),
            max_attempts=int(raw.get("max_attempts", 3)),
            model_version=str(
                raw.get("model_version") or "yolo-best+shufflenet-v4-bridge"
            ),
            produce_catalog=default_produce_catalog(),
        )
        config.validate()
        return config

    def validate(self) -> None:
        if self.main_db_path.resolve() == self.worker_db_path.resolve():
            raise ValueError("主库和工作库不能是同一个文件")
        if self.poll_interval_sec <= 0:
            raise ValueError("poll_interval_sec 必须大于 0")
        if self.worker_timeout_sec <= 0:
            raise ValueError("worker_timeout_sec 必须大于 0")
        if self.lease_renew_sec <= 0:
            raise ValueError("lease_renew_sec 必须大于 0")
