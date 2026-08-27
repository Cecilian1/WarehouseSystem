"""设备异常（制冷故障）判定：温度持续超过安全阈值达到设定时长则生成告警。

维护内存中"连续超阈值起始时间"游标（服务重启后计时归零，这是可接受的
简化行为，因为重启本身间隔通常远小于abnormal_duration_sec）。
生成告警后做防抖，避免同一次异常状态期间重复插入多条alert_record。
"""

import logging
import time

from backend.common.db import connection_scope

logger = logging.getLogger("env_service.alert_evaluator")


class AlertEvaluator:
    def __init__(
        self,
        db_path: str,
        temp_high_threshold_c: float,
        abnormal_duration_sec: float,
    ):
        self.db_path = db_path
        self.temp_high_threshold_c = temp_high_threshold_c
        self.abnormal_duration_sec = abnormal_duration_sec

        self._abnormal_since: float | None = None
        self._alert_generated_this_episode = False

    def evaluate(self, temperature: float) -> bool:
        """输入本次读数，返回本次是否处于"异常"状态(is_abnormal)。
        若持续超阈值达到设定时长且本轮尚未生成过告警，则写入alert_record。
        """
        now = time.monotonic()

        if temperature > self.temp_high_threshold_c:
            if self._abnormal_since is None:
                self._abnormal_since = now
                self._alert_generated_this_episode = False

            duration = now - self._abnormal_since
            is_abnormal = duration >= self.abnormal_duration_sec

            if is_abnormal and not self._alert_generated_this_episode:
                self._create_device_abnormal_alert(temperature)
                self._alert_generated_this_episode = True

            return is_abnormal
        else:
            # 温度恢复正常，重置计时
            self._abnormal_since = None
            self._alert_generated_this_episode = False
            return False

    def _create_device_abnormal_alert(self, temperature: float) -> None:
        with connection_scope(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO alert_record (produce_id, alert_type, expire_date, is_read)
                VALUES (NULL, 'device_abnormal', NULL, 0)
                """
            )
        logger.warning(
            "生成设备异常告警：温度%.1f℃持续超过阈值%.1f℃达到%d秒以上",
            temperature,
            self.temp_high_threshold_c,
            self.abnormal_duration_sec,
        )
