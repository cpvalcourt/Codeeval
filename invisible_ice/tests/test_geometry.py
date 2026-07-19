import numpy as np

from invisible_ice.features.geometry import (
    angle_to_target,
    distance,
    point_segment_distance,
)


class TestPointSegmentDistance:
    def test_perpendicular_foot_inside_segment(self):
        d = point_segment_distance(np.array([[5.0, 3.0]]), (0.0, 0.0), (10.0, 0.0))
        assert np.isclose(d[0], 3.0)

    def test_point_beyond_endpoint_uses_endpoint_distance(self):
        d = point_segment_distance(np.array([[13.0, 4.0]]), (0.0, 0.0), (10.0, 0.0))
        assert np.isclose(d[0], 5.0)  # 3-4-5 to endpoint (10, 0)

    def test_point_before_start_uses_start_distance(self):
        d = point_segment_distance(np.array([[-3.0, 4.0]]), (0.0, 0.0), (10.0, 0.0))
        assert np.isclose(d[0], 5.0)

    def test_degenerate_segment_is_point_distance(self):
        d = point_segment_distance(np.array([[3.0, 4.0]]), (0.0, 0.0), (0.0, 0.0))
        assert np.isclose(d[0], 5.0)

    def test_vectorized_over_points(self):
        pts = np.array([[5.0, 1.0], [5.0, -2.0], [20.0, 0.0]])
        d = point_segment_distance(pts, (0.0, 0.0), (10.0, 0.0))
        assert np.allclose(d, [1.0, 2.0, 10.0])

    def test_point_on_segment_is_zero(self):
        d = point_segment_distance(np.array([[4.0, 0.0]]), (0.0, 0.0), (10.0, 0.0))
        assert np.isclose(d[0], 0.0)


class TestScalarHelpers:
    def test_distance(self):
        assert distance((0.0, 0.0), (3.0, 4.0)) == 5.0

    def test_angle_straight_ahead_is_zero(self):
        assert angle_to_target((0.0, 0.0), (10.0, 0.0)) == 0.0

    def test_angle_signs(self):
        assert angle_to_target((0.0, 0.0), (0.0, 10.0)) > 0
        assert angle_to_target((0.0, 0.0), (0.0, -10.0)) < 0
