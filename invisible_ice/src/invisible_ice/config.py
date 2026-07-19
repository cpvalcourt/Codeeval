"""Immutable configuration objects shared across the pipeline.

All spatial quantities are expressed in the canonical rink coordinate
system: x in [-100, 100] (feet, along the length of the ice) and
y in [-42.5, 42.5] (feet, across the ice), with the attacking team
always moving toward positive x after direction normalization.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RinkConfig:
    """Geometry of the canonical NHL rink."""

    x_min: float = -100.0
    x_max: float = 100.0
    y_min: float = -42.5
    y_max: float = 42.5
    #: Goal line is 11 ft from the end boards.
    goal_line_x: float = 89.0
    #: Offensive blue line is 25 ft from center ice.
    blue_line_x: float = 25.0

    @property
    def attacking_net(self) -> tuple[float, float]:
        """Location of the net the attacking team shoots at."""
        return (self.goal_line_x, 0.0)

    def contains(self, x: float, y: float) -> bool:
        return self.x_min <= x <= self.x_max and self.y_min <= y <= self.y_max


@dataclass(frozen=True)
class PossessionConfig:
    """Tuning knobs for the rule-based possession state machine."""

    #: A skater within this many feet of the puck is a control candidate.
    control_radius: float = 4.0
    #: Consecutive frames of control needed before possession flips.
    min_control_frames: int = 3
    #: Consecutive frames with no control candidate before the puck is loose.
    loose_frames: int = 5


@dataclass(frozen=True)
class KinematicsConfig:
    """Parameters for finite-difference kinematics."""

    frame_rate: float = 30.0

    @property
    def dt(self) -> float:
        return 1.0 / self.frame_rate


@dataclass(frozen=True)
class LaneConfig:
    """Parameters mapping raw lane geometry to an openness score."""

    #: Perpendicular distance (ft) at which a defender fully closes a lane.
    closed_distance: float = 3.0
    #: Distance scale (ft) of the logistic openness curve. A defender on the
    #: lane line scores ~0.12; one stick-length (~6 ft) off scores ~0.88.
    distance_scale: float = 1.5
    #: Openness above this threshold counts the lane as "open".
    open_threshold: float = 0.5


@dataclass(frozen=True)
class LabelConfig:
    """Horizon used when deriving per-frame action labels from events."""

    #: Frames of look-ahead when assigning the next-action label.
    horizon_frames: int = 15
