from __future__ import annotations

import argparse
import signal
import time
from pathlib import Path

from backend.common.init_db import init_db
from backend.common.logging_setup import setup_logging
from backend.inference_bridge.config import DEFAULT_CONFIG, BridgeConfig
from backend.inference_bridge.instance_lock import InstanceLock, InstanceLockError
from backend.inference_bridge.service import InferenceBridge


logger = setup_logging("inference_bridge")
_running = True


def _stop(signum, frame) -> None:
    del frame
    global _running
    logger.info("收到停止信号(%s)，准备退出", signum)
    _running = False


def run(config: BridgeConfig) -> None:
    init_db(str(config.main_db_path))
    init_db(str(config.worker_db_path))
    bridge = InferenceBridge(config)
    logger.info(
        "inference-bridge 启动，主库=%s，工作库=%s",
        config.main_db_path,
        config.worker_db_path,
    )
    while _running:
        try:
            if not bridge.process_once():
                time.sleep(config.poll_interval_sec)
        except Exception:
            logger.exception("处理门周期推理任务失败，本轮跳过")
            time.sleep(config.poll_interval_sec)


def main() -> None:
    parser = argparse.ArgumentParser(description="芯鲜管家推理桥接服务")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    config = BridgeConfig.load(args.config)
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    try:
        with InstanceLock(config.lock_path):
            run(config)
    except InstanceLockError as exc:
        logger.error("%s", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
