"""Canonical dataframe schemas and validation.

Tracking data is long-format: one row per (frame, entity). Events are one
row per discrete event. Every layer downstream of ingestion assumes these
schemas, so validation happens once at the boundary (fail fast) instead of
defensively everywhere.
"""

from __future__ import annotations

import pandas as pd

from ..domain import EventType, Position, Team

TRACKING_COLUMNS: dict[str, str] = {
    "game_id": "str",
    "period": "int64",
    "frame_id": "int64",
    "timestamp": "float64",
    "entity_id": "str",
    "team": "str",
    "position": "str",
    "x": "float64",
    "y": "float64",
}

EVENT_COLUMNS: dict[str, str] = {
    "game_id": "str",
    "frame_id": "int64",
    "event_type": "str",
    "team": "str",
    "player_id": "str",
}

_VALID_TEAMS = {Team.HOME.value, Team.AWAY.value, "none"}
_VALID_POSITIONS = {p.value for p in Position}
_VALID_EVENTS = {e.value for e in EventType}


class SchemaError(ValueError):
    """Raised when a dataframe does not conform to a canonical schema."""


def _require_columns(df: pd.DataFrame, required: dict[str, str], kind: str) -> None:
    missing = sorted(set(required) - set(df.columns))
    if missing:
        raise SchemaError(f"{kind} data is missing columns: {missing}")


def validate_tracking(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and coerce a tracking dataframe to the canonical schema.

    Returns a copy with canonical dtypes and columns ordered per schema.
    """
    _require_columns(df, TRACKING_COLUMNS, "tracking")
    out = df[list(TRACKING_COLUMNS)].astype(TRACKING_COLUMNS)

    if out[["x", "y", "frame_id", "timestamp"]].isna().any().any():
        raise SchemaError("tracking data contains nulls in x/y/frame_id/timestamp")

    bad_teams = set(out["team"].unique()) - _VALID_TEAMS
    if bad_teams:
        raise SchemaError(f"tracking data has invalid team values: {sorted(bad_teams)}")

    bad_pos = set(out["position"].unique()) - _VALID_POSITIONS
    if bad_pos:
        raise SchemaError(f"tracking data has invalid positions: {sorted(bad_pos)}")

    puck_mismatch = (out["position"] == Position.PUCK.value) != (out["team"] == "none")
    if puck_mismatch.any():
        raise SchemaError("rows must have team='none' iff position='puck'")

    return out.sort_values(["game_id", "frame_id", "entity_id"], ignore_index=True)


def validate_events(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and coerce an events dataframe to the canonical schema."""
    _require_columns(df, EVENT_COLUMNS, "event")
    out = df[list(EVENT_COLUMNS)].astype(EVENT_COLUMNS)

    bad_events = set(out["event_type"].unique()) - _VALID_EVENTS
    if bad_events:
        raise SchemaError(f"event data has invalid event types: {sorted(bad_events)}")

    return out.sort_values(["game_id", "frame_id"], ignore_index=True)
