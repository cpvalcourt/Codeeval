"""Coordinate and direction normalization (Phase 1).

Two adapters bring arbitrary tracking feeds into the canonical frame:

- :class:`CoordinateNormalizer` — affine transform from a source coordinate
  system (e.g. Big Data Cup's 0..200 x 0..85 ft) onto the canonical
  [-100, 100] x [-42.5, 42.5] rink.
- :class:`DirectionNormalizer` — flips periods so the team of interest
  always attacks toward positive x, regardless of which end it defended.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import pandas as pd

from ..config import RinkConfig
from ..domain import Team


@dataclass(frozen=True)
class SourceCoordinateSystem:
    """Axis-aligned extent of the source feed's coordinates."""

    x_min: float
    x_max: float
    y_min: float
    y_max: float

    def __post_init__(self) -> None:
        if self.x_max <= self.x_min or self.y_max <= self.y_min:
            raise ValueError("source coordinate extents must have positive size")


#: Stathletes Big Data Cup feeds: origin at a corner, feet.
BIG_DATA_CUP = SourceCoordinateSystem(x_min=0.0, x_max=200.0, y_min=0.0, y_max=85.0)


class CoordinateNormalizer:
    """Affine map from a source coordinate system to the canonical rink."""

    def __init__(self, source: SourceCoordinateSystem, rink: RinkConfig | None = None):
        self._source = source
        self._rink = rink or RinkConfig()

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return a copy of ``df`` with x/y mapped onto the canonical rink."""
        src, rink = self._source, self._rink
        out = df.copy()
        sx = (rink.x_max - rink.x_min) / (src.x_max - src.x_min)
        sy = (rink.y_max - rink.y_min) / (src.y_max - src.y_min)
        out["x"] = (out["x"] - src.x_min) * sx + rink.x_min
        out["y"] = (out["y"] - src.y_min) * sy + rink.y_min
        return out


class DirectionNormalizer:
    """Flip frames so a reference team always attacks toward positive x.

    ``attacking_right`` maps period number -> whether the reference team
    already attacks toward positive x in that period. Periods where it does
    not are rotated 180 degrees about center ice (x -> -x, y -> -y), which
    preserves all relative geometry.
    """

    def __init__(self, attacking_right: Mapping[int, bool]):
        self._attacking_right = dict(attacking_right)

    @classmethod
    def infer(
        cls, tracking: pd.DataFrame, reference_team: Team
    ) -> "DirectionNormalizer":
        """Infer per-period attacking direction from mean skater position.

        Heuristic: within a period, the reference team's skaters spend more
        time in the half they attack (offensive-zone pressure outweighs
        defensive-zone time for the side that carries play there). This is
        the standard bootstrap when the feed lacks explicit side metadata;
        feeds that carry side metadata should construct the normalizer
        directly instead.
        """
        team_rows = tracking[tracking["team"] == reference_team.value]
        if team_rows.empty:
            raise ValueError(f"no rows for reference team {reference_team.value!r}")
        mapping = {
            int(period): bool(group["x"].mean() > 0.0)
            for period, group in team_rows.groupby("period")
        }
        return cls(mapping)

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return a copy with periods flipped so the reference team attacks +x."""
        unknown = sorted(int(p) for p in set(df["period"].unique()) - set(self._attacking_right))
        if unknown:
            raise ValueError(f"no attacking direction configured for periods {unknown}")
        out = df.copy()
        flip = ~out["period"].map(self._attacking_right).astype(bool)
        out.loc[flip, ["x", "y"]] = -out.loc[flip, ["x", "y"]]
        return out
