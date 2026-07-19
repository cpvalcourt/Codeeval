"""Defensive pressure and gap control features (Phase 2).

For each attacking skater on each frame: distance to the nearest defending
skater, and the *gap closure rate* (defensive cushion) — the time
derivative of that gap. Negative closure means the defense is tightening.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..domain import Position, Team


def compute_pressure(tracking: pd.DataFrame, attacking_team: Team) -> pd.DataFrame:
    """Per (frame_id, attacker) pressure features for a single game.

    Returns columns: frame_id, entity_id, nearest_defender_id,
    nearest_defender_dist, gap_closure_rate. Goalies are excluded from the
    defender pool (they defend the net, not the carrier).
    """
    skaters = tracking[tracking["position"] == Position.SKATER.value]
    attackers = skaters[skaters["team"] == attacking_team.value]
    defenders = skaters[skaters["team"] == attacking_team.opponent.value]

    records: list[dict] = []
    defender_groups = {fid: g for fid, g in defenders.groupby("frame_id")}
    for frame_id, frame_attackers in attackers.groupby("frame_id"):
        frame_defenders = defender_groups.get(frame_id)
        for row in frame_attackers.itertuples(index=False):
            if frame_defenders is None or frame_defenders.empty:
                records.append(
                    {
                        "frame_id": int(frame_id),
                        "entity_id": row.entity_id,
                        "nearest_defender_id": None,
                        "nearest_defender_dist": np.inf,
                    }
                )
                continue
            dists = np.hypot(
                frame_defenders["x"].to_numpy() - row.x,
                frame_defenders["y"].to_numpy() - row.y,
            )
            j = int(np.argmin(dists))
            records.append(
                {
                    "frame_id": int(frame_id),
                    "entity_id": row.entity_id,
                    "nearest_defender_id": frame_defenders.iloc[j]["entity_id"],
                    "nearest_defender_dist": float(dists[j]),
                }
            )

    out = pd.DataFrame.from_records(records)
    out["gap_closure_rate"] = 0.0

    timestamps = (
        tracking[["frame_id", "timestamp"]]
        .drop_duplicates("frame_id")
        .set_index("frame_id")["timestamp"]
    )
    for _, idx in out.groupby("entity_id", sort=False).indices.items():
        if len(idx) < 2:
            continue
        gaps = out.loc[idx, "nearest_defender_dist"].to_numpy()
        t = timestamps.loc[out.loc[idx, "frame_id"]].to_numpy()
        finite = np.isfinite(gaps)
        if finite.sum() >= 2:
            rates = np.zeros_like(gaps)
            rates[finite] = np.gradient(gaps[finite], t[finite])
            out.loc[idx, "gap_closure_rate"] = rates
    return out.sort_values(["frame_id", "entity_id"], ignore_index=True)
