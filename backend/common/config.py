"""极简YAML配置读取，不引入环境变量插值/多层继承等复杂特性。

各服务自行定义dataclass并调用 load_yaml() 拿到dict后自行构造，
避免在common里为每个服务的字段耦合一份schema。
"""

from pathlib import Path
from typing import Any

import yaml


def load_yaml(config_path: str) -> dict[str, Any]:
    path = Path(config_path)
    if not path.is_file():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}
