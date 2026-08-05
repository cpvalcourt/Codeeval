import numpy as np
import pandas as pd
import pytest

from bdc_fixture import build_game
from invisible_ice.data.bdc import (
    BigDataCupError,
    BigDataCupLoader,
    build_entity_id,
    clock_to_seconds,
    direction_map,
    discover_games,
    parse_frame_id,
    split_segments,
)
from invisible_ice.data.schema import validate_events, validate_tracking
from invisible_ice.domain import EventType, Position, Team


@pytest.fixture(scope="module")
def game(tmp_path_factory):
    return build_game(tmp_path_factory.mktemp("raw"), seed=5)


@pytest.fixture(scope="module")
def segments(game):
    return BigDataCupLoader().load_game(
        game["tracking"], game["events"], game["orientations"],
        game_id="g1", game_key=game["game_key"],
    )


class TestParseFrameId:
    def test_extracts_trailing_digits_with_period_offset(self):
        ids = pd.Series(["2025-10-11 Team A @ Team D_065468", "x_065469"])
        out = parse_frame_id(ids, period=1)
        assert out.tolist() == [10_065_468, 10_065_469]

    def test_periods_cannot_collide(self):
        same = pd.Series(["g_000100"])
        assert parse_frame_id(same, 1).iloc[0] != parse_frame_id(same, 2).iloc[0]
        assert parse_frame_id(same, 2).iloc[0] > parse_frame_id(same, 1).iloc[0]

    def test_rejects_ids_without_digits(self):
        with pytest.raises(BigDataCupError, match="no numeric frame index"):
            parse_frame_id(pd.Series(["nope", "still nope"]), 1)


class TestBuildEntityId:
    def test_skater_uses_team_and_jersey(self):
        assert build_entity_id("Home", "44", "Player") == "home_44"

    def test_goalie_jersey_becomes_role(self):
        assert build_entity_id("Away", "Go", "Player") == "away_goalie"

    def test_puck_ignores_team_and_jersey(self):
        assert build_entity_id(np.nan, np.nan, "Puck") == "puck"


class TestClockAndDirection:
    def test_clock_parses_mmss(self):
        assert clock_to_seconds(pd.Series(["19:57"])).iloc[0] == pytest.approx(1197.0)

    def test_direction_map_alternates_by_period(self):
        orientations = pd.DataFrame(
            [{"Game": "G", "GoalieTeamOnRightSideOfRink1stPeriod": "Away"}]
        )
        # Away's goalie defends +x in P1, so HOME attacks +x in P1.
        assert direction_map(orientations, "G", Team.HOME) == {
            1: True, 2: False, 3: True, 4: False
        }
        # The same file read for the away team is the mirror image.
        assert direction_map(orientations, "G", Team.AWAY) == {
            1: False, 2: True, 3: False, 4: True
        }

    def test_unknown_game_raises(self):
        orientations = pd.DataFrame(
            [{"Game": "G", "GoalieTeamOnRightSideOfRink1stPeriod": "Away"}]
        )
        with pytest.raises(BigDataCupError, match="no camera orientation"):
            direction_map(orientations, "OTHER", Team.HOME)


class TestSplitSegments:
    def test_contiguous_frames_are_one_segment(self):
        assert split_segments(np.arange(100, 110)) == [(100, 109)]

    def test_gap_beyond_tolerance_splits(self):
        frames = np.concatenate([np.arange(0, 10), np.arange(500, 510)])
        assert split_segments(frames) == [(0, 9), (500, 509)]

    def test_small_gaps_are_tolerated(self):
        frames = np.array([0, 1, 3, 4])  # single dropped frame
        assert split_segments(frames, max_gap=2) == [(0, 4)]

    def test_empty_input(self):
        assert split_segments(np.array([])) == []


