import pandas as pd

from conftest import make_tracking
from invisible_ice.domain import Team
from invisible_ice.features.builder import (
    CarrierFeatures,
    FeatureContext,
    FrameFeatureBuilder,
)
from invisible_ice.features.kinematics import add_kinematics


def context(n_frames: int = 4) -> FeatureContext:
    frames = {
        i: {
            "home_1": (30.0 + i, 0.0),
            "home_2": (40.0, 15.0),
            "away_1": (50.0, 0.0),
            "away_goalie": (87.0, 0.0),
            "puck": (30.0 + i, 0.0),
        }
        for i in range(n_frames)
    }
    tracking = add_kinematics(make_tracking(frames))
    carrier = pd.Series({i: "home_1" for i in range(n_frames)})
    return FeatureContext(tracking=tracking, attacking_team=Team.HOME, carrier_by_frame=carrier)


class TestFrameFeatureBuilder:
    def test_one_row_per_frame_with_all_features(self):
        builder = FrameFeatureBuilder()
        out = builder.build(context(n_frames=4))
        assert len(out) == 4
        assert set(builder.feature_names) <= set(out.columns)
        assert not out[builder.feature_names].isna().any().any()

    def test_carrier_distance_shrinks_as_carrier_advances(self):
        out = FrameFeatureBuilder().build(context(n_frames=4))
        dist = out["carrier_dist_to_net"]
        assert dist.is_monotonic_decreasing

    def test_composition_is_extensible(self):
        class ConstantFeature:
            columns = ["always_seven"]

            def transform(self, ctx):
                frames = ctx.tracking["frame_id"].drop_duplicates()
                return pd.DataFrame({"frame_id": frames, "always_seven": 7.0})

        builder = FrameFeatureBuilder([CarrierFeatures(), ConstantFeature()])
        out = builder.build(context())
        assert (out["always_seven"] == 7.0).all()
        assert builder.feature_names == CarrierFeatures.columns + ["always_seven"]

    def test_loose_frames_fall_back_to_puck_position(self):
        ctx = context(n_frames=2)
        ctx.carrier_by_frame = pd.Series({0: None, 1: None})
        out = FrameFeatureBuilder([CarrierFeatures()]).build(ctx)
        # Puck sits at x=30/31 -> distance to the net at (89, 0).
        assert abs(out.loc[0, "carrier_dist_to_net"] - 59.0) < 1e-9
