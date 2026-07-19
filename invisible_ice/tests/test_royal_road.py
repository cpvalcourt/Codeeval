from conftest import make_tracking
from invisible_ice.features.royal_road import flag_royal_road


def puck_path(points):
    return make_tracking({i: {"puck": xy} for i, xy in enumerate(points)})


class TestFlagRoyalRoad:
    def test_crossing_in_offensive_zone_is_flagged(self):
        df = puck_path([(60.0, 5.0), (61.0, -4.0), (62.0, -6.0)])
        out = flag_royal_road(df)
        assert out["royal_road_crossing"].tolist() == [False, True, False]

    def test_crossing_outside_zone_is_ignored(self):
        df = puck_path([(0.0, 5.0), (1.0, -5.0)])
        out = flag_royal_road(df)
        assert not out["royal_road_crossing"].any()

    def test_crossing_requires_both_frames_in_zone(self):
        df = puck_path([(20.0, 5.0), (30.0, -5.0)])  # entered zone mid-cross
        out = flag_royal_road(df)
        assert not out["royal_road_crossing"].any()

    def test_no_crossing_when_staying_on_one_side(self):
        df = puck_path([(60.0, 5.0), (65.0, 8.0), (70.0, 3.0)])
        out = flag_royal_road(df)
        assert not out["royal_road_crossing"].any()

    def test_recent_window_persists_then_expires(self):
        points = [(60.0, 3.0), (60.0, -3.0)] + [(60.0, -3.0)] * 40
        out = flag_royal_road(puck_path(points), recent_window=10)
        assert out.loc[1, "royal_road_recent"]
        assert out.loc[11, "royal_road_recent"]  # frame 11 - crossing frame 1 = 10
        assert not out.loc[12, "royal_road_recent"]

    def test_no_flags_before_any_crossing(self):
        out = flag_royal_road(puck_path([(60.0, 5.0), (61.0, 6.0)]))
        assert not out["royal_road_recent"].any()