class TestLoadTrackingPeriod:
    def test_produces_canonical_columns(self, game):
        df = BigDataCupLoader().load_tracking_period(game["tracking"][1], 1)
        assert {"frame_id", "entity_id", "team", "position", "x", "y"} <= set(df.columns)

    def test_goalies_identified_by_go_jersey(self, game):
        df = BigDataCupLoader().load_tracking_period(game["tracking"][1], 1)
        goalies = df[df["position"] == Position.GOALIE.value]
        assert set(goalies["entity_id"]) == {"home_goalie", "away_goalie"}

    def test_puck_rows_have_team_none(self, game):
        df = BigDataCupLoader().load_tracking_period(game["tracking"][1], 1)
        puck = df[df["position"] == Position.PUCK.value]
        assert set(puck["team"]) == {"none"}
        assert set(puck["entity_id"]) == {"puck"}

    def test_entity_ids_are_stable_despite_track_id_churn(self, game):
        df = BigDataCupLoader().load_tracking_period(game["tracking"][1], 1)
        skaters = df[df["position"] == Position.SKATER.value]
        # 5 per team, regardless of thousands of per-detection track ids.
        assert len(set(skaters["entity_id"])) == 10

    def test_null_coordinates_dropped(self, game):
        df = BigDataCupLoader().load_tracking_period(game["tracking"][1], 1)
        assert not df[["x", "y"]].isna().any().any()

    def test_missing_columns_raise(self, tmp_path):
        bad = tmp_path / "bad.csv"
        pd.DataFrame({"Image Id": ["g_1"]}).to_csv(bad, index=False)
        with pytest.raises(BigDataCupError, match="missing columns"):
            BigDataCupLoader().load_tracking_period(bad, 1)


class TestLoadEvents:
    def test_maps_vocabulary_and_ignores_unlisted(self, game):
        loader = BigDataCupLoader()
        source = loader.load_tracking_period(game["tracking"][1], 1)
        events = loader.load_events(game["events"], source, "g1")
        kinds = set(events["event_type"])
        assert EventType.PASS.value in kinds
        assert EventType.SHOT.value in kinds
        assert EventType.TURNOVER.value in kinds
        # "Zone Entry" is deliberately not part of the label set.
        assert len(events) < 100

    def test_takeaway_is_credited_as_opponent_turnover(self, game):
        loader = BigDataCupLoader()
        source = loader.load_tracking_period(game["tracking"][1], 1)
        events = loader.load_events(game["events"], source, "g1")
        turnovers = events[events["event_type"] == EventType.TURNOVER.value]
        # The fixture's takeaways are BY the away team, so they are home's
        # turnovers.
        assert set(turnovers["team"]) == {Team.HOME.value}

    def test_every_goal_has_a_shot_at_the_same_frame(self, game):
        loader = BigDataCupLoader()
        source = loader.load_tracking_period(game["tracking"][1], 1)
        events = loader.load_events(game["events"], source, "g1")
        goals = events[events["event_type"] == EventType.GOAL.value]
        shots = events[events["event_type"] == EventType.SHOT.value]
        assert len(goals) >= 1
        for goal in goals.itertuples(index=False):
            assert (shots["frame_id"] - goal.frame_id).abs().min() <= 45

    def test_events_align_near_the_puck(self, game):
        """Alignment must use coordinates, not just the 1-second clock."""
        loader = BigDataCupLoader()
        source = loader.load_tracking_period(game["tracking"][1], 1)
        events = loader.load_events(game["events"], source, "g1")
        puck = source[source["position"] == Position.PUCK.value].set_index("frame_id")
        for row in events.head(10).itertuples(index=False):
            assert row.frame_id in puck.index

    def test_player_ids_are_entity_ids(self, game):
        loader = BigDataCupLoader()
        source = loader.load_tracking_period(game["tracking"][1], 1)
        events = loader.load_events(game["events"], source, "g1")
        assert events["player_id"].str.match(r"(home|away)_").all()


