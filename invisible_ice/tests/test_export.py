import json

import numpy as np
import pandas as pd
import pytest

from conftest import make_tracking
from invisible_ice.domain import Possession, Team
from invisible_ice.export import (
    PAYLOAD_VERSION,
    game_payload,
    possession_payload,
    write_game_json,
)
from invisible_ice.pipeline import PossessionAnalysis


def build_analysis(start=0, end=3):
    frames = list(range(start, end + 1))
    epv = pd.DataFrame(
        {
            "frame_id": frames,
            "epv": [0.05123456, 0.06, 0.07, 0.08],
            "xg": [0.02] * 4,
            "p_shoot": [0.1] * 4,
            "p_pass": [0.2] * 4,
            "p_keep": [0.6] * 4,
            "p_turnover": [0.1] * 4,
        }
    )
    features = pd.DataFrame({"frame_id": frames, "f": np.zeros(4)})
    attribution = pd.DataFrame(
        {
            "player_id": ["home_1"],
            "epv_added_on_puck": [0.0299999],
            "epv_added_off_puck": [0.0],
            "epv_added_total": [0.0299999],
        }
    )
    possession = Possession("g1", Team.HOME, start, end)
    return PossessionAnalysis(possession, features, epv, attribution)


def build_tracking(n=4):
    return make_tracking(
        {
            i: {
                "home_1": (10.123456 + i, 5.0),
                "away_1": (20.0, -5.0),
                "puck": (10.0 + i, 5.0),
            }
            for i in range(n)
        }
    )


class TestPossessionPayload:
    def test_structure_of_arrays_layout(self):
        payload = possession_payload(build_analysis(), build_tracking())
        assert payload["frames"] == [0, 1, 2, 3]
        entity_ids = [e["id"] for e in payload["entities"]]
        assert entity_ids == ["away_1", "home_1", "puck"]
        assert len(payload["x"]) == 3  # one row per entity
        assert all(len(row) == 4 for row in payload["x"])

    def test_coordinates_quantized_to_decifeet(self):
        payload = possession_payload(build_analysis(), build_tracking())
        home_idx = [e["id"] for e in payload["entities"]].index("home_1")
        assert payload["x"][home_idx][0] == 10.1

    def test_probabilities_quantized_to_4_decimals(self):
        payload = possession_payload(build_analysis(), build_tracking())
        assert payload["series"]["epv"][0] == 0.0512
        assert payload["attribution"][0]["total"] == 0.03

    def test_epv_alignment_enforced(self):
        base = build_analysis(end=3)
        stretched = PossessionAnalysis(
            Possession("g1", Team.HOME, 0, 5),  # span wider than the EPV series
            base.features,
            base.epv,
            base.attribution,
        )
        with pytest.raises(ValueError, match="do not align"):
            possession_payload(stretched, build_tracking(n=6))

    def test_missing_entity_frames_rejected(self):
        tracking = build_tracking()
        tracking = tracking[
            ~((tracking["entity_id"] == "away_1") & (tracking["frame_id"] == 2))
        ]
        with pytest.raises(ValueError, match="missing frames"):
            possession_payload(build_analysis(), tracking)


class TestGamePayload:
    def test_envelope_carries_version_rink_and_sorted_possessions(self):
        analyses = [build_analysis()]
        payload = game_payload("g1", build_tracking(), analyses)
        assert payload["version"] == PAYLOAD_VERSION
        assert payload["gameId"] == "g1"
        assert payload["rink"]["goalLineX"] == 89.0
        assert len(payload["possessions"]) == 1

    def test_requires_at_least_one_analysis(self):
        with pytest.raises(ValueError, match="at least one"):
            game_payload("g1", build_tracking(), [])

    def test_payload_is_json_serializable(self):
        payload = game_payload("g1", build_tracking(), [build_analysis()])
        parsed = json.loads(json.dumps(payload))
        assert parsed["possessions"][0]["team"] == "home"


class TestWriteGameJson:
    def test_writes_minified_json_and_creates_dirs(self, tmp_path):
        payload = game_payload("g1", build_tracking(), [build_analysis()])
        out = write_game_json(payload, tmp_path / "data" / "demo.json")
        text = out.read_text()
        assert ": " not in text  # minified
        assert json.loads(text)["gameId"] == "g1"
