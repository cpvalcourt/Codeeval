"""Core domain vocabulary: enums and value objects used by every layer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Team(StrEnum):
    HOME = "home"
    AWAY = "away"

    @property
    def opponent(self) -> "Team":
        return Team.AWAY if self is Team.HOME else Team.HOME


class Position(StrEnum):
    SKATER = "skater"
    GOALIE = "goalie"
    PUCK = "puck"


class PuckState(StrEnum):
    """Output states of the possession state machine."""

    HOME = "home"
    AWAY = "away"
    LOOSE = "loose"


class Action(StrEnum):
    """Transition-model classes: what the possessing team does next."""

    SHOOT = "shoot"
    PASS = "pass"
    KEEP = "keep"
    TURNOVER = "turnover"


class EventType(StrEnum):
    """Discrete events recorded alongside tracking data."""

    PASS = "pass"
    SHOT = "shot"
    GOAL = "goal"
    TURNOVER = "turnover"


@dataclass(frozen=True)
class Possession:
    """A contiguous span of frames controlled by one team."""

    game_id: str
    team: Team
    start_frame: int
    end_frame: int

    @property
    def n_frames(self) -> int:
        return self.end_frame - self.start_frame + 1

    def __post_init__(self) -> None:
        if self.end_frame < self.start_frame:
            raise ValueError(
                f"end_frame {self.end_frame} precedes start_frame {self.start_frame}"
            )
