from __future__ import annotations

import json
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
                SELECT id, image_path, attempt_count
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
            VALUES (?, ?, ?, ?, 'AI识别区')
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
    def _update_stock(
        conn: Any,
        produce_id: int,
        action: str,
        definition: ProduceDefinition,
    ) -> None:
        if action == "OUT":
            conn.execute(
                """
                UPDATE stock_summary
                SET current_qty = MAX(0, COALESCE(current_qty, 0) - 1),
                    last_updated = datetime('now', 'localtime')
                WHERE produce_id = ?
                """,
                (produce_id,),
            )
            return
        expire_date = (
            date.today() + timedelta(days=definition.shelf_life_days)
        ).isoformat()
        conn.execute(
            """
            INSERT INTO stock_summary
                (produce_id, current_qty, earliest_expire_date, last_updated)
            VALUES (?, 1, ?, datetime('now', 'localtime'))
            ON CONFLICT(produce_id) DO UPDATE SET
                current_qty = COALESCE(current_qty, 0) + 1,
                earliest_expire_date = CASE
                    WHEN earliest_expire_date IS NULL OR earliest_expire_date = ''
                    THEN excluded.earliest_expire_date
                    ELSE earliest_expire_date
                END,
                last_updated = excluded.last_updated
            """,
            (produce_id, expire_date),
        )

    def save_results(
        self,
        frame_id: int,
        source_image_path: str | Path,
        results: list[RecognitionResult],
    ) -> list[int]:
        log_ids: list[int] = []
        with connection_scope(str(self.config.db_path)) as conn:
            for result in results:
                definition = self.config.produce_catalog[result.detection.species]
                produce_id = self._resolve_produce(conn, definition)
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
                if self.config.update_stock_summary:
                    self._update_stock(
                        conn,
                        produce_id,
                        self.config.inventory_action,
                        definition,
                    )

            status = "processed" if results else "discarded"
            message = "" if results else "未检测到支持的果蔬目标"
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
                "SELECT attempt_count FROM pending_frames WHERE id = ?",
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

