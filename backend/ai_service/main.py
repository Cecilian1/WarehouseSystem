from __future__ import annotations

import argparse
import signal
import time
from dataclasses import replace
from pathlib import Path

from backend.ai_service.config import AIServiceConfig
from backend.ai_service.pipeline import InferencePipeline
from backend.ai_service.result_writer import RecognitionRepository
from backend.common.init_db import init_db
from backend.common.logging_setup import setup_logging


logger = setup_logging("ai_service")
DEFAULT_CONFIG = Path(__file__).parent / "config" / "ai_service.yaml"
_running = True


def _stop(signum, frame) -> None:
    del frame
    global _running
    logger.info("收到停止信号(%s)，准备退出", signum)
    _running = False


def run(config: AIServiceConfig, once: bool = False) -> None:
    init_db(str(config.db_path))
    repository = RecognitionRepository(config)
    pipeline = InferencePipeline(config)
    logger.info(
        "AI服务启动，YOLO=%s，新鲜度模型=%s",
        config.detector_model.name,
        config.freshness_model.name,
    )

    while _running:
        frame = repository.next_pending_frame()
        if not frame:
            if once:
                logger.info("当前没有待处理图片")
                return
            time.sleep(config.poll_interval_sec)
            continue
        frame_id = int(frame["id"])
        try:
            results = pipeline.process(frame_id, str(frame["image_path"]))
            log_ids = repository.save_results(
                frame_id,
                str(frame["image_path"]),
                results,
            )
            logger.info(
                "frame=%d 处理完成，目标=%d，inventory_log=%s",
                frame_id,
                len(results),
                log_ids,
            )
        except Exception as exc:
            repository.record_failure(frame_id, exc)
            logger.exception("frame=%d 推理失败", frame_id)
        if once:
            return


def main() -> None:
    parser = argparse.ArgumentParser(description="芯鲜管家AI推理服务")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--db-path", type=Path)
    parser.add_argument(
        "--once",
        action="store_true",
        help="只处理一条待处理图片后退出，适合本地联调",
    )
    args = parser.parse_args()
    config = AIServiceConfig.load(args.config)
    if args.db_path:
        config = replace(config, db_path=args.db_path.resolve())
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    run(config, once=args.once)


if __name__ == "__main__":
    main()
