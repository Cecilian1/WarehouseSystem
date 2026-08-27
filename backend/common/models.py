"""轻量数据类，非ORM，仅用于跨函数传递结构化数据，保持简单。"""

from dataclasses import dataclass


@dataclass
class EnvReading:
    temperature: float
    humidity: float
    is_abnormal: bool


@dataclass
class PendingFrame:
    id: int
    image_path: str
    change_ratio: float
    status: str
    created_at: str
