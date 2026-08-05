import numpy as np
import pandas as pd
import pytest

from conftest import make_tracking
from invisible_ice.data.synthetic import SyntheticGameGenerator
from invisible_ice.diagnostics import (
    Report,
    corpus_report,
    epv_report,
    label_report,
)
from invisible_ice.domain import Possession, Team
from invisible_ice.pipeline import EPVPipeline, PossessionAnalysis


@pytest.fixture(scope="module")
def corpus():
    return [
        SyntheticGameGenerator(seed=seed).generate_game(f"g{seed}")
        for seed in range(8)
    ]


@pytest.fixture(scope="module")
def fitted(corpus):
    return EPVPipeline().fit(corpus, team=Team.HOME)


class TestReport:
    def test_ok_requires_every_check(self):
        report = Report()
        report.add("a", True, "fine")
        assert report.ok
        report.add("b", False, "broken")
        assert not report.ok

    def test_str_renders_checks_and_stats(self):
        report = Report()
        report.add("a", True, "fine")
        report.stats["n"] = 3
        text = str(report)
        assert "[PASS] a: fine" in text
        assert "n=3" in text


class TestCorpusReport:
    def test_reports_volume_and_direction(self, corpus):
        """The synthetic corpus is minutes long, so it deliberately trips the
        volume thresholds that are calibrated for real games; structure and
        direction must still check out."""
        report = corpus_report(corpus, Team.HOME)
        text = str(report)
        assert "[PASS] corpus non-empty" in text
        assert "[PASS] direction normalized" in text
        assert report.stats["segments"] == 8
        assert report.stats["event_shot"] > 0
        assert report.stats["own_goalie_mean_x"] < 0

    def test_empty_corpus_fails(self):
        report = corpus_report([])
        assert not report.ok
        assert "no games loaded" in str(report)

    def test_missing_shots_and_goals_flagged(self):
        tracking = make_tracking(
            {i: {"home_1": (0.0, 0.0), "home_goalie": (-87.0, 0.0), "puck": (0.0, 0.0)}
             for i in range(5)}
        )
        events = pd.DataFrame(
            columns=["game_id", "frame_id", "event_type", "team", "player_id"]
        )
        report = corpus_report([(tracking, events)])
        text = str(report)
        assert "[FAIL] shots present" in text
        assert "[FAIL] goals present" in text

    def test_inverted_direction_is_caught(self):
        """The single most damaging bug: goalie on the wrong side."""
        tracking = make_tracking(
            {i: {"home_1": (0.0, 0.0), "home_goalie": (+87.0, 0.0), "puck": (0.0, 0.0)}
             for i in range(5)}
        )
        events = pd.DataFrame(
            columns=["game_id", "frame_id", "event_type", "team", "player_id"]
        )
        report = corpus_report([(tracking, events)], Team.HOME)
        assert "[FAIL] direction normalized" in str(report)

    def test_correct_direction_passes_that_check(self):
        tracking = make_tracking(
            {i: {"home_1": (0.0, 0.0), "home_goalie": (-87.0, 0.0), "puck": (0.0, 0.0)}
             for i in range(5)}
        )
        events = pd.DataFrame(
            columns=["game_id", "frame_id", "event_type", "team", "player_id"]
        )
        report = corpus_report([(tracking, events)], Team.HOME)
        assert "[PASS] direction normalized" in str(report)


class TestLabelReport:
    def test_reports_label_distribution(self, fitted, corpus):
        report = label_report(fitted, corpus[:3], Team.HOME)
        assert report.stats["label_keep"] > 0
        assert "possessions found" in str(report)

    def test_no_events_yields_degenerate_labels(self, fitted, corpus):
        stripped = [
            (tracking, events.iloc[0:0]) for tracking, events in corpus[:2]
        ]
        report = label_report(fitted, stripped, Team.HOME)
        text = str(report)
        assert "[FAIL] shoot labels present" in text
        assert "[FAIL] labels not degenerate" in text


class TestEpvReport:
    def test_healthy_analyses_pass(self, fitted, corpus):
        analyses = fitted.analyze_game(corpus[0][0], team=Team.HOME)
        report = epv_report(analyses)
        assert report.ok, str(report)
        assert report.stats["epv_max"] > 0

    def test_no_analyses_fails(self):
        assert not epv_report([]).ok

    def test_flat_epv_is_caught(self):
        frames = list(range(5))
        epv = pd.DataFrame(
            {
                "frame_id": frames,
                "epv": [0.0] * 5,
                "xg": [0.0] * 5,
                "p_shoot": [0.0] * 5,
                "p_pass": [0.0] * 5,
                "p_keep": [1.0] * 5,
                "p_turnover": [0.0] * 5,
            }
        )
        features = pd.DataFrame(
            {"frame_id": frames, "carrier_dist_to_net": np.linspace(20, 80, 5)}
        )
        analysis = PossessionAnalysis(
            Possession("g", Team.HOME, 0, 4), features, epv, pd.DataFrame()
        )
        report = epv_report([analysis])
        assert "[FAIL] epv varies" in str(report)


class TestCoverageChecks:
    def test_coverage_counted_per_game_not_pooled(self, fitted, corpus):
        """Frame ids repeat across games; pooling them understates coverage."""
        single = label_report(fitted, corpus[:1], Team.HOME)
        repeated = label_report(fitted, corpus[:1] * 3, Team.HOME)
        assert repeated.stats["possession_frame_coverage"] == pytest.approx(
            single.stats["possession_frame_coverage"], rel=1e-9
        )

    def test_shots_outside_possessions_are_flagged(self, fitted, corpus):
        """Shots that never land in a possession cannot train xG."""
        tracking, events = corpus[0]
        moved = events.copy()
        moved.loc[moved["event_type"] == "shot", "frame_id"] = -999
        report = label_report(fitted, [(tracking, moved)], Team.HOME)
        assert "[FAIL] shots land inside possessions" in str(report)
