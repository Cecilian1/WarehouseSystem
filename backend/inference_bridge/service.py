from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from backend.ai_service.config import AIServiceConfig
from backend.ai_service.contracts import Detection, FreshnessPrediction, RecognitionResult
from backend.ai_service.result_writer import RecognitionRepository
from backend.common.db import connection_scope
from backend.inference_bridge.config import BridgeConfig, species_from_produce_name


logger = logging.getLogger("inference_bridge")

WORKER_ID = "inference-bridge"
JobStatus = Literal["waiting", "done", "failed"]
OutcomeKind = Literal["detections", "empty", "failure", "timeout"]


@dataclass(frozen=True)
class InferenceJob:
    main_frame_id: int
    door_cycle_id: int | None
    worker_frame_id: int
    image_path: str
    status: str


@dataclass(frozen=True)
class WorkerOutcome:
    kind: OutcomeKind
    detections: list[RecognitionResult]
    error: str = ""


def _as_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    return int(value)


def _as_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    return float(value)


def _parse_bbox(raw: str | None) -> tuple[tuple[int, int, int, int], int, int]:
    if not raw:
        return (0, 0, 0, 0), 0, 0
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return (0, 0, 0, 0), 0, 0
    x1 = int(data.get("x1", 0))
    y1 = int(data.get("y1", 0))
    x2 = int(data.get("x2", x1))
    y2 = int(data.get("y2", y1))
    return (
        (x1, y1, x2, y2),
        int(data.get("image_width", 0) or 0),
        int(data.get("image_height", 0) or 0),
    )


def _parse_probabilities(raw: str | None) -> dict[str, float]:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return {str(key): float(value) for key, value in data.items()}


def detections_from_worker_rows(rows: list[Any]) -> list[RecognitionResult]:
    boxed = [row for row in rows if str(row["bbox_json"] or "").strip()]
    selected = boxed or [
        row
        for row in rows
        if str(row["action_type"] or "") == "IN" and _as_float(row["quantity"]) == 1
    ]
    results: list[RecognitionResult] = []
    for row in selected:
        species = species_from_produce_name(str(row["produce_name"] or ""))
        if species is None:
            logger.warning("工作库出现未识别品类，已忽略: %s", row["produce_name"])
            continue
        bbox, width, height = _parse_bbox(row["bbox_json"])
        results.append(
            RecognitionResult(
                detection=Detection(
                    bbox,
                    species,
                    str(row["detector_label"] or species),
                    _as_float(row["detector_confidence"] or row["confidence"]),
                ),
                freshness=FreshnessPrediction(
                    str(row["freshness_level"] or "unknown"),
                    _as_float(row["freshness_confidence"] or row["confidence"]),
                    _as_float(row["freshness_score"]),
                    _parse_probabilities(row["freshness_probabilities_json"]),
                    _as_float(row["inference_latency_ms"]),
                ),
                crop_path=Path(str(row["image_path"] or "")),
                image_width=width,
                image_height=height,
                inference_latency_ms=_as_float(row["inference_latency_ms"]),
            )
        )
    return results


