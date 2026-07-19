import pandas as pd
import pytest

from conftest import make_tracking
from invisible_ice.data.schema import SchemaError, validate_events, validate_tracking


def valid_tracking() -> pd.DataFrame:
    return make_tracking({0: {"home_1": (0.0, 0.0), "puck": (1.0, 1.0)}})


def valid_events() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "game_id": "g1",
                "frame_id": 3,
                "event_type": "pass",
                "team": "home",
                "player_id": "home_1",
            }
        ]
    )


class TestValidateTracking:
    def test_accepts_valid_data(self):
        out = validate_tracking(valid_tracking())
        assert len(out) == 2
        assert list(out.columns)[:4] == ["game_id", "period", "frame_id", "timestamp"]

    def test_missing_column_raises(self):
        with pytest.raises(SchemaError, match="missing columns.*position"):
            validate_tracking(valid_tracking().drop(columns=["position"]))

    def test_null_coordinates_raise(self):
        df = valid_tracking()
        df.loc[0, "x"] = None
        with pytest.raises(SchemaError, match="nulls"):
            validate_tracking(df)

    def test_invalid_team_raises(self):
        df = valid_tracking()
        df.loc[0, "team"] = "visitors"
        with pytest.raises(SchemaError, match="invalid team"):
            validate_tracking(df)

    def test_puck_must_have_team_none(self):
        df = valid_tracking()
        df.loc[df["entity_id"] == "puck", "team"] = "home"
        with pytest.raises(SchemaError, match="team='none'"):
            validate_tracking(df)

    def test_sorts_and_coerces_dtypes(self):
        df = valid_tracking()
        df["frame_id"] = df["frame_id"].astype("int32")
        out = validate_tracking(df.iloc[::-1])
        assert out["frame_id"].dtype == "int64"
        assert list(out["entity_id"]) == sorted(out["entity_id"])


class TestValidateEvents:
    def test_accepts_valid_events(self):
        out = validate_events(valid_events())
        assert out.loc[0, "event_type"] == "pass"

    def test_invalid_event_type_raises(self):
        df = valid_events()
        df.loc[0, "event_type"] = "fight"
        with pytest.raises(SchemaError, match="invalid event"):
            validate_events(df)

    def test_missing_column_raises(self):
        with pytest.raises(SchemaError, match="missing columns"):
            validate_events(valid_events().drop(columns=["player_id"]))
