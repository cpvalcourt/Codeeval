import pytest

from conftest import make_tracking
from invisible_ice.config import PossessionConfig
from invisible_ice.data.possession import PossessionStateMachine
from invisible_ice.domain import Team


CFG = PossessionConfig(control_radius=4.0, min_control_frames=3, loose_frames=5)


def machine() -> PossessionStateMachine:
    return PossessionStateMachine(CFG)


def frames_with_carrier(n, carrier="home_1", start=0, puck_at=(10.0, 0.0)):
    """n frames of `carrier` sitting on the puck, opponent far away."""
    return {
        start + i: {
            carrier: puck_at,
            "away_1": (-50.0, 0.0),
            "puck": puck_at,
        }
        for i in range(n)
    }


class TestPossessionStateMachine:
    def test_control_requires_min_frames(self):
        df = make_tracking(frames_with_carrier(2))
        states = machine().annotate(df)
        assert set(states["puck_state"]) == {"loose"}

        df = make_tracking(frames_with_carrier(3))
        states = machine().annotate(df)
        assert states["puck_state"].iloc[-1] == "home"
        assert states["controller"].iloc[-1] == "home_1"

    def test_brief_opponent_touch_does_not_flip_possession(self):
        frames = frames_with_carrier(5)
        # Two frames where away_1 is nearest and in radius, home_1 pushed out.
        for i in (5, 6):
            frames[i] = {
                "home_1": (20.0, 0.0),
                "away_1": (10.0, 0.0),
                "puck": (10.0, 0.0),
            }
        frames.update(frames_with_carrier(5, start=7))
        states = machine().annotate(make_tracking(frames))
        assert (states["puck_state"].iloc[5:7] == "home").all()
        assert states["puck_state"].iloc[-1] == "home"

    def test_sustained_opponent_control_flips_possession(self):
        frames = frames_with_carrier(5)
        for i in range(5, 9):
            frames[i] = {
                "home_1": (30.0, 0.0),
                "away_1": (10.0, 0.0),
                "puck": (10.0, 0.0),
            }
        states = machine().annotate(make_tracking(frames))
        assert states["puck_state"].iloc[-1] == "away"
        assert states["controller"].iloc[-1] == "away_1"

    def test_puck_goes_loose_after_loose_frames(self):
        frames = frames_with_carrier(5)
        for i in range(5, 11):
            frames[i] = {
                "home_1": (10.0, 0.0),
                "away_1": (-50.0, 0.0),
                "puck": (60.0, 30.0),  # nobody close
            }
        states = machine().annotate(make_tracking(frames))
        assert states["puck_state"].iloc[8] == "home"  # within hysteresis
        assert states["puck_state"].iloc[9] == "loose"  # 5th frame without control

    def test_goalies_never_take_control(self):
        frames = {
            i: {"away_goalie": (10.0, 0.0), "home_1": (-60.0, 0.0), "puck": (10.0, 0.0)}
            for i in range(6)
        }
        states = machine().annotate(make_tracking(frames))
        assert set(states["puck_state"]) == {"loose"}

    def test_rejects_multiple_games(self):
        import pandas as pd

        df = pd.concat(
            [
                make_tracking(frames_with_carrier(2), game_id="g1"),
                make_tracking(frames_with_carrier(2), game_id="g2"),
            ],
            ignore_index=True,
        )
        with pytest.raises(ValueError, match="single game"):
            machine().annotate(df)


class TestExtractPossessions:
    def test_contiguous_spans_split_by_loose_and_team(self):
        frames = frames_with_carrier(6)  # home control
        for i in range(6, 12):
            frames[i] = {
                "home_1": (10.0, 0.0),
                "away_1": (-50.0, 0.0),
                "puck": (60.0, 30.0),
            }
        for i in range(12, 18):
            frames[i] = {
                "home_1": (-60.0, 0.0),
                "away_1": (10.0, 0.0),
                "puck": (10.0, 0.0),
            }
        m = machine()
        states = m.annotate(make_tracking(frames))
        possessions = m.extract_possessions(states, "g1")
        assert [p.team for p in possessions] == [Team.HOME, Team.AWAY]
        home, away = possessions
        assert home.start_frame == 2  # control established on 3rd frame
        assert home.end_frame == 9  # hysteresis holds until the 5th loose frame
        assert away.start_frame == 14  # away control established on its 3rd frame
        assert away.end_frame == 17
        assert away.n_frames == away.end_frame - away.start_frame + 1
