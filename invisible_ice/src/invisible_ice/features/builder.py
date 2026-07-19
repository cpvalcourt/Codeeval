"""Per-frame feature assembly (Phase 2) — composite/pipeline pattern.

Each :class:`FeatureExtractor` turns a :class:`FeatureContext` into a
per-frame dataframe keyed by ``frame_id``; the :class:`FrameFeatureBuilder`
composes any number of extractors into a single model-ready feature
matrix. New features are added by writing a new extractor, not by editing
the builder.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

import numpy as np
import pandas as pd

from ..config import LaneConfig, RinkConfig
from ..domain import Position, Team
from .geometry import angle_to_target
from .lanes import compute_lane_features
from .pressure import compute_pressure
from .royal_road import flag_royal_road


@dataclass
class FeatureContext:
    """Everything extractors may need for one game's worth of frames.

    ``tracking`` must already carry kinematic columns (see
    :func:`invisible_ice.features.kinematics.add_kinematics`).
    ``carrier_by_frame`` maps frame_id -> controlling entity_id (None when
    the puck is loose), typically from the possession state machine.
    """

    tracking: pd.DataFrame
    attacking_team: Team
    carrier_by_frame: pd.Series
    rink: RinkConfig = field(default_factory=RinkConfig)


class FeatureExtractor(Protocol):
    def transform(self, ctx: FeatureContext) -> pd.DataFrame:
        """Return a dataframe with a frame_id column plus feature columns."""
        ...


class CarrierFeatures:
    """State of the puck carrier (falls back to the puck itself when loose)."""

    columns = ["carrier_dist_to_net", "carrier_angle_to_net", "carrier_speed", "carrier_x"]

    def transform(self, ctx: FeatureContext) -> pd.DataFrame:
        net = np.array(ctx.rink.attacking_net)
        puck = ctx.tracking[ctx.tracking["position"] == Position.PUCK.value]
        by_entity_frame = ctx.tracking.set_index(["frame_id", "entity_id"])

        records = []
        for row in puck.itertuples(index=False):
            carrier_id = ctx.carrier_by_frame.get(row.frame_id)
            subject = row
            if carrier_id is not None and (row.frame_id, carrier_id) in by_entity_frame.index:
                subject = by_entity_frame.loc[(row.frame_id, carrier_id)]
            xy = np.array([subject.x, subject.y])
            records.append(
                {
                    "frame_id": int(row.frame_id),
                    "carrier_dist_to_net": float(np.linalg.norm(net - xy)),
                    "carrier_angle_to_net": abs(angle_to_target(xy, net)),
                    "carrier_speed": float(getattr(subject, "speed", 0.0)),
                    "carrier_x": float(subject.x),
                }
            )
        return pd.DataFrame.from_records(records)


class PressureFeatures:
    """Pressure on the carrier plus team-wide defensive spacing."""

    columns = ["carrier_pressure_dist", "carrier_gap_closure", "mean_defender_gap"]

    def transform(self, ctx: FeatureContext) -> pd.DataFrame:
        pressure = compute_pressure(ctx.tracking, ctx.attacking_team)
        finite = pressure.replace(np.inf, np.nan)

        records = []
        for frame_id, group in finite.groupby("frame_id"):
            carrier_id = ctx.carrier_by_frame.get(frame_id)
            carrier_rows = group[group["entity_id"] == carrier_id]
            if carrier_rows.empty:
                dist, closure = np.nan, 0.0
            else:
                dist = float(carrier_rows["nearest_defender_dist"].iloc[0])
                closure = float(carrier_rows["gap_closure_rate"].iloc[0])
            records.append(
                {
                    "frame_id": int(frame_id),
                    "carrier_pressure_dist": dist,
                    "carrier_gap_closure": closure,
                    "mean_defender_gap": float(group["nearest_defender_dist"].mean()),
                }
            )
        out = pd.DataFrame.from_records(records)
        # A frame with no measurable pressure = maximal cushion, capped.
        return out.fillna({"carrier_pressure_dist": 60.0, "mean_defender_gap": 60.0})


class LaneFeatures:
    columns = ["best_lane_openness", "mean_lane_openness", "n_open_lanes"]

    def __init__(self, config: LaneConfig | None = None):
        self._config = config or LaneConfig()

    def transform(self, ctx: FeatureContext) -> pd.DataFrame:
        return compute_lane_features(
            ctx.tracking, ctx.attacking_team, ctx.carrier_by_frame, self._config
        )


class RoyalRoadFeatures:
    columns = ["royal_road_crossing", "royal_road_recent"]

    def transform(self, ctx: FeatureContext) -> pd.DataFrame:
        flags = flag_royal_road(ctx.tracking, ctx.rink)
        flags["royal_road_crossing"] = flags["royal_road_crossing"].astype(float)
        flags["royal_road_recent"] = flags["royal_road_recent"].astype(float)
        return flags


def default_extractors() -> list[FeatureExtractor]:
    return [CarrierFeatures(), PressureFeatures(), LaneFeatures(), RoyalRoadFeatures()]


class FrameFeatureBuilder:
    """Composes extractors into one per-frame feature matrix."""

    def __init__(self, extractors: list[FeatureExtractor] | None = None):
        self._extractors = extractors if extractors is not None else default_extractors()

    @property
    def feature_names(self) -> list[str]:
        return [c for ex in self._extractors for c in ex.columns]

    def build(self, ctx: FeatureContext) -> pd.DataFrame:
        """Feature matrix with one row per frame, columns = feature_names."""
        frames = ctx.tracking[["frame_id"]].drop_duplicates().sort_values("frame_id")
        out = frames.reset_index(drop=True)
        for extractor in self._extractors:
            part = extractor.transform(ctx)
            out = out.merge(part, on="frame_id", how="left")
        return out.fillna(0.0)
