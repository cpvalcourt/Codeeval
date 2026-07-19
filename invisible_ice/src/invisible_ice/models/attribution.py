"""Micro-attribution engine (Phase 3) — strategy pattern.

Splits each frame-to-frame EPV change (delta EPV) among the attacking
skaters, separating on-puck credit (the carrier's share) from off-puck
credit (teammates whose movement changed the threat picture — e.g.
driving the net and dragging a defender out of a passing lane).

The division rule is a pluggable :class:`AttributionStrategy`; the
default :class:`ThreatDeltaAttribution` weights off-puck skaters by how
much their individual net-proximity threat changed in the direction of
the EPV swing.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..config import RinkConfig
from ..domain import Position, Team


@dataclass(frozen=True)
class AttributionFrame:
    """Inputs the strategy sees for one frame transition."""

    frame_id: int
    delta_epv: float
    carrier_id: str | None
    #: entity_id -> (x, y) this frame, attackers only.
    positions: dict[str, tuple[float, float]]
    #: entity_id -> (x, y) previous frame, attackers only.
    prev_positions: dict[str, tuple[float, float]]
    net: tuple[float, float]


class AttributionStrategy(ABC):
    @abstractmethod
    def attribute(self, frame: AttributionFrame) -> dict[str, float]:
        """Split ``frame.delta_epv`` across players; shares must sum to it."""


class ThreatDeltaAttribution(AttributionStrategy):
    """Carrier gets a fixed share; the rest follows off-puck threat change.

    A skater's *threat* is exp(-dist_to_net / scale). Off-puck credit for a
    positive (negative) EPV swing is distributed proportionally to positive
    (negative) threat changes; if no off-puck movement matches the swing's
    direction, the carrier absorbs everything.
    """

    def __init__(self, carrier_share: float = 0.6, threat_scale: float = 30.0):
        if not 0.0 <= carrier_share <= 1.0:
            raise ValueError("carrier_share must be in [0, 1]")
        self._carrier_share = carrier_share
        self._threat_scale = threat_scale

    def _threat(self, xy: tuple[float, float], net: tuple[float, float]) -> float:
        dist = float(np.hypot(xy[0] - net[0], xy[1] - net[1]))
        return float(np.exp(-dist / self._threat_scale))

    def attribute(self, frame: AttributionFrame) -> dict[str, float]:
        delta = frame.delta_epv
        if delta == 0.0 or not frame.positions:
            return {}

        deltas_threat = {
            pid: self._threat(xy, frame.net)
            - self._threat(frame.prev_positions.get(pid, xy), frame.net)
            for pid, xy in frame.positions.items()
        }
        off_puck = {
            pid: dt
            for pid, dt in deltas_threat.items()
            if pid != frame.carrier_id and np.sign(dt) == np.sign(delta) and dt != 0.0
        }

        shares: dict[str, float] = {}
        if frame.carrier_id is None:
            carrier_amount = 0.0
        elif off_puck:
            carrier_amount = self._carrier_share * delta
        else:
            carrier_amount = delta
        if frame.carrier_id is not None and carrier_amount != 0.0:
            shares[frame.carrier_id] = carrier_amount

        remainder = delta - carrier_amount
        if off_puck and remainder != 0.0:
            total = sum(abs(dt) for dt in off_puck.values())
            for pid, dt in off_puck.items():
                shares[pid] = shares.get(pid, 0.0) + remainder * abs(dt) / total
        elif remainder != 0.0:
            # No carrier and no aligned movement: spread evenly.
            per = remainder / len(frame.positions)
            for pid in frame.positions:
                shares[pid] = shares.get(pid, 0.0) + per
        return shares


class MicroAttributionEngine:
    """Aggregates per-frame attributions into per-player EPV-added totals."""

    def __init__(
        self,
        strategy: AttributionStrategy | None = None,
        rink: RinkConfig | None = None,
    ):
        self._strategy = strategy or ThreatDeltaAttribution()
        self._rink = rink or RinkConfig()

    def attribute_possession(
        self,
        epv: pd.DataFrame,
        tracking: pd.DataFrame,
        carrier_by_frame: pd.Series,
        attacking_team: Team,
    ) -> pd.DataFrame:
        """Per-player EPV added over one possession.

        ``epv`` is the EPVEngine output; ``tracking`` the possession's
        canonical tracking rows. Returns columns: player_id,
        epv_added_on_puck, epv_added_off_puck, epv_added_total.
        """
        attackers = tracking[
            (tracking["team"] == attacking_team.value)
            & (tracking["position"] == Position.SKATER.value)
        ]
        pos_by_frame: dict[int, dict[str, tuple[float, float]]] = {
            int(fid): {
                r.entity_id: (float(r.x), float(r.y))
                for r in group.itertuples(index=False)
            }
            for fid, group in attackers.groupby("frame_id")
        }

        on_puck: dict[str, float] = {}
        off_puck: dict[str, float] = {}
        ordered = epv.sort_values("frame_id").reset_index(drop=True)
        for i in range(1, len(ordered)):
            fid = int(ordered.loc[i, "frame_id"])
            prev_fid = int(ordered.loc[i - 1, "frame_id"])
            delta = float(ordered.loc[i, "epv"] - ordered.loc[i - 1, "epv"])
            carrier = carrier_by_frame.get(fid)
            frame = AttributionFrame(
                frame_id=fid,
                delta_epv=delta,
                carrier_id=carrier,
                positions=pos_by_frame.get(fid, {}),
                prev_positions=pos_by_frame.get(prev_fid, {}),
                net=self._rink.attacking_net,
            )
            for pid, share in self._strategy.attribute(frame).items():
                bucket = on_puck if pid == carrier else off_puck
                bucket[pid] = bucket.get(pid, 0.0) + share

        players = sorted(set(on_puck) | set(off_puck))
        return pd.DataFrame(
            {
                "player_id": players,
                "epv_added_on_puck": [on_puck.get(p, 0.0) for p in players],
                "epv_added_off_puck": [off_puck.get(p, 0.0) for p in players],
            }
        ).assign(
            epv_added_total=lambda df: df["epv_added_on_puck"] + df["epv_added_off_puck"]
        )
