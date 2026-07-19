"""Phase 4 serialization bridge: engine outputs -> browser payloads.

Converts :class:`~invisible_ice.pipeline.PossessionAnalysis` results into a
compact, versioned JSON structure the frontend replays. Design choices:

- **Structure-of-arrays**: per possession, one shared ``frames`` axis with
  per-entity ``x``/``y`` arrays indexed [entity][frame] — smaller and
  faster to decode than per-frame objects.
- **Quantization**: coordinates to 0.1 ft, probabilities to 4 decimals.
  Tracking noise is far above 0.1 ft, so this is lossless in practice and
  cuts payload size roughly in half before gzip.
- **Versioned envelope**: the frontend refuses payloads whose version it
  does not understand, so the wire format can evolve safely.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .config import RinkConfig
from .pipeline import PossessionAnalysis

PAYLOAD_VERSION = 1

_COORD_DECIMALS = 1
_PROB_DECIMALS = 4
_EPV_SERIES = ["epv", "xg", "p_shoot", "p_pass", "p_keep", "p_turnover"]


def possession_payload(
    analysis: PossessionAnalysis, tracking: pd.DataFrame
) -> dict:
    """Serialize one possession to a JSON-ready dict.

    ``tracking`` is the game's canonical tracking data; the possession's
    span is sliced out here so callers pass the same frame everywhere.
    """
    span = analysis.possession
    window = tracking[
        tracking["frame_id"].between(span.start_frame, span.end_frame)
    ].sort_values(["frame_id", "entity_id"])

    frame_ids = sorted(window["frame_id"].unique().tolist())
    epv = analysis.epv.sort_values("frame_id")
    if epv["frame_id"].tolist() != frame_ids:
        raise ValueError(
            f"EPV frames do not align with tracking frames for possession "
            f"{span.start_frame}-{span.end_frame}"
        )

    entities = (
        window[["entity_id", "team", "position"]]
        .drop_duplicates("entity_id")
        .sort_values("entity_id")
    )
    xs, ys = [], []
    for entity_id in entities["entity_id"]:
        rows = window[window["entity_id"] == entity_id].set_index("frame_id")
        if len(rows) != len(frame_ids):
            raise ValueError(f"entity {entity_id!r} is missing frames in possession")
        xs.append([round(float(v), _COORD_DECIMALS) for v in rows.loc[frame_ids, "x"]])
        ys.append([round(float(v), _COORD_DECIMALS) for v in rows.loc[frame_ids, "y"]])

    return {
        "team": span.team.value,
        "startFrame": int(span.start_frame),
        "endFrame": int(span.end_frame),
        "entities": [
            {"id": r.entity_id, "team": r.team, "position": r.position}
            for r in entities.itertuples(index=False)
        ],
        "frames": [int(f) for f in frame_ids],
        "x": xs,
        "y": ys,
        "series": {
            name: [round(float(v), _PROB_DECIMALS) for v in epv[name]]
            for name in _EPV_SERIES
        },
        "attribution": [
            {
                "playerId": r.player_id,
                "onPuck": round(float(r.epv_added_on_puck), _PROB_DECIMALS),
                "offPuck": round(float(r.epv_added_off_puck), _PROB_DECIMALS),
                "total": round(float(r.epv_added_total), _PROB_DECIMALS),
            }
            for r in analysis.attribution.itertuples(index=False)
        ],
    }


def game_payload(
    game_id: str,
    tracking: pd.DataFrame,
    analyses: list[PossessionAnalysis],
    frame_rate: float = 30.0,
    rink: RinkConfig | None = None,
) -> dict:
    """Serialize a whole game's analyses into one payload."""
    rink = rink or RinkConfig()
    if not analyses:
        raise ValueError("game_payload requires at least one possession analysis")
    return {
        "version": PAYLOAD_VERSION,
        "gameId": game_id,
        "frameRate": frame_rate,
        "rink": {
            "xMin": rink.x_min,
            "xMax": rink.x_max,
            "yMin": rink.y_min,
            "yMax": rink.y_max,
            "goalLineX": rink.goal_line_x,
            "blueLineX": rink.blue_line_x,
        },
        "possessions": [
            possession_payload(analysis, tracking)
            for analysis in sorted(analyses, key=lambda a: a.possession.start_frame)
        ],
    }


def write_game_json(payload: dict, path: Path | str) -> Path:
    """Write a payload as minified JSON (gzip at the edge does the rest)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, separators=(",", ":")))
    return path
