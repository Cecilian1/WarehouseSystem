from __future__ import annotations

import json
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from backend.ai_service.config import AIServiceConfig, ProduceDefinition
from backend.ai_service.contracts import RecognitionResult
from backend.common.db import connection_scope


class RecognitionRepository:
    def __init__(self, config: AIServiceConfig) -> None:
        self.config = config

    def next_pending_frame(self) -> dict[str, Any] | None:
        with connection_scope(str(self.config.db_path)) as conn:
            row = conn.execute(
                """
                SELECT id, image_path, attempt_count, door_cycle_id
                FROM pending_frames
                WHERE status = 'pending'
                ORDER BY id
                LIMIT 1
                """
            ).fetchone()
            return dict(row) if row else None

    @staticmethod
    def _resolve_produce(
        conn: Any,
        definition: ProduceDefinition,
    ) -> int:
        row = conn.execute(
            """
            SELECT id FROM produce_info
            WHERE name = ?
            ORDER BY id LIMIT 1
            """,
            (definition.name,),
        ).fetchone()
        if row:
            return int(row["id"])
        row = conn.execute(
            """
            SELECT id FROM produce_info
            WHERE name = ? AND category = ?
            ORDER BY id LIMIT 1
            """,
            (definition.name, definition.category),
        ).fetchone()
        if row:
            return int(row["id"])
        cursor = conn.execute(
            """
            INSERT INTO produce_info
                (name, category, shelf_life_days, unit, location)
            VALUES (?, ?, ?, ?, '本地库存')
            """,
            (
                definition.name,
                definition.category,
                definition.shelf_life_days,
                definition.unit,
            ),
        )
        return int(cursor.lastrowid)

    @staticmethod
    def _set_stock(
        conn: Any,
        produce_id: int,
        quantity: int,
        definition: ProduceDefinition,
    ) -> None:
        expire_date = (
            date.today() + timedelta(days=definition.shelf_life_days)
        ).isoformat()
        conn.execute(
            """
            INSERT INTO stock_summary
                (produce_id, current_qty, earliest_expire_date, last_updated)
            VALUES (?, ?, ?, datetime('now', 'localtime'))
            ON CONFLICT(produce_id) DO UPDATE SET
                current_qty = excluded.current_qty,
                earliest_expire_date = CASE
                    WHEN earliest_expire_date IS NULL OR earliest_expire_date = ''
                    THEN excluded.earliest_expire_date
                    ELSE earliest_expire_date
                END,
                last_updated = excluded.last_updated
            """,
            (produce_id, quantity, expire_date),
        )

    def _current_stock(self, conn: Any, produce_id: int) -> int:
        row = conn.execute(
            "SELECT COALESCE(current_qty, 0) AS qty FROM stock_summary WHERE produce_id = ?",
            (produce_id,),
        ).fetchone()
        return int(row["qty"]) if row else 0

    @staticmethod
    def _recognition_counts(conn: Any, frame_id: int) -> Counter[int]:
        rows = conn.execute(
            """
            SELECT produce_id, COUNT(*) AS quantity
            FROM inventory_log
            WHERE source_frame_id = ?
              AND COALESCE(bbox_json, '') <> ''
              AND produce_id IS NOT NULL
            GROUP BY produce_id
            """,
            (frame_id,),
        ).fetchall()
        return Counter({int(row["produce_id"]): int(row["quantity"]) for row in rows})

    @staticmethod
    def _previous_cycle_counts(conn: Any, cycle_id: int) -> Counter[int] | None:
        row = conn.execute(
            """
            SELECT frame_id
            FROM door_cycle
            WHERE id < ? AND status = 'completed' AND frame_id IS NOT NULL
            ORDER BY id DESC
            LIMIT 1
            """,
            (cycle_id,),
        ).fetchone()
        if row is None:
            return None
        return RecognitionRepository._recognition_counts(conn, int(row["frame_id"]))

    def _insert_movement(
        self,
        conn: Any,
        frame_id: int,
        produce_id: int,
        delta: int,
    ) -> int | None:
        if delta == 0:
            return None
        cursor = conn.execute(
            """
            INSERT INTO inventory_log
                (produce_id, action_type, quantity, sync_status,
                 source_frame_id, model_version)
            VALUES (?, ?, ?, 'local', ?, ?)
            """,
            (
                produce_id,
                "IN" if delta > 0 else "OUT",
                abs(delta),
                frame_id,
                self.config.model_version,
            ),
        )
        return int(cursor.lastrowid)

    def save_results(
        self,
        frame_id: int,
        source_image_path: str | Path,
        results: list[RecognitionResult],
    ) -> list[int]:
        log_ids: list[int] = []
        with connection_scope(str(self.config.db_path)) as conn:
            frame_row = conn.execute(
                "SELECT door_cycle_id FROM pending_frames WHERE id = ?",
                (frame_id,),
            ).fetchone()
            cycle_id = (
                int(frame_row["door_cycle_id"])
                if frame_row and frame_row["door_cycle_id"] is not None
                else None
            )
            frame_counts: Counter[int] = Counter()
            produce_defs: dict[int, ProduceDefinition] = {}
            for result in results:
                definition = self.config.produce_catalog[result.detection.species]
                produce_id = self._resolve_produce(conn, definition)
                frame_counts[produce_id] += 1
                produce_defs[produce_id] = definition
                bbox = {
                    "x1": result.detection.bbox[0],
                    "y1": result.detection.bbox[1],
                    "x2": result.detection.bbox[2],
                    "y2": result.detection.bbox[3],
                    "image_width": result.image_width,
                    "image_height": result.image_height,
                }
                cursor = conn.execute(
                    """
                    INSERT INTO inventory_log
                        (produce_id, action_type, quantity, freshness_level,
                         freshness_score, confidence, image_path, sync_status,
                         source_frame_id, detector_label,
                         detector_confidence, freshness_confidence, bbox_json,
                         freshness_probabilities_json, inference_latency_ms,
                         model_version)
                    VALUES (?, ?, 1, ?, ?, ?, ?, 'local', ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        produce_id,
                        self.config.inventory_action,
                        result.freshness.label,
                        result.freshness.score,
                        result.freshness.confidence,
                        str(result.crop_path),
                        frame_id,
                        result.detection.detector_label,
                        result.detection.confidence,
                        result.freshness.confidence,
                        json.dumps(bbox, ensure_ascii=False),
                        json.dumps(
                            result.freshness.probabilities,
                            ensure_ascii=False,
                        ),
                        result.inference_latency_ms,
                        self.config.model_version,
                    ),
                )
                log_ids.append(int(cursor.lastrowid))

            if cycle_id is None:
                # 兼容升级前遗留的帧；新门事件流程不再依赖周期帧差触发。
                for produce_id, quantity in frame_counts.items():
                    previous = self._current_stock(conn, produce_id)
                    self._set_stock(conn, produce_id, quantity, produce_defs[produce_id])
                    movement_id = self._insert_movement(
                        conn, frame_id, produce_id, quantity - previous
                    )
                    if movement_id is not None:
                        log_ids.append(movement_id)
            else:
                previous_counts = self._previous_cycle_counts(conn, cycle_id)
                cycle = conn.execute(
                    "SELECT retry_count FROM door_cycle WHERE id = ?",
                    (cycle_id,),
                ).fetchone()
                retry_count = int(cycle["retry_count"] or 0) if cycle else 0

                if not results and previous_counts and retry_count < 1:
                    conn.execute(
                        """
                        UPDATE pending_frames
                        SET status = 'discarded',
                            processed_at = datetime('now', 'localtime'),
                            last_error = '空识别结果，已请求自动复拍'
                        WHERE id = ?
                        """,
                        (frame_id,),
                    )
                    conn.execute(
                        """
                        UPDATE door_cycle
                        SET status = 'recapture_requested', retry_count = retry_count + 1,
                            frame_id = NULL, last_error = '空识别结果，正在自动复拍'
                        WHERE id = ? AND status = 'processing'
                        """,
                        (cycle_id,),
                    )
                    return log_ids

                # 解析完整目录，确保本次完全消失的品类也以数量 0 参与比较。
                for definition in self.config.produce_catalog.values():
                    produce_id = self._resolve_produce(conn, definition)
                    produce_defs[produce_id] = definition
                all_produce_ids = set(produce_defs) | set(frame_counts)
                if previous_counts is not None:
                    all_produce_ids |= set(previous_counts)

                is_baseline = previous_counts is None
                for produce_id in all_produce_ids:
                    quantity = int(frame_counts.get(produce_id, 0))
                    definition = produce_defs.get(produce_id)
                    if definition is None:
                        continue
                    self._set_stock(conn, produce_id, quantity, definition)
                    if not is_baseline:
                        movement_id = self._insert_movement(
                            conn,
                            frame_id,
                            produce_id,
                            quantity - int(previous_counts.get(produce_id, 0)),
                        )
                        if movement_id is not None:
                            log_ids.append(movement_id)

                conn.execute(
                    """
                    UPDATE door_cycle
                    SET status = 'completed', frame_id = ?, is_baseline = ?,
                        completed_at = datetime('now', 'localtime'), last_error = ''
                    WHERE id = ? AND status = 'processing'
                    """,
                    (frame_id, 1 if is_baseline else 0, cycle_id),
                )

            status = "processed" if results or cycle_id is not None else "discarded"
            message = "" if status == "processed" else "未检测到支持的果蔬目标"
            conn.execute(
                """
                UPDATE pending_frames
                SET status = ?, processed_at = datetime('now', 'localtime'),
                    last_error = ?
                WHERE id = ?
                """,
                (status, message, frame_id),
            )
        return log_ids

    def record_failure(self, frame_id: int, error: Exception) -> None:
        with connection_scope(str(self.config.db_path)) as conn:
            row = conn.execute(
                "SELECT attempt_count, door_cycle_id FROM pending_frames WHERE id = ?",
                (frame_id,),
            ).fetchone()
            attempts = int(row["attempt_count"] or 0) + 1 if row else 1
            status = "discarded" if attempts >= self.config.max_attempts else "pending"
            conn.execute(
                """
                UPDATE pending_frames
                SET attempt_count = ?, last_error = ?, status = ?,
                    processed_at = CASE WHEN ? = 'discarded'
                        THEN datetime('now', 'localtime') ELSE processed_at END
                WHERE id = ?
                """,
                (attempts, str(error)[:500], status, status, frame_id),
            )
            if (
                status == "discarded"
                and row
                and row["door_cycle_id"] is not None
            ):
                conn.execute(
                    """
                    UPDATE door_cycle
                    SET status = 'failed', completed_at = datetime('now', 'localtime'),
                        last_error = ?
                    WHERE id = ?
                    """,
                    (str(error)[:500], int(row["door_cycle_id"])),
                )

