import numpy as np
import pandas as pd

from conftest import make_tracking
from invisible_ice.features.kinematics import KINEMATIC_COLUMNS, add_kinematics


def linear_motion(vx: float, vy: float, n: int = 10, frame_rate: float = 30.0):
    dt = 1.0 / frame_rate
    return make_tracking(
        {i: {"home_1": (vx * i * dt, vy * i * dt)} for i in range(n)},
        frame_rate=frame_rate,
    )


class TestAddKinematics:
    def test_constant_velocity_recovered_exactly(self):
        out = add_kinematics(linear_motion(vx=12.0, vy=-6.0))
        assert np.allclose(out["vx"], 12.0)
        assert np.allclose(out["vy"], -6.0)
        assert np.allclose(out["speed"], np.hypot(12.0, -6.0))
        assert np.allclose(out["accel"], 0.0)

    def test_stationary_entity_has_zero_kinematics(self):
        out = add_kinematics(make_tracking({i: {"puck": (5.0, 5.0)} for i in range(5)}))
        for col in KINEMATIC_COLUMNS:
            assert np.allclose(out[col], 0.0)

    def test_constant_acceleration_recovered(self):
        dt = 1.0 / 30.0
        a = 10.0
        df = make_tracking(
            {i: {"home_1": (0.5 * a * (i * dt) ** 2, 0.0)} for i in range(12)}
        )
        out = add_kinematics(df)
        # Velocity central differences are exact for quadratics on [1:-1];
        # acceleration needs one more interior step since the endpoint
        # velocities are one-sided estimates.
        v_interior = out.iloc[1:-1]
        assert np.allclose(v_interior["vx"], a * v_interior["timestamp"].to_numpy())
        assert np.allclose(out.iloc[2:-2]["ax"], a)

    def test_single_frame_entity_defaults_to_zero(self):
        df = make_tracking({0: {"home_1": (1.0, 1.0)}})
        out = add_kinematics(df)
        assert out.loc[0, "speed"] == 0.0

    def test_entities_are_independent(self):
        moving = linear_motion(vx=10.0, vy=0.0)
        still = make_tracking({i: {"away_1": (0.0, 0.0)} for i in range(10)})
        out = add_kinematics(pd.concat([moving, still], ignore_index=True))
        assert np.allclose(out[out["entity_id"] == "home_1"]["vx"], 10.0)
        assert np.allclose(out[out["entity_id"] == "away_1"]["vx"], 0.0)

    def test_preserves_row_count_and_sorts_by_frame(self):
        df = linear_motion(vx=1.0, vy=1.0)
        out = add_kinematics(df.sample(frac=1.0, random_state=0))
        assert len(out) == len(df)
        assert out["frame_id"].is_monotonic_increasing
