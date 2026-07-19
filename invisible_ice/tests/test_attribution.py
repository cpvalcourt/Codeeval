import numpy as np
import pandas as pd
import pytest

from conftest import make_tracking
from invisible_ice.domain import Team
from invisible_ice.models.attribution import (
    AttributionFrame,
    MicroAttributionEngine,
    ThreatDeltaAttribution,
)

NET = (89.0, 0.0)


def frame(delta, carrier="home_1", positions=None, prev=None):
    positions = positions or {"home_1": (50.0, 0.0), "home_2": (40.0, 10.0)}
    return AttributionFrame(
        frame_id=1,
        delta_epv=delta,
        carrier_id=carrier,
        positions=positions,
        prev_positions=prev or positions,
        net=NET,
    )


class TestThreatDeltaAttribution:
    def test_shares_conserve_delta_epv(self):
        strategy = ThreatDeltaAttribution()
        f = frame(
            0.08,
            positions={"home_1": (50.0, 0.0), "home_2": (70.0, 5.0)},
            prev={"home_1": (50.0, 0.0), "home_2": (60.0, 5.0)},
        )
        shares = strategy.attribute(f)
        assert np.isclose(sum(shares.values()), 0.08)

    def test_carrier_takes_all_when_no_offpuck_movement_aligns(self):
        shares = ThreatDeltaAttribution().attribute(frame(0.05))
        assert shares == {"home_1": pytest.approx(0.05)}

    def test_net_driving_teammate_earns_offpuck_credit(self):
        strategy = ThreatDeltaAttribution(carrier_share=0.6)
        f = frame(
            0.10,
            positions={"home_1": (50.0, 0.0), "home_2": (75.0, 0.0)},
            prev={"home_1": (50.0, 0.0), "home_2": (60.0, 0.0)},
        )
        shares = strategy.attribute(f)
        assert shares["home_1"] == pytest.approx(0.06)
        assert shares["home_2"] == pytest.approx(0.04)

    def test_negative_delta_attributed_to_retreating_teammate(self):
        strategy = ThreatDeltaAttribution(carrier_share=0.5)
        f = frame(
            -0.10,
            positions={"home_1": (50.0, 0.0), "home_2": (40.0, 0.0)},
            prev={"home_1": (50.0, 0.0), "home_2": (70.0, 0.0)},
        )
        shares = strategy.attribute(f)
        assert np.isclose(sum(shares.values()), -0.10)
        assert shares["home_2"] < 0

    def test_zero_delta_gives_no_shares(self):
        assert ThreatDeltaAttribution().attribute(frame(0.0)) == {}

    def test_loose_puck_spreads_evenly(self):
        f = frame(0.04, carrier=None)
        shares = ThreatDeltaAttribution().attribute(f)
        assert np.isclose(sum(shares.values()), 0.04)
        assert len(shares) == 2

    def test_invalid_carrier_share_rejected(self):
        with pytest.raises(ValueError):
            ThreatDeltaAttribution(carrier_share=1.5)


class TestMicroAttributionEngine:
    def test_totals_sum_to_net_epv_change(self):
        frames = {
            i: {
                "home_1": (50.0 + i, 0.0),
                "home_2": (40.0 + 2 * i, 5.0),
                "away_1": (60.0, 0.0),
                "puck": (50.0 + i, 0.0),
            }
            for i in range(4)
        }
        tracking = make_tracking(frames)
        epv = pd.DataFrame({"frame_id": range(4), "epv": [0.05, 0.07, 0.10, 0.16]})
        carrier = pd.Series({i: "home_1" for i in range(4)})
        result = MicroAttributionEngine().attribute_possession(
            epv, tracking, carrier, Team.HOME
        )
        assert np.isclose(result["epv_added_total"].sum(), 0.16 - 0.05)
        assert set(result["player_id"]) <= {"home_1", "home_2"}

    def test_on_and_off_puck_buckets_are_separated(self):
        frames = {
            i: {
                "home_1": (50.0, 0.0),  # static carrier
                "home_2": (40.0 + 10 * i, 0.0),  # drives the net
                "puck": (50.0, 0.0),
            }
            for i in range(3)
        }
        tracking = make_tracking(frames)
        epv = pd.DataFrame({"frame_id": range(3), "epv": [0.05, 0.10, 0.15]})
        carrier = pd.Series({i: "home_1" for i in range(3)})
        result = MicroAttributionEngine().attribute_possession(
            epv, tracking, carrier, Team.HOME
        ).set_index("player_id")
        assert result.loc["home_1", "epv_added_off_puck"] == 0.0
        assert result.loc["home_2", "epv_added_on_puck"] == 0.0
        assert result.loc["home_2", "epv_added_off_puck"] > 0.0
