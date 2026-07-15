"""env_service 入口：周期性读取SHT30温湿度，写入env_log，异常时生成告警。

流程（对应docx 2.3节温湿度独立采集流程）：
1. 按interval读取一次SHT30
2. 读取失败/CRC校验失败则跳过本次写入，只记录warning日志
3. 判定是否处于设备异常状态(温度持续超阈值)
4. 写入env_log（含is_abnormal标记）
5. sleep至下一周期
"""

import logging
import signal
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.common.config import load_yaml
from backend.common.db import connection_scope
from backend.common.init_db import init_db
from backend.common.logging_setup import setup_logging
from backend.env_service.alert_evaluator import AlertEvaluator
from backend.env_service.device_status_reporter import DeviceStatusReporter
from backend.env_service.sht30_driver import SHT30, SHT30ReadError

logger = setup_logging("env_service")

_CONFIG_PATH = Path(__file__).parent / "config" / "env_service.yaml"

_running = True


def _handle_shutdown(signum, frame):
    global _running
    logger.info("收到停止信号(%s)，准备退出主循环", signum)
    _running = False


def _write_env_log(db_path: str, temperature: float, humidity: float, is_abnormal: bool) -> None:
    with connection_scope(db_path) as conn:
        conn.execute(
            """
            INSERT INTO env_log (temperature, humidity, is_abnormal)
            VALUES (?, ?, ?)
            """,
            (temperature, humidity, int(is_abnormal)),
        )


def main() -> None:
    signal.signal(signal.SIGTERM, _handle_shutdown)
    signal.signal(signal.SIGINT, _handle_shutdown)

    config = load_yaml(str(_CONFIG_PATH))

    init_db(config["db_path"])

    sht30_address = config["sht30_address"]
    if isinstance(sht30_address, str):
        sht30_address = int(sht30_address, 0)  # 支持yaml里写 "0x44" 字符串

    sensor = SHT30(bus_path=config["i2c_bus"], address=sht30_address)
    evaluator = AlertEvaluator(
        db_path=config["db_path"],
        temp_high_threshold_c=config["temp_high_threshold_c"],
        abnormal_duration_sec=config["abnormal_duration_sec"],
    )
    status_reporter = DeviceStatusReporter(
        db_path=config["db_path"],
        device_id=config["device_id"],
    )

    interval_sec = config["read_interval_sec"]

    try:
        sensor.open()
    except OSError:
        logger.exception("SHT30初始化失败(I2C总线打开异常)，服务退出")
        status_reporter.report(sensor_ok=False)
        sys.exit(1)

    logger.info("env_service启动，采集周期=%ds", interval_sec)

    try:
        while _running:
            cycle_start = time.monotonic()
            try:
                temperature, humidity = sensor.read_temperature_humidity()
                is_abnormal = evaluator.evaluate(temperature)
                _write_env_log(config["db_path"], temperature, humidity, is_abnormal)
                status_reporter.report(sensor_ok=True)
                logger.debug(
                    "读数: temp=%.2f humidity=%.2f abnormal=%s",
                    temperature,
                    humidity,
                    is_abnormal,
                )
            except SHT30ReadError as e:
                logger.warning("传感器读取校验失败，本次跳过写入: %s", e)
                status_reporter.report(sensor_ok=False)
            except Exception:
                logger.exception("采集循环发生异常，本轮跳过")
                status_reporter.report(sensor_ok=False)

            elapsed = time.monotonic() - cycle_start
            sleep_time = max(0.0, interval_sec - elapsed)
            time.sleep(sleep_time)
    finally:
        sensor.close()
        logger.info("env_service已停止")


if __name__ == "__main__":
    main()
