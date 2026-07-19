"""Parquet-backed persistence (Phase 1) — repository pattern.

Tracking data is partitioned by game and period (the natural access
pattern: replay one game/period at a time), events by game only. The rest
of the pipeline never touches the filesystem directly; it depends on this
repository, so the storage backend can be swapped without touching callers.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .schema import (
    EVENT_COLUMNS,
    TRACKING_COLUMNS,
    validate_events,
    validate_tracking,
)


class ParquetRepository:
    """Stores canonical tracking and event dataframes as partitioned Parquet."""

    def __init__(self, root: Path | str):
        self._root = Path(root)
        self._tracking_dir = self._root / "tracking"
        self._events_dir = self._root / "events"

    def save_tracking(self, df: pd.DataFrame) -> None:
        validated = validate_tracking(df)
        validated.to_parquet(
            self._tracking_dir, partition_cols=["game_id", "period"], index=False
        )

    def save_events(self, df: pd.DataFrame) -> None:
        validated = validate_events(df)
        validated.to_parquet(
            self._events_dir, partition_cols=["game_id"], index=False
        )

    def load_tracking(
        self, game_id: str | None = None, period: int | None = None
    ) -> pd.DataFrame:
        filters = []
        if game_id is not None:
            filters.append(("game_id", "==", game_id))
        if period is not None:
            filters.append(("period", "==", period))
        df = pd.read_parquet(self._tracking_dir, filters=filters or None)
        return self._restore(df, TRACKING_COLUMNS, ["game_id", "frame_id", "entity_id"])

    def load_events(self, game_id: str | None = None) -> pd.DataFrame:
        filters = [("game_id", "==", game_id)] if game_id is not None else None
        df = pd.read_parquet(self._events_dir, filters=filters)
        return self._restore(df, EVENT_COLUMNS, ["game_id", "frame_id"])

    def list_games(self) -> list[str]:
        if not self._tracking_dir.exists():
            return []
        return sorted(
            p.name.removeprefix("game_id=")
            for p in self._tracking_dir.iterdir()
            if p.is_dir() and p.name.startswith("game_id=")
        )

    @staticmethod
    def _restore(
        df: pd.DataFrame, schema: dict[str, str], sort_by: list[str]
    ) -> pd.DataFrame:
        # Partition columns come back as dictionary-encoded strings; restore
        # canonical dtypes and column order.
        out = df[list(schema)].astype(schema)
        return out.sort_values(sort_by, ignore_index=True)
