from __future__ import annotations

import pandas as pd
import pytest

from invisible_ice.data.synthetic import SyntheticGameGenerator


def make_tracking(
    frames: dict[int, dict[str, tuple[float, float]]],
    game_id: str = "g1",
    period: int = 1,
    frame_rate: float = 30.0,
) -> pd.DataFrame:
    """Build canonical tracking rows from {frame_id: {entity_id: (x, y)}}.

    Team and position are inferred from the entity id ("home_*"/"away_*",
    "*goalie*", "puck").
    """
    rows = []
    for frame_id, entities in frames.items():
        for entity_id, (x, y) in entities.items():
            if entity_id == "puck":
                team, position = "none", "puck"
            else:
                team = "home" if entity_id.startswith("home") else "away"
                position = "goalie" if "goalie" in entity_id else "skater"
            rows.append(
                {
                    "game_id": game_id,
                    "period": period,
                    "frame_id": frame_id,
                    "timestamp": frame_id / frame_rate,
                    "entity_id": entity_id,
                    "team": team,
                    "position": position,
                    "x": float(x),
                    "y": float(y),
                }
            )
    return pd.DataFrame(rows)


@pytest.fixture(scope="session")
def synthetic_game() -> tuple[pd.DataFrame, pd.DataFrame]:
    """One deterministic synthetic game shared across the session."""
    return SyntheticGameGenerator(seed=7).generate_game("game_7")
