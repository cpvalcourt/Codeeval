import pandas as pd
import pytest

from conftest import make_tracking
from invisible_ice.data.schema import SchemaError
from invisible_ice.data.storage import ParquetRepository


@pytest.fixture
def repo(tmp_path):
    return ParquetRepository(tmp_path)


def two_game_tracking() -> pd.DataFrame:
    return pd.concat(
        [
            make_tracking({0: {"home_1": (1.0, 2.0), "puck": (1.0, 2.0)}}, game_id="g1"),
            make_tracking({0: {"home_1": (3.0, 4.0), "puck": (3.0, 4.0)}}, game_id="g2"),
        ],
        ignore_index=True,
    )


class TestParquetRepository:
    def test_tracking_roundtrip_preserves_schema(self, repo):
        original = two_game_tracking()
        repo.save_tracking(original)
        loaded = repo.load_tracking()
        assert len(loaded) == len(original)
        assert loaded["game_id"].dtype == original["game_id"].dtype
        assert loaded["period"].dtype == "int64"
        pd.testing.assert_frame_equal(
            loaded.sort_values(["game_id", "entity_id"], ignore_index=True),
            original.sort_values(["game_id", "entity_id"], ignore_index=True),
        )

    def test_load_filters_by_game_and_period(self, repo):
        repo.save_tracking(two_game_tracking())
        g1 = repo.load_tracking(game_id="g1")
        assert set(g1["game_id"]) == {"g1"}
        empty = repo.load_tracking(game_id="g1", period=2)
        assert empty.empty

    def test_list_games(self, repo):
        assert repo.list_games() == []
        repo.save_tracking(two_game_tracking())
        assert repo.list_games() == ["g1", "g2"]

    def test_events_roundtrip(self, repo):
        events = pd.DataFrame(
            [
                {
                    "game_id": "g1",
                    "frame_id": 5,
                    "event_type": "shot",
                    "team": "home",
                    "player_id": "home_1",
                }
            ]
        )
        repo.save_events(events)
        loaded = repo.load_events("g1")
        assert loaded.loc[0, "event_type"] == "shot"
        assert loaded["frame_id"].dtype == "int64"

    def test_save_rejects_invalid_data(self, repo):
        with pytest.raises(SchemaError):
            repo.save_tracking(pd.DataFrame({"x": [1.0]}))