class InferenceBridge:
    def __init__(self, config: BridgeConfig, sleep: Any = time.sleep):
        if config.main_db_path.resolve() == config.worker_db_path.resolve():
            raise ValueError("旧 NCNN 工作库不能与主库相同")
        self.config = config
        self.sleep = sleep
        self.repository = RecognitionRepository(
            AIServiceConfig(
                db_path=config.main_db_path,
                detector_model=Path("unused.onnx"),
                freshness_model=Path("unused.onnx"),
                crop_dir=Path("/data/warehousekeeper/frames/crops"),
                detector_confidence=0.35,
                detector_iou=0.45,
                detector_image_size=640,
                bbox_padding_ratio=0.05,
                poll_interval_sec=config.poll_interval_sec,
                max_attempts=config.max_attempts,
                onnx_threads=1,
                inventory_action="IN",
                update_stock_summary=False,
                model_version=config.model_version,
                produce_catalog=config.produce_catalog,
            )
        )

    def process_once(self) -> bool:
        job = self.next_job()
        if job is None:
            return False
        outcome = self.wait_for_worker(job)
        self.apply_outcome(job, outcome)
        return True

    def next_job(self) -> InferenceJob | None:
        waiting = self._load_waiting_job()
        if waiting is not None:
            return waiting
        frame = self.claim_next_frame()
        if frame is None:
            return None
        return self.ensure_worker_job(frame)

    def claim_next_frame(self) -> dict[str, Any] | None:
        stale = f"-{self.config.stale_claim_minutes} minutes"
        with connection_scope(str(self.config.main_db_path)) as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                """
                SELECT pf.id, pf.image_path, pf.door_cycle_id
                FROM pending_frames AS pf
                WHERE (
                        pf.status = 'pending'
                        OR (
                            pf.status = 'processing'
                            AND (
                                 pf.claimed_at IS NULL
                                 OR pf.claimed_at <= datetime('now', 'localtime', ?)
                            )
                        )
                      )
                  AND pf.door_cycle_id IS NOT NULL
                  AND EXISTS (
                        SELECT 1 FROM door_cycle AS dc
                        WHERE dc.id = pf.door_cycle_id
                          AND dc.status = 'processing'
                  )
                  AND NOT EXISTS (
                        SELECT 1 FROM inference_job
                        WHERE inference_job.main_frame_id = pf.id
                          AND inference_job.status = 'done'
                  )
                ORDER BY pf.id
                LIMIT 1
                """,
                (stale,),
            ).fetchone()
            if row is None:
                return None
            updated = conn.execute(
                """
                UPDATE pending_frames
                SET status = 'processing', claimed_by = ?,
                    claimed_at = datetime('now', 'localtime')
                WHERE id = ?
                  AND (
                       status = 'pending'
                       OR (
                            status = 'processing'
                            AND (
                                 claimed_at IS NULL
                                 OR claimed_at <= datetime('now', 'localtime', ?)
                            )
                       )
                  )
                  AND door_cycle_id IS NOT NULL
                  AND EXISTS (
                       SELECT 1 FROM door_cycle
                       WHERE door_cycle.id = pending_frames.door_cycle_id
                         AND door_cycle.status = 'processing'
                  )
                """,
                (WORKER_ID, int(row["id"]), stale),
            )
            if updated.rowcount != 1:
                return None
            return {
                "id": int(row["id"]),
                "image_path": str(row["image_path"]),
                "door_cycle_id": (
                    int(row["door_cycle_id"])
                    if row["door_cycle_id"] is not None
                    else None
                ),
            }

    def discard_legacy_pending_frames(self) -> int:
        """Discard pre-door-cycle frames so a restart cannot infer preview history."""
        with connection_scope(str(self.config.main_db_path)) as conn:
            updated = conn.execute(
                """
                UPDATE pending_frames
                SET status = 'discarded',
                    processed_at = datetime('now', 'localtime'),
                    last_error = '门周期模式已忽略升级前遗留帧',
                    claimed_by = NULL, claimed_at = NULL
                WHERE door_cycle_id IS NULL
                  AND status IN ('pending', 'processing')
                """
            )
            return max(0, updated.rowcount)

    def ensure_worker_job(self, frame: dict[str, Any]) -> InferenceJob:
        existing = self._job_for_frame(int(frame["id"]))
        if existing is not None and existing.status == "waiting" and existing.worker_frame_id:
            return existing
        worker_frame_id = self._insert_worker_frame(str(frame["image_path"]))
        with connection_scope(str(self.config.main_db_path)) as conn:
            conn.execute(
                """
                INSERT INTO inference_job
                    (main_frame_id, door_cycle_id, worker_frame_id, image_path, status)
                VALUES (?, ?, ?, ?, 'waiting')
                ON CONFLICT(main_frame_id) DO UPDATE SET
                    worker_frame_id = excluded.worker_frame_id,
                    image_path = excluded.image_path,
                    status = CASE
                        WHEN inference_job.status = 'done'
                        THEN 'done'
                        ELSE 'waiting'
                    END,
                    last_error = CASE
                        WHEN inference_job.status = 'done'
                        THEN inference_job.last_error
                        ELSE ''
                    END,
                    finished_at = CASE
                        WHEN inference_job.status = 'done'
                        THEN inference_job.finished_at
                        ELSE NULL
                    END
                """,
                (
                    int(frame["id"]),
                    frame["door_cycle_id"],
                    worker_frame_id,
                    str(frame["image_path"]),
                ),
            )
        job = self._job_for_frame(int(frame["id"]))
        if job is None:
            raise RuntimeError(f"主帧{frame['id']}未能登记 inference_job")
        return job

    def renew_lease(self, main_frame_id: int) -> bool:
        with connection_scope(str(self.config.main_db_path)) as conn:
            updated = conn.execute(
                """
                UPDATE pending_frames
                SET claimed_at = datetime('now', 'localtime')
                WHERE id = ? AND claimed_by = ? AND status = 'processing'
                """,
                (main_frame_id, WORKER_ID),
            )
            return updated.rowcount == 1

    def wait_for_worker(self, job: InferenceJob) -> WorkerOutcome:
        deadline = time.monotonic() + self.config.worker_timeout_sec
        next_lease_at = time.monotonic()
        while time.monotonic() < deadline:
            if time.monotonic() >= next_lease_at:
                self.renew_lease(job.main_frame_id)
                next_lease_at = time.monotonic() + self.config.lease_renew_sec
            outcome = self.read_worker_outcome(job.worker_frame_id)
            if outcome is not None:
                return outcome
            self.sleep(self.config.poll_interval_sec)
        return WorkerOutcome("timeout", [], "等待旧 NCNN 推理超时")

    def read_worker_outcome(self, worker_frame_id: int) -> WorkerOutcome | None:
        with connection_scope(str(self.config.worker_db_path)) as conn:
            frame = conn.execute(
                """
                SELECT status, attempt_count, last_error
                FROM pending_frames
                WHERE id = ?
                """,
                (worker_frame_id,),
            ).fetchone()
            if frame is None:
                return WorkerOutcome("failure", [], "工作库找不到对应帧")
            status = str(frame["status"] or "")
            attempt_count = _as_int(frame["attempt_count"])
            last_error = str(frame["last_error"] or "")
            if status in {"pending", "processing"}:
                return None
            if attempt_count >= 3:
                return WorkerOutcome(
                    "failure",
                    [],
                    last_error or "旧 NCNN 连续推理失败",
                )
            if status == "discarded" and attempt_count == 0:
                return WorkerOutcome("empty", [], last_error)
            if status == "discarded":
                return WorkerOutcome(
                    "failure",
                    [],
                    last_error or "旧 NCNN 推理失败",
                )
            detections = detections_from_worker_rows(
                list(
                    conn.execute(
                        """
                        SELECT l.action_type, l.quantity, l.freshness_level,
                               l.freshness_score, l.confidence, l.image_path,
                               l.detector_label, l.detector_confidence,
                               l.freshness_confidence, l.bbox_json,
                               l.freshness_probabilities_json,
                               l.inference_latency_ms, p.name AS produce_name
                        FROM inventory_log l
                        LEFT JOIN produce_info p ON p.id = l.produce_id
                        WHERE l.source_frame_id = ?
                        ORDER BY l.id
                        """,
                        (worker_frame_id,),
                    ).fetchall()
                )
            )
            return WorkerOutcome(
                "empty" if not detections else "detections",
                detections,
                last_error,
            )

    def apply_outcome(self, job: InferenceJob, outcome: WorkerOutcome) -> None:
        with connection_scope(str(self.config.main_db_path)) as conn:
            current = conn.execute(
                "SELECT status FROM inference_job WHERE main_frame_id = ?",
                (job.main_frame_id,),
            ).fetchone()
            if current and str(current["status"]) in {"done", "failed"}:
                return
            frame = conn.execute(
                """
                SELECT pf.door_cycle_id, dc.status AS cycle_status
                FROM pending_frames AS pf
                LEFT JOIN door_cycle AS dc ON dc.id = pf.door_cycle_id
                WHERE pf.id = ?
                """,
                (job.main_frame_id,),
            ).fetchone()
            if (
                frame
                and frame["door_cycle_id"] is not None
                and str(frame["cycle_status"] or "") != "processing"
            ):
                error = "门周期已结束，忽略遗留推理结果"
                conn.execute(
                    """
                    UPDATE pending_frames
                    SET status = 'discarded', last_error = ?,
                        processed_at = datetime('now', 'localtime'),
                        claimed_by = NULL, claimed_at = NULL
                    WHERE id = ?
                    """,
                    (error, job.main_frame_id),
                )
                self._finish_job(conn, job.main_frame_id, "failed", error)
                return
            if outcome.kind == "timeout":
                self.repository.record_failure_on_connection(
                    conn,
                    job.main_frame_id,
                    RuntimeError(outcome.error or "等待旧 NCNN 推理超时"),
                )
                self._finish_job(conn, job.main_frame_id, "failed", outcome.error)
                return
            if outcome.kind == "failure":
                self.repository.record_terminal_failure_on_connection(
                    conn,
                    job.main_frame_id,
                    RuntimeError(outcome.error or "旧 NCNN 推理失败"),
                )
                self._finish_job(conn, job.main_frame_id, "failed", outcome.error)
                return
            self.repository.save_results_on_connection(
                conn,
                job.main_frame_id,
                job.image_path,
                outcome.detections,
            )
            self._finish_job(conn, job.main_frame_id, "done", "")

    def _insert_worker_frame(self, image_path: str) -> int:
        with connection_scope(str(self.config.worker_db_path)) as conn:
            cursor = conn.execute(
                """
                INSERT INTO pending_frames (image_path, change_ratio, status)
                VALUES (?, 1.0, 'pending')
                """,
                (image_path,),
            )
            return int(cursor.lastrowid)

    def _load_waiting_job(self) -> InferenceJob | None:
        with connection_scope(str(self.config.main_db_path)) as conn:
            row = conn.execute(
                """
                SELECT main_frame_id, door_cycle_id, worker_frame_id,
                       image_path, status
                FROM inference_job
                WHERE status = 'waiting' AND worker_frame_id IS NOT NULL
                ORDER BY main_frame_id
                LIMIT 1
                """
            ).fetchone()
        return self._job_from_row(row)

    def _job_for_frame(self, main_frame_id: int) -> InferenceJob | None:
        with connection_scope(str(self.config.main_db_path)) as conn:
            row = conn.execute(
                """
                SELECT main_frame_id, door_cycle_id, worker_frame_id,
                       image_path, status
                FROM inference_job
                WHERE main_frame_id = ?
                """,
                (main_frame_id,),
            ).fetchone()
        return self._job_from_row(row)

    @staticmethod
    def _job_from_row(row: Any) -> InferenceJob | None:
        if row is None:
            return None
        worker_frame_id = row["worker_frame_id"]
        if worker_frame_id is None:
            return None
        return InferenceJob(
            main_frame_id=int(row["main_frame_id"]),
            door_cycle_id=(
                int(row["door_cycle_id"]) if row["door_cycle_id"] is not None else None
            ),
            worker_frame_id=int(worker_frame_id),
            image_path=str(row["image_path"]),
            status=str(row["status"]),
        )

    @staticmethod
    def _finish_job(
        conn: Any,
        main_frame_id: int,
        status: JobStatus,
        error: str,
    ) -> None:
        conn.execute(
            """
            UPDATE inference_job
            SET status = ?, last_error = ?,
                finished_at = datetime('now', 'localtime')
            WHERE main_frame_id = ?
            """,
            (status, (error or "")[:500], main_frame_id),
        )
