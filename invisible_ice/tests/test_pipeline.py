"""End-to-end integration: synthetic corpus -> trained models -> EPV curves."""

import numpy as np
import pytest

from invisible_ice.data.synthetic import SyntheticGameGenerator
from invisible_ice.domain import Team
from invisible_ice.pipeline import EPVPipeline


@pytest.fixture(scope="module")
def corpus():
    return [
        SyntheticGameGenerator(seed=seed).generate_game(f"game_{seed}")
        for seed in range(10)
    ]


@pytest.fixture(scope="module")
def fitted(corpus):
    return EPVPipeline().fit(corpus, team=Team.HOME)


class TestEPVPipeline:
    def test_fit_produces_both_models(self, fitted):
        assert fitted.transition_model is not None
        assert fitted.xg_model is not None

    def test_analyze_yields_bounded_epv_curves(self, fitted, corpus):
        tracking, _ = corpus[0]
        analyses = fitted.analyze_game(tracking, team=Team.HOME)
        assert analyses, "expected at least one qualifying possession"
        for analysis in analyses:
            epv = analysis.epv
            assert len(epv) == len(analysis.features)
            assert ((epv["epv"] >= 0.0) & (epv["epv"] <= 1.0)).all()
            probs = epv[["p_shoot", "p_pass", "p_keep", "p_turnover"]].sum(axis=1)
            np.testing.assert_allclose(probs, 1.0, atol=1e-9)

    def test_epv_frames_lie_within_possession_span(self, fitted, corpus):
        tracking, _ = corpus[1]
        for analysis in fitted.analyze_game(tracking, team=Team.HOME):
            span = analysis.possession
            assert analysis.epv["frame_id"].between(
                span.start_frame, span.end_frame
            ).all()

    def test_attribution_covers_home_skaters_and_conserves_delta(
        self, fitted, corpus
    ):
        tracking, _ = corpus[2]
        for analysis in fitted.analyze_game(tracking, team=Team.HOME):
            attr = analysis.attribution
            if attr.empty:
                continue
            assert attr["player_id"].str.startswith("home_").all()
            net_change = analysis.epv["epv"].iloc[-1] - analysis.epv["epv"].iloc[0]
            assert np.isclose(attr["epv_added_total"].sum(), net_change, atol=1e-9)

    def test_epv_responds_to_scoring_threat(self, fitted, corpus):
        """Frames near the net with the puck should carry more value on
        average than frames in the neutral zone."""
        near, far = [], []
        for tracking, _ in corpus[:4]:
            for analysis in fitted.analyze_game(tracking, team=Team.HOME):
                merged = analysis.features.merge(analysis.epv, on="frame_id")
                near.extend(merged[merged["carrier_dist_to_net"] < 30]["epv"])
                far.extend(merged[merged["carrier_dist_to_net"] > 70]["epv"])
        assert near and far
        assert np.mean(near) > np.mean(far)

    def test_analyze_before_fit_raises(self, corpus):
        tracking, _ = corpus[0]
        with pytest.raises(RuntimeError, match="not fitted"):
            EPVPipeline().analyze_game(tracking)

    def test_fit_with_no_possessions_raises(self):
        import pandas as pd

        from conftest import make_tracking

        tiny = make_tracking({0: {"home_1": (0.0, 0.0), "puck": (50.0, 0.0)}})
        empty_events = pd.DataFrame(
            columns=["game_id", "frame_id", "event_type", "team", "player_id"]
        )
        with pytest.raises(ValueError, match="no qualifying possessions"):
            EPVPipeline().fit([(tiny, empty_events)])
