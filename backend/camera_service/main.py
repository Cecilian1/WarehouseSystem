"""camera_service 入口：门事件触发识别，周期采集只更新 Web 预览。"""

import logging
import signal
import sys
import time
from pathlib import Path

# 允许 `python3 main.py` 直接运行时也能找到 backend 包
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.camera_service.camera_capture import CameraCapture
from backend.camera_service.device_status_reporter import DeviceStatusReporter
from backend.camera_service.door_cycle import DoorCycleRepository
from backend.camera_service.door_key_input import DoorKeyInput
from backend.camera_service.door_led_control import DoorLedControl
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
    fill_led = LedControl(
        gpio_num=config["led_gpio"],
        warmup_sec=config["led_warmup_sec"],
    )
    door_led = DoorLedControl(
        config.get(
            "door_led_brightness_path",
            "/sys/class/leds/user-led/brightness",
        )
    )
    door_cycles = DoorCycleRepository(config["db_path"])
    door_key = DoorKeyInput(
        config.get(
            "door_key_event_path",
            "/dev/input/by-path/platform-gpio_keys@0-event",
        )
        if config.get("door_key_enabled", True)
        else None,
        key_code=int(config.get("door_key_code", 114)),
        debounce_sec=float(config.get("door_key_debounce_sec", 0.25)),
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

    preview_interval_sec = max(1.0, float(config["capture_interval_sec"]))
    poll_interval_sec = max(0.05, float(config.get("door_poll_interval_sec", 0.2)))
    close_settle_sec = max(0.0, float(config.get("close_settle_sec", 0.3)))
    latest_frame_name = config.get("latest_frame_name", "latest.jpg")

    try:
        startup_frame_cleaner.cleanup()
    except Exception:
        logger.exception("启动时清理历史图片失败，继续启动摄像头服务")
    next_cleanup_at = time.monotonic() + cleanup_interval_sec

    door_led.turn_off()
    try:
        camera.open()
    except RuntimeError:
        logger.exception("摄像头初始化失败，服务退出")
        status_reporter.report(camera_ok=False)
        sys.exit(1)

    door_cycles.recover_interrupted_capture()
    if door_cycles.has_open_cycle():
        door_led.turn_on()

    logger.info(
        "camera_service启动，门事件轮询=%.2fs，预览周期=%.1fs，实体按键=%s",
        poll_interval_sec,
        preview_interval_sec,
        door_key.event_path if door_key.enabled else "禁用",
    )
    next_preview_at = time.monotonic()

    try:
        while _running:
            cycle_start = time.monotonic()
            active_cycle_id: int | None = None
            try:
                for _ in range(door_key.read_presses()):
                    key_action, key_cycle_id = door_cycles.request_toggle()
                    if key_action == "open_requested":
                        logger.info(
                            "USER-KEY：提交开门请求，门周期%d",
                            key_cycle_id,
                        )
                    elif key_action == "close_requested":
                        logger.info(
                            "USER-KEY：提交关门拍照请求，门周期%d",
                            key_cycle_id,
                        )
                    else:
                        logger.info(
                            "USER-KEY：门周期%d正在处理中，本次按键已忽略",
                            key_cycle_id,
                        )
                if cycle_start >= next_cleanup_at:
                    next_cleanup_at = cycle_start + cleanup_interval_sec
                    try:
                        periodic_frame_cleaner.cleanup()
                    except Exception:
                        logger.exception("定时清理历史图片失败，本轮继续采集")
                captured_for_cycle = False
                action = door_cycles.next_action()
                if action is not None:
                    active_cycle_id = int(action["id"])
                    status = str(action["status"])
                    if status == "open_requested":
                        door_led.turn_on()
                        door_cycles.mark_open(active_cycle_id)
                        logger.info("门周期%d：模拟开门，板载LED已点亮", active_cycle_id)
                    elif door_cycles.claim_capture(active_cycle_id, status):
                        captured_for_cycle = True
                        door_led.turn_off()
                        time.sleep(close_settle_sec)
                        fill_led.turn_on()
                        try:
                            frame = camera.read_frame()
                        finally:
                            fill_led.turn_off()
                        if frame is None:
                            status_reporter.report(camera_ok=False)
                            door_cycles.mark_failed(active_cycle_id, "摄像头拍照失败")
                        else:
                            frame_writer.save_latest(frame, latest_frame_name)
                            frame_id = frame_writer.save_and_register(
                                frame,
                                1.0,
                                door_cycle_id=active_cycle_id,
                            )
                            if frame_id is None:
                                door_cycles.mark_failed(active_cycle_id, "AI待处理队列已满")
                            else:
                                status_reporter.report(camera_ok=True)
                                next_preview_at = time.monotonic() + preview_interval_sec
                                logger.info(
                                    "门周期%d：关门拍照完成，pending_frames.id=%d",
                                    active_cycle_id,
                                    frame_id,
                                )

                now = time.monotonic()
                if not captured_for_cycle and now >= next_preview_at:
                    next_preview_at = now + preview_interval_sec
                    fill_led.turn_on()
                    try:
                        preview_frame = camera.read_frame()
                    finally:
                        fill_led.turn_off()
                    if preview_frame is None:
                        status_reporter.report(camera_ok=False)
                    else:
                        frame_writer.save_latest(preview_frame, latest_frame_name)
                        status_reporter.report(camera_ok=True)
            except Exception:
                logger.exception("采集循环发生异常，本轮跳过")
                fill_led.turn_off()
                if active_cycle_id is not None:
                    door_led.turn_off()
                    door_cycles.mark_failed(active_cycle_id, "摄像头服务处理异常")

            elapsed = time.monotonic() - cycle_start
            sleep_time = max(0.0, poll_interval_sec - elapsed)
            time.sleep(sleep_time)
    finally:
        door_key.close()
        fill_led.close()
        door_led.turn_off()
        camera.close()
        logger.info("camera_service已停止")


if __name__ == "__main__":
    main()
