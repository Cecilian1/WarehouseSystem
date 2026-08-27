"""camera_service 入口：周期性补光+采集+帧间差分触发判断。

流程（对应docx 2.3节视觉触发流程）：
1. 点亮LED补光灯
2. 清理UVC旧缓冲并采集一帧图像
3. 原子更新latest.jpg，供Web预览
4. 熄灭LED补光灯（节能）
5. 与上一帧做帧间差分，计算变化像素占比
6. 变化占比超阈值则落盘图片+登记pending_frames，供未来AI服务消费
7. sleep至下一周期
"""

import logging
import signal
import sys
import time
from pathlib import Path

# 允许 `python3 main.py` 直接运行时也能找到 backend 包
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.camera_service.camera_capture import CameraCapture
from backend.camera_service.device_status_reporter import DeviceStatusReporter
from backend.camera_service.frame_diff import FrameDiffDetector
from backend.camera_service.led_control import LedControl
from backend.camera_service.pending_frame_writer import PendingFrameWriter
from backend.common.config import load_yaml
from backend.common.frame_cleanup import (
    FrameRetentionCleaner,
    FrameRetentionPolicy,
)
from backend.common.init_db import init_db
from backend.common.logging_setup import setup_logging

logger = setup_logging("camera_service")

_CONFIG_PATH = Path(__file__).parent / "config" / "camera_service.yaml"

_running = True


def _handle_shutdown(signum, frame):
    global _running
    logger.info("收到停止信号(%s)，准备退出主循环", signum)
    _running = False


def main() -> None:
    signal.signal(signal.SIGTERM, _handle_shutdown)
    signal.signal(signal.SIGINT, _handle_shutdown)

    config = load_yaml(str(_CONFIG_PATH))

    init_db(config["db_path"])

    camera = CameraCapture(
        device=config["camera_device"],
        resolution=tuple(config["resolution"]),
        discard_frames_before_capture=config.get("discard_frames_before_capture", 4),
    )
    led = LedControl(
        gpio_num=config["led_gpio"],
        warmup_sec=config["led_warmup_sec"],
    )
    diff_detector = FrameDiffDetector(
        downsample_size=tuple(config["diff_downsample"]),
        diff_threshold=config["diff_threshold"],
    )
    frame_writer = PendingFrameWriter(
        db_path=config["db_path"],
        frame_save_dir=config["frame_save_dir"],
        max_pending_frames=int(config.get("max_pending_frames", 1000)),
    )
    status_reporter = DeviceStatusReporter(
        db_path=config["db_path"],
        device_id=config["device_id"],
    )
    cleanup_interval_sec = max(
        60,
        int(config.get("frame_cleanup_interval_sec", 3600)),
    )
    startup_frame_cleaner = FrameRetentionCleaner(
        db_path=config["db_path"],
        frame_root=config["frame_save_dir"],
        latest_frame_name=config.get("latest_frame_name", "latest.jpg"),
        policy=FrameRetentionPolicy(
            completed_retention_days=int(
                config.get("completed_frame_retention_days", 7)
            ),
            pending_retention_days=int(
                config.get("pending_frame_retention_days", 7)
            ),
            max_completed_frames=int(config.get("max_completed_frames", 1000)),
            max_pending_frames=int(config.get("max_pending_frames", 1000)),
        ),
    )
    periodic_frame_cleaner = FrameRetentionCleaner(
        db_path=config["db_path"],
        frame_root=config["frame_save_dir"],
        latest_frame_name=config.get("latest_frame_name", "latest.jpg"),
        policy=FrameRetentionPolicy(
            completed_retention_days=int(
                config.get("completed_frame_retention_days", 7)
            ),
            pending_retention_days=0,
            max_completed_frames=int(config.get("max_completed_frames", 1000)),
            max_pending_frames=0,
        ),
    )

    change_ratio_threshold = config["change_ratio_threshold"]
    interval_sec = config["capture_interval_sec"]
    latest_frame_name = config.get("latest_frame_name", "latest.jpg")

    try:
        startup_frame_cleaner.cleanup()
    except Exception:
        logger.exception("启动时清理历史图片失败，继续启动摄像头服务")
    next_cleanup_at = time.monotonic() + cleanup_interval_sec

    try:
        camera.open()
    except RuntimeError:
        logger.exception("摄像头初始化失败，服务退出")
        status_reporter.report(camera_ok=False)
        sys.exit(1)

    logger.info("camera_service启动，采集周期=%ds", interval_sec)

    try:
        while _running:
            cycle_start = time.monotonic()
            try:
                if cycle_start >= next_cleanup_at:
                    next_cleanup_at = cycle_start + cleanup_interval_sec
                    try:
                        periodic_frame_cleaner.cleanup()
                    except Exception:
                        logger.exception("定时清理历史图片失败，本轮继续采集")
                led.turn_on()
                frame = camera.read_frame()
                led.turn_off()

                if frame is None:
                    status_reporter.report(camera_ok=False)
                else:
                    frame_writer.save_latest(frame, latest_frame_name)
                    status_reporter.report(camera_ok=True)
                    change_ratio = diff_detector.compute_change_ratio(frame)
                    if change_ratio >= change_ratio_threshold:
                        frame_writer.save_and_register(frame, change_ratio)
                    else:
                        logger.debug("变化占比%.3f未达阈值，跳过本次登记", change_ratio)
            except Exception:
                logger.exception("采集循环发生异常，本轮跳过")
                led.turn_off()

            elapsed = time.monotonic() - cycle_start
            sleep_time = max(0.0, interval_sec - elapsed)
            time.sleep(sleep_time)
    finally:
        led.close()
        camera.close()
        logger.info("camera_service已停止")


if __name__ == "__main__":
    main()
