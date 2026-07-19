import pandas as pd

from invisible_ice.config import RinkConfig
from invisible_ice.data.schema import validate_events, validate_tracking
from invisible_ice.data.synthetic import PUCK_ID, SyntheticGameGenerator


class TestSyntheticGameGenerator:
    def test_same_seed_is_deterministic(self):
        t1, e1 = SyntheticGameGenerator(seed=3).generate_game("g")
        t2, e2 = SyntheticGameGenerator(seed=3).generate_game("g")
        pd.testing.assert_frame_equal(t1, t2)
        pd.testing.assert_frame_equal(e1, e2)

    def test_different_seeds_differ(self):
        t1, _ = SyntheticGameGenerator(seed=3).generate_game("g")
        t2, _ = SyntheticGameGenerator(seed=4).generate_game("g")
        assert not t1.equals(t2)

    def test_output_is_schema_valid(self, synthetic_game):
        tracking, events = synthetic_game
        validate_tracking(tracking)
        validate_events(events)

    def test_positions_stay_on_the_rink(self, synthetic_game):
        tracking, _ = synthetic_game
        rink = RinkConfig()
        skaters = tracking[tracking["entity_id"] != PUCK_ID]
        assert skaters["x"].between(rink.x_min, rink.x_max).all()
        assert skaters["y"].between(rink.y_min, rink.y_max).all()

    def test_full_roster_every_frame(self, synthetic_game):
        tracking, _ = synthetic_game
        counts = tracking.groupby("frame_id")["entity_id"].nunique()
        assert (counts == 13).all()  # 10 skaters + 2 goalies + puck

    def test_events_reference_existing_frames_and_players(self, synthetic_game):
        tracking, events = synthetic_game
        frames = set(tracking["frame_id"])
        assert set(events["frame_id"]).issubset(frames)
        assert events["player_id"].str.startswith("home_").all()

    def test_every_possession_reaches_a_terminal_event(self, synthetic_game):
        _, events = synthetic_game
        terminal = events[events["event_type"].isin(["shot", "turnover"])]
        gen_cfg_possessions = 6
        assert len(terminal) >= gen_cfg_possessions

    def test_corpus_contains_shots_and_goals(self):
        """A modest corpus must exercise both xG classes."""
        all_events = []
        for seed in range(8):
            _, events = SyntheticGameGenerator(seed=seed).generate_game(f"g{seed}")
            all_events.append(events)
        events = pd.concat(all_events)
        kinds = set(events["event_type"])
        assert {"pass", "shot", "goal", "turnover"} <= kinds