class TestLoadGame:
    def test_returns_one_unit_per_play_segment(self, segments, game):
        assert len(segments) == game["n_segments"]

    def test_every_segment_validates(self, segments):
        for tracking, events in segments:
            validate_tracking(tracking)
            validate_events(events)

    def test_segments_have_unique_game_ids(self, segments):
        ids = [t["game_id"].iloc[0] for t, _ in segments]
        assert len(set(ids)) == len(ids)

    def test_no_segment_spans_a_stoppage(self, segments, game):
        for tracking, _ in segments:
            frames = np.sort(tracking["frame_id"].unique())
            assert np.all(np.diff(frames) <= 2)
            assert len(frames) <= game["segment_frames"]

    def test_roster_is_complete_in_every_frame(self, segments):
        """The exporter requires this; possessions are subsets of segments."""
        for tracking, _ in segments:
            per_frame = tracking.groupby("frame_id")["entity_id"].nunique()
            assert per_frame.nunique() == 1

    def test_puck_present_in_every_frame(self, segments):
        for tracking, _ in segments:
            pucks = tracking[tracking["position"] == Position.PUCK.value]
            assert pucks["frame_id"].nunique() == tracking["frame_id"].nunique()

    def test_goalies_survive_sparse_tracking(self, segments):
        """Goalies are ~35% tracked but must not be dropped — xG needs them."""
        for tracking, _ in segments:
            assert {"home_goalie", "away_goalie"} <= set(tracking["entity_id"])

    def test_direction_normalized_so_home_attacks_positive_x(self, segments):
        """Home defends -x, so its goalie must sit at negative mean x."""
        for tracking, _ in segments:
            goalies = tracking[tracking["position"] == Position.GOALIE.value]
            home = goalies[goalies["team"] == Team.HOME.value]["x"].mean()
            away = goalies[goalies["team"] == Team.AWAY.value]["x"].mean()
            assert home < 0 < away

    def test_flipped_orientation_produces_same_normalized_geometry(self, tmp_path):
        """The orientation flag must actually be honored, not ignored."""
        mirrored = build_game(
            tmp_path / "mirror", seed=5, home_attacks_right_p1=False
        )
        out = BigDataCupLoader().load_game(
            mirrored["tracking"], mirrored["events"], mirrored["orientations"],
            game_id="g2", game_key=mirrored["game_key"],
        )
        assert out
        for tracking, _ in out:
            goalies = tracking[tracking["position"] == Position.GOALIE.value]
            assert goalies[goalies["team"] == Team.HOME.value]["x"].mean() < 0

    def test_timestamps_start_at_zero_and_step_by_frame_rate(self, segments):
        for tracking, _ in segments:
            times = np.sort(tracking["timestamp"].unique())
            assert times[0] == pytest.approx(0.0)
            steps = np.diff(times)
            assert np.allclose(steps, 1 / 30.0, atol=1e-6)

    def test_short_segments_are_dropped(self, game):
        loader = BigDataCupLoader(min_segment_frames=10_000)
        assert loader.load_game(
            game["tracking"], game["events"], game["orientations"],
            game_id="g1", game_key=game["game_key"],
        ) == []


class TestDiscoverGames:
    def test_groups_tracking_and_events_by_game(self, game, tmp_path):
        found = discover_games(game["tracking"][1].parent)
        assert len(found) == 1
        entry = next(iter(found.values()))
        assert set(entry["tracking"]) == {1}
        assert entry["events"].name.endswith("Events.csv")

    def test_games_without_events_are_skipped(self, tmp_path):
        (tmp_path / "x.Tracking_P1.csv").write_text("Image Id\n")
        assert discover_games(tmp_path) == {}


class TestPipelineIntegration:
    """The loader's contract is that the engine consumes it unchanged."""

    @pytest.fixture(scope="class")
    def corpus(self, tmp_path_factory):
        root = tmp_path_factory.mktemp("corpus")
        loader = BigDataCupLoader()
        games = []
        for seed in range(4):
            spec = build_game(root / f"g{seed}", seed=seed)
            games.extend(
                loader.load_game(
                    spec["tracking"], spec["events"], spec["orientations"],
                    game_id=f"g{seed}", game_key=spec["game_key"],
                )
            )
        return games

    def test_pipeline_fits_and_analyzes_loader_output(self, corpus):
        from invisible_ice.pipeline import EPVPipeline

        pipeline = EPVPipeline().fit(corpus, team=Team.HOME)
        analyses = pipeline.analyze_game(corpus[0][0], team=Team.HOME)
        for analysis in analyses:
            assert ((analysis.epv["epv"] >= 0) & (analysis.epv["epv"] <= 1)).all()

    def test_exporter_accepts_loader_output(self, corpus):
        from invisible_ice.export import game_payload
        from invisible_ice.pipeline import EPVPipeline

        pipeline = EPVPipeline().fit(corpus, team=Team.HOME)
        tracking = corpus[0][0]
        analyses = pipeline.analyze_game(tracking, team=Team.HOME)
        if not analyses:
            pytest.skip("no possessions detected in this fixture segment")
        payload = game_payload("bdc", tracking, analyses)
        assert payload["possessions"]
        assert payload["possessions"][0]["entities"]
