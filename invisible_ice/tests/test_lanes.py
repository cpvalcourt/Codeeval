import numpy as np
import pandas as pd

from conftest import make_tracking
from invisible_ice.config import LaneConfig
from invisible_ice.domain import Team
from invisible_ice.features.lanes import compute_lane_features, lane_openness

CARRIER = np.array([0.0, 0.0])
TARGET = np.array([20.0, 0.0])


class TestLaneOpenness:
    def test_no_defenders_is_fully_open(self):
        assert lane_openness(CARRIER, TARGET, np.empty((0, 2))) == 1.0

    def test_defender_in_lane_closes_it(self):
        score = lane_openness(CARRIER, TARGET, np.array([[10.0, 0.0]]))
        assert score < 0.25

    def test_distant_defender_leaves_lane_open(self):
        score = lane_openness(CARRIER, TARGET, np.array([[10.0, 30.0]]))
        assert score > 0.9

    def test_openness_increases_with_defender_distance(self):
        scores = [
            lane_openness(CARRIER, TARGET, np.array([[10.0, dy]]))
            for dy in (0.0, 3.0, 6.0, 12.0)
        ]
        assert scores == sorted(scores)

    def test_defender_closing_on_lane_reduces_openness(self):
        static = lane_openness(
            CARRIER, TARGET, np.array([[10.0, 6.0]]), np.array([[0.0, 0.0]])
        )
        closing = lane_openness(
            CARRIER, TARGET, np.array([[10.0, 6.0]]), np.array([[0.0, -8.0]])
        )
        assert closing < static

    def test_only_nearest_defender_matters(self):
        one = lane_openness(CARRIER, TARGET, np.array([[10.0, 4.0]]))
        crowd = lane_openness(
            CARRIER, TARGET, np.array([[10.0, 4.0], [5.0, 30.0], [15.0, -25.0]])
        )
        assert np.isclose(one, crowd)


class TestComputeLaneFeatures:
    def frames(self):
        return make_tracking(
            {
                0: {
                    "home_1": (0.0, 0.0),  # carrier
                    "home_2": (20.0, 0.0),  # blocked lane
                    "home_3": (0.0, 20.0),  # open lane
                    "away_1": (10.0, 0.0),
                    "puck": (0.0, 0.0),
                }
            }
        )

    def test_summarizes_best_mean_and_count(self):
        carrier = pd.Series({0: "home_1"})
        out = compute_lane_features(self.frames(), Team.HOME, carrier)
        row = out.iloc[0]
        assert row["best_lane_openness"] > 0.9
        assert 0.0 < row["mean_lane_openness"] < row["best_lane_openness"]
        assert row["n_open_lanes"] == 1

    def test_loose_puck_frames_get_neutral_features(self):
        carrier = pd.Series({0: None})
        out = compute_lane_features(self.frames(), Team.HOME, carrier)
        assert out.iloc[0]["best_lane_openness"] == 0.0
        assert out.iloc[0]["n_open_lanes"] == 0

    def test_threshold_configurable(self):
        carrier = pd.Series({0: "home_1"})
        strict = compute_lane_features(
            self.frames(), Team.HOME, carrier, LaneConfig(open_threshold=0.999)
        )
        assert strict.iloc[0]["n_open_lanes"] == 0
