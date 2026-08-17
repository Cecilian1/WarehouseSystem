"""Retention-based cleanup for captured frame records and image files."""

from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from backend.common.db import connection_scope

logger = logging.getLogger("frame_cleanup")


@dataclass(frozen=True)
class FrameRetentionPolicy:
    completed_retention_days: int = 7
    pending_retention_days: int = 7
    max_completed_frames: int = 1000
    max_pending_frames: int = 1000

    def __post_init__(self) -> None:
        values = (
            self.completed_retention_days,
            self.pending_retention_days,
            self.max_completed_frames,
            self.max_pending_frames,
        )
        if any(value < 0 for value in values):
            raise ValueError("图片保留天数和数量不能小于 0")


@dataclass(frozen=True)
class FrameCleanupResult:
    records_deleted: int = 0
    files_deleted: int = 0
    files_missing: int = 0
    files_preserved: int = 0
    unsafe_paths: int = 0
    failures: int = 0


class FrameRetentionCleaner:
    """Remove stale/capped frame rows and, optionally, their local files."""

    _COMPLETED_STATUSES = frozenset({"processed", "discarded"})

    def __init__(
        self,
        db_path: str | Path,
        policy: FrameRetentionPolicy,
        frame_root: str | Path | None = None,
        latest_frame_name: str = "latest.jpg",
    ) -> None:
        self.db_path = str(db_path)
        self.policy = policy
        self.frame_root = Path(frame_root).resolve() if frame_root else None
        self.latest_frame_name = Path(latest_frame_name).name

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).replace("/", "-").strip())
        except ValueError:
            return None

    def _is_candidate(
        self,
        row: dict[str, Any],
        rank: int,
        now: datetime,
    ) -> bool:
        # Keep one high-water row per group. The Windows incremental sync uses
        # MAX(id) to detect database rollback and would otherwise re-import
        # already-cleaned board rows after a table became empty.
        if rank == 1:
            return False
        status = str(row.get("status") or "")
        created_at = self._parse_datetime(row.get("created_at"))
        if status == "pending":
            retention_days = self.policy.pending_retention_days
            max_frames = self.policy.max_pending_frames
        elif status in self._COMPLETED_STATUSES:
            retention_days = self.policy.completed_retention_days
            max_frames = self.policy.max_completed_frames
        else:
            return False

        expired = bool(
            retention_days
            and created_at
            and created_at < now - timedelta(days=retention_days)
        )
        over_limit = bool(max_frames and rank > max_frames)
        return expired or over_limit

    def _candidate_rows(self, now: datetime) -> list[dict[str, Any]]:
        with connection_scope(self.db_path) as conn:
            rows = [
                dict(row)
                for row in conn.execute(
                    """
                    SELECT id, image_path, status, created_at
                    FROM pending_frames
                    ORDER BY created_at DESC, id DESC
                    """
                ).fetchall()
            ]

        ranks = {"pending": 0, "completed": 0}
        candidates: list[dict[str, Any]] = []
        for row in rows:
            status = str(row.get("status") or "")
            group = (
                "pending"
                if status == "pending"
                else "completed"
                if status in self._COMPLETED_STATUSES
                else ""
            )
            if not group:
                continue
            ranks[group] += 1
            if self._is_candidate(row, ranks[group], now):
                candidates.append(row)
        return candidates

    def _protected_image_paths(self) -> set[Path]:
        if self.frame_root is None:
            return set()
        with connection_scope(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT DISTINCT image_path
                FROM inventory_log
                WHERE image_path IS NOT NULL AND image_path != ''
                """
            ).fetchall()
        return {Path(str(row["image_path"])).resolve() for row in rows}

    def cleanup(self, now: datetime | None = None) -> FrameCleanupResult:
        cleanup_time = now or datetime.now()
        candidates = self._candidate_rows(cleanup_time)
        if not candidates:
            return FrameCleanupResult()

        protected_paths = self._protected_image_paths()
        removable_ids: list[int] = []
        files_deleted = 0
        files_missing = 0
        files_preserved = 0
        unsafe_paths = 0
        failures = 0

        for row in candidates:
            if self.frame_root is None:
                removable_ids.append(int(row["id"]))
                continue

            image_path = Path(str(row.get("image_path") or ""))
            resolved_path = image_path.resolve()
            try:
                resolved_path.relative_to(self.frame_root)
            except ValueError:
                unsafe_paths += 1
                logger.warning("跳过图片目录之外的路径: %s", resolved_path)
                continue

            if (
                resolved_path.name == self.latest_frame_name
                or resolved_path in protected_paths
            ):
                files_preserved += 1
                removable_ids.append(int(row["id"]))
                continue

            try:
                if resolved_path.is_file():
                    resolved_path.unlink()
                    files_deleted += 1
                else:
                    files_missing += 1
                removable_ids.append(int(row["id"]))
            except OSError:
                failures += 1
                logger.exception("删除过期图片失败，保留数据库记录: %s", resolved_path)

        records_deleted = 0
        if removable_ids:
            with connection_scope(self.db_path) as conn:
                cursor = conn.executemany(
                    "DELETE FROM pending_frames WHERE id = ?",
                    ((frame_id,) for frame_id in removable_ids),
                )
                records_deleted = max(0, cursor.rowcount)

        result = FrameCleanupResult(
            records_deleted=records_deleted,
            files_deleted=files_deleted,
            files_missing=files_missing,
            files_preserved=files_preserved,
            unsafe_paths=unsafe_paths,
            failures=failures,
        )
        logger.info("图片定期清理完成: %s", result)
        return result


def main() -> None:
    parser = argparse.ArgumentParser(description="清理芯鲜管家历史图片及数据库记录")
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--frame-root")
    parser.add_argument("--latest-frame-name", default="latest.jpg")
    parser.add_argument("--completed-retention-days", type=int, default=7)
    parser.add_argument("--pending-retention-days", type=int, default=7)
    parser.add_argument("--max-completed-frames", type=int, default=1000)
    parser.add_argument("--max-pending-frames", type=int, default=1000)
    args = parser.parse_args()

    from backend.common.init_db import init_db

    init_db(args.db_path)
    cleaner = FrameRetentionCleaner(
        db_path=args.db_path,
        frame_root=args.frame_root,
        latest_frame_name=args.latest_frame_name,
        policy=FrameRetentionPolicy(
            completed_retention_days=args.completed_retention_days,
            pending_retention_days=args.pending_retention_days,
            max_completed_frames=args.max_completed_frames,
            max_pending_frames=args.max_pending_frames,
        ),
    )
    print(cleaner.cleanup())


if __name__ == "__main__":
    main()
