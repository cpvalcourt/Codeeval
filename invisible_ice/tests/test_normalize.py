import numpy as np
import pytest

from conftest import make_tracking
from invisible_ice.config import RinkConfig
from invisible_ice.data.normalize import (
    BIG_DATA_CUP,
    CoordinateNormalizer,
    DirectionNormalizer,
    SourceCoordinateSystem,
)
from invisible_ice.domain import Team


class TestCoordinateNormalizer:
    def test_maps_bdc_extents_to_canonical_rink(self):
        df = make_tracking(
            {0: {"home_1": (0.0, 0.0), "home_2": (200.0, 85.0), "puck": (100.0, 42.5)}}
        )
        out = CoordinateNormalizer(BIG_DATA_CUP).transform(df)
        by_id = out.set_index("entity_id")
        assert by_id.loc["home_1", ["x", "y"]].tolist() == [-100.0, -42.5]
        assert by_id.loc["home_2", ["x", "y"]].tolist() == [100.0, 42.5]
        assert by_id.loc["puck", ["x", "y"]].tolist() == [0.0, 0.0]

    def test_preserves_relative_distances_linearly(self):
        df = make_tracking({0: {"home_1": (50.0, 20.0), "home_2": (150.0, 20.0)}})
        out = CoordinateNormalizer(BIG_DATA_CUP).transform(df)
        xs = out.sort_values("entity_id")["x"].to_numpy()
        assert np.isclose(xs[1] - xs[0], 100.0)  # 100 source ft = 100 canonical ft

    def test_rejects_degenerate_source_extent(self):
        with pytest.raises(ValueError, match="positive size"):
            SourceCoordinateSystem(0.0, 0.0, 0.0, 85.0)

    def test_does_not_mutate_input(self):
        df = make_tracking({0: {"puck": (100.0, 42.5)}})
        CoordinateNormalizer(BIG_DATA_CUP).transform(df)
        assert df.loc[0, "x"] == 100.0


class TestDirectionNormalizer:
    def test_flips_only_periods_attacking_left(self):
        p1 = make_tracking({0: {"home_1": (30.0, 10.0)}}, period=1)
        p2 = make_tracking({1: {"home_1": (30.0, 10.0)}}, period=2)
        df = __import__("pandas").concat([p1, p2], ignore_index=True)
        out = DirectionNormalizer({1: True, 2: False}).transform(df)
        assert out[out["period"] == 1][["x", "y"]].to_numpy().tolist() == [[30.0, 10.0]]
        assert out[out["period"] == 2][["x", "y"]].to_numpy().tolist() == [[-30.0, -10.0]]

    def test_unknown_period_raises(self):
        df = make_tracking({0: {"home_1": (0.0, 0.0)}}, period=3)
        with pytest.raises(ValueError, match="periods \\[3\\]"):
            DirectionNormalizer({1: True}).transform(df)

    def test_infer_detects_attacking_side_from_mean_position(self):
        df = make_tracking(
            {0: {"home_1": (60.0, 0.0), "home_2": (40.0, 5.0), "away_1": (-50.0, 0.0)}}
        )
        normalizer = DirectionNormalizer.infer(df, Team.HOME)
        out = normalizer.transform(df)
        # Home already attacks +x: nothing flips.
        assert out.equals(df.sort_index())

        inferred_away = DirectionNormalizer.infer(df, Team.AWAY)
        flipped = inferred_away.transform(df)
        assert flipped[flipped["entity_id"] == "away_1"]["x"].iloc[0] == 50.0

    def test_infer_requires_reference_team_rows(self):
        df = make_tracking({0: {"home_1": (0.0, 0.0)}})
        with pytest.raises(ValueError, match="no rows"):
            DirectionNormalizer.infer(df, Team.AWAY)
