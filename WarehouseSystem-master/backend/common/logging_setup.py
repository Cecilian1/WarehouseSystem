"""统一日志格式。服务以systemd常驻运行时，stdout/stderr由journal自动收集，
因此这里只配置到stdout的StreamHandler，不额外写文件，避免日志轮转的额外复杂度。
"""

import logging
import sys


def setup_logging(service_name: str, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(service_name)
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
