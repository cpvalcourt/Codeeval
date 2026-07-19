import numpy as np

from conftest import make_tracking
from invisible_ice.domain import Team
from invisible_ice.features.pressure import compute_pressure


class TestComputePressure:
    def test_nearest_defender_identified(self):
        df = make_tracking(
            {
                0: {
                    "home_1": (0.0, 0.0),
                    "away_1": (3.0, 4.0),  # dist 5
                    "away_2": (20.0, 0.0),
                    "puck": (0.0, 0.0),
                }
            }
        )
        out = compute_pressure(df, Team.HOME)
        row = out.iloc[0]
        assert row["nearest_defender_id"] == "away_1"
        assert np.isclose(row["nearest_defender_dist"], 5.0)

    def test_goalies_are_not_defenders(self):
        df = make_tracking(
            {
                0: {
                    "home_1": (80.0, 0.0),
                    "away_goalie": (87.0, 0.0),
                    "away_1": (40.0, 0.0),
                    "puck": (80.0, 0.0),
                }
            }
        )
        out = compute_pressure(df, Team.HOME)
        assert out.iloc[0]["nearest_defender_id"] == "away_1"

    def test_closing_defender_gives_negative_gap_closure(self):
        # Defender closes from 12 ft to 4 ft over 9 frames.
        frames = {
            i: {
                "home_1": (0.0, 0.0),
                "away_1": (12.0 - i, 0.0),
                "puck": (0.0, 0.0),
            }
            for i in range(9)
        }
        out = compute_pressure(make_tracking(frames), Team.HOME)
        # Gap shrinks 1 ft per frame at 30 fps => -30 ft/s.
        assert np.allclose(out["gap_closure_rate"], -30.0)

    def test_retreating_defender_gives_positive_gap_closure(self):
        frames = {
            i: {"home_1": (0.0, 0.0), "away_1": (5.0 + i, 0.0), "puck": (0.0, 0.0)}
            for i in range(6)
        }
        out = compute_pressure(make_tracking(frames), Team.HOME)
        assert (out["gap_closure_rate"] > 0).all()

    def test_no_defenders_yields_infinite_gap(self):
        df = make_tracking({0: {"home_1": (0.0, 0.0), "puck": (0.0, 0.0)}})
        out = compute_pressure(df, Team.HOME)
        assert np.isinf(out.iloc[0]["nearest_defender_dist"])
        assert out.iloc[0]["gap_closure_rate"] == 0.0

    def test_one_row_per_attacker_per_frame(self):
        frames = {
            i: {
                "home_1": (0.0, 0.0),
                "home_2": (10.0, 10.0),
                "away_1": (5.0, 5.0),
                "puck": (0.0, 0.0),
            }
            for i in range(3)
        }
        out = compute_pressure(make_tracking(frames), Team.HOME)
        assert len(out) == 6
        assert set(out["entity_id"]) == {"home_1", "home_2"}
