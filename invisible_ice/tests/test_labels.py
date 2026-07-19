import numpy as np
import pandas as pd

from invisible_ice.config import LabelConfig
from invisible_ice.models.labels import make_action_labels, make_shot_samples


def events(rows):
    return pd.DataFrame(
        [
            {
                "game_id": "g1",
                "frame_id": fid,
                "event_type": kind,
                "team": "home",
                "player_id": "home_1",
            }
            for fid, kind in rows
        ],
        columns=["game_id", "frame_id", "event_type", "team", "player_id"],
    )


class TestMakeActionLabels:
    def test_frames_before_event_within_horizon_get_event_label(self):
        labels = make_action_labels(
            np.array([0, 5, 10]), events([(10, "shot")]), LabelConfig(horizon_frames=10)
        )
        assert labels.tolist() == ["shoot", "shoot", "shoot"]

    def test_frames_beyond_horizon_are_keep(self):
        labels = make_action_labels(
            np.array([0, 40]), events([(50, "pass")]), LabelConfig(horizon_frames=15)
        )
        assert labels.tolist() == ["keep", "pass"]

    def test_nearest_upcoming_event_wins(self):
        labels = make_action_labels(
            np.array([0, 12]),
            events([(10, "pass"), (20, "shot")]),
            LabelConfig(horizon_frames=15),
        )
        assert labels.tolist() == ["pass", "shoot"]

    def test_goal_events_are_ignored_for_actions(self):
        labels = make_action_labels(
            np.array([5]), events([(10, "goal")]), LabelConfig(horizon_frames=15)
        )
        assert labels.tolist() == ["keep"]

    def test_no_events_all_keep(self):
        labels = make_action_labels(np.array([0, 1, 2]), events([]))
        assert set(labels) == {"keep"}


class TestMakeShotSamples:
    def features(self):
        return pd.DataFrame({"frame_id": [0, 10, 20, 30], "f": [1.0, 2.0, 3.0, 4.0]})

    def test_shot_followed_by_goal_labeled_positive(self):
        X, y = make_shot_samples(
            self.features(), events([(10, "shot"), (25, "goal")])
        )
        assert len(X) == 1
        assert X["frame_id"].tolist() == [10]
        assert y.tolist() == [1]

    def test_shot_without_goal_labeled_negative(self):
        X, y = make_shot_samples(self.features(), events([(20, "shot")]))
        assert y.tolist() == [0]

    def test_goal_before_shot_does_not_count(self):
        _, y = make_shot_samples(self.features(), events([(5, "goal"), (20, "shot")]))
        assert y.tolist() == [0]

    def test_shot_frame_missing_from_features_is_skipped(self):
        X, y = make_shot_samples(self.features(), events([(99, "shot")]))
        assert len(X) == 0
        assert len(y) == 0
