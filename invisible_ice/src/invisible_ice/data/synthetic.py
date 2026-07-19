"""Deterministic, physics-plausible synthetic tracking data (Phase 1).

Stands in for real feeds (e.g. Stathletes Big Data Cup) so the entire
pipeline can be developed and tested offline. Emits canonical-schema
tracking and event dataframes: the home team attacks toward positive x,
skaters move with bounded acceleration toward tactical targets, defenders
play man coverage between their check and the net, and the puck is either
carried, in pass flight, or in shot flight.

Everything is driven by a seeded ``numpy`` generator, so a given seed
always produces identical data — a requirement for reproducible tests.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..config import RinkConfig
from ..domain import EventType, Position, Team
from .schema import validate_events, validate_tracking

HOME_SKATERS = [f"home_{i}" for i in range(1, 6)]
AWAY_SKATERS = [f"away_{i}" for i in range(1, 6)]
PUCK_ID = "puck"


@dataclass(frozen=True)
class SyntheticConfig:
    n_possessions: int = 6
    min_frames_per_possession: int = 45
    max_frames_per_possession: int = 240
    max_skater_speed: float = 32.0  # ft/s
    skater_accel: float = 18.0  # ft/s^2 toward target
    pass_speed: float = 80.0  # ft/s
    shot_speed: float = 95.0  # ft/s
    p_pass: float = 0.02  # per-frame pass probability while carried
    p_shot_base: float = 0.012  # per-frame shot probability scale
    p_turnover: float = 0.004  # per-frame turnover probability


class SyntheticGameGenerator:
    """Generates one or more games of canonical tracking + event data."""

    def __init__(
        self,
        rink: RinkConfig | None = None,
        frame_rate: float = 30.0,
        seed: int = 0,
        config: SyntheticConfig | None = None,
    ):
        self._rink = rink or RinkConfig()
        self._frame_rate = frame_rate
        self._rng = np.random.default_rng(seed)
        self._config = config or SyntheticConfig()

    def generate_game(
        self, game_id: str, period: int = 1
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Return (tracking, events) for one game of home-team possessions."""
        tracking_rows: list[dict] = []
        event_rows: list[dict] = []
        frame_offset = 0
        for _ in range(self._config.n_possessions):
            frames, events = self._simulate_possession(frame_offset)
            tracking_rows.extend(frames)
            event_rows.extend(events)
            frame_offset = frames[-1]["frame_id"] + 1

        tracking = pd.DataFrame.from_records(tracking_rows)
        tracking["game_id"] = game_id
        tracking["period"] = period
        tracking["timestamp"] = tracking["frame_id"] / self._frame_rate

        events = pd.DataFrame.from_records(event_rows)
        events["game_id"] = game_id
        events["team"] = Team.HOME.value
        return validate_tracking(tracking), validate_events(events)

    # ------------------------------------------------------------------
    # possession simulation
    # ------------------------------------------------------------------

    def _simulate_possession(
        self, frame_offset: int
    ) -> tuple[list[dict], list[dict]]:
        rng, cfg, rink = self._rng, self._config, self._rink
        dt = 1.0 / self._frame_rate
        net = np.array(rink.attacking_net)

        pos = self._initial_positions()
        vel = {e: np.zeros(2) for e in pos}
        targets = {e: self._draw_attack_target() for e in HOME_SKATERS}
        coverage = dict(zip(AWAY_SKATERS, HOME_SKATERS))  # man-to-man

        carrier = HOME_SKATERS[int(rng.integers(len(HOME_SKATERS)))]
        pos[PUCK_ID] = pos[carrier].copy()
        puck_mode = "carried"
        receiver: str | None = None
        shot_will_score = False

        frames: list[dict] = []
        events: list[dict] = []
        n_frames = int(
            rng.integers(cfg.min_frames_per_possession, cfg.max_frames_per_possession)
        )

        for i in range(n_frames):
            frame_id = frame_offset + i

            # Re-draw attacker intentions occasionally so play evolves.
            for skater in HOME_SKATERS:
                if rng.random() < 1.0 / 60.0:
                    targets[skater] = self._draw_attack_target()

            # Skater dynamics: bounded acceleration toward each target.
            for skater in HOME_SKATERS:
                self._steer(pos, vel, skater, targets[skater], dt)
            for defender, check in coverage.items():
                cover_point = 0.55 * pos[check] + 0.45 * net
                self._steer(pos, vel, defender, cover_point, dt)
            # Goalies hold their crease, tracking the puck laterally.
            pos["away_goalie"] = np.array(
                [rink.goal_line_x - 2.0, float(np.clip(pos[PUCK_ID][1] * 0.25, -3.5, 3.5))]
            )
            pos["home_goalie"] = np.array([-rink.goal_line_x + 2.0, 0.0])

            # Puck dynamics.
            if puck_mode == "carried":
                pos[PUCK_ID] = pos[carrier] + rng.normal(0.0, 0.3, size=2)
            elif puck_mode == "pass":
                assert receiver is not None
                arrived = self._fly(pos, PUCK_ID, pos[receiver], cfg.pass_speed, dt)
                if arrived:
                    carrier, puck_mode, receiver = receiver, "carried", None
            elif puck_mode == "shot":
                self._fly(pos, PUCK_ID, net, cfg.shot_speed, dt)

            frames.extend(self._emit_frame(frame_id, pos))

            # Resolve an in-flight shot reaching the goal line.
            if puck_mode == "shot" and pos[PUCK_ID][0] >= rink.goal_line_x - 0.5:
                if shot_will_score:
                    events.append(self._event(frame_id, EventType.GOAL, carrier))
                break

            # Decide the carrier's next micro-action.
            if puck_mode == "carried":
                action_events, puck_mode, receiver, shot_will_score = self._decide(
                    frame_id, pos, carrier
                )
                events.extend(action_events)
                if action_events and action_events[-1]["event_type"] == "turnover":
                    break
        else:
            # Possession timed out without a terminal event: log a turnover
            # so every possession has a terminal label.
            events.append(self._event(frames[-1]["frame_id"], EventType.TURNOVER, carrier))

        return frames, events

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _initial_positions(self) -> dict[str, np.ndarray]:
        rng, rink = self._rng, self._rink
        pos: dict[str, np.ndarray] = {}
        for skater in HOME_SKATERS:
            pos[skater] = np.array(
                [rng.uniform(-10.0, 20.0), rng.uniform(rink.y_min + 5, rink.y_max - 5)]
            )
        for defender in AWAY_SKATERS:
            pos[defender] = np.array(
                [rng.uniform(30.0, 70.0), rng.uniform(rink.y_min + 5, rink.y_max - 5)]
            )
        pos["away_goalie"] = np.array([rink.goal_line_x - 2.0, 0.0])
        pos["home_goalie"] = np.array([-rink.goal_line_x + 2.0, 0.0])
        return pos

    def _draw_attack_target(self) -> np.ndarray:
        rng, rink = self._rng, self._rink
        return np.array(
            [
                rng.uniform(rink.blue_line_x, rink.goal_line_x - 5.0),
                rng.uniform(-25.0, 25.0),
            ]
        )

    def _steer(
        self,
        pos: dict[str, np.ndarray],
        vel: dict[str, np.ndarray],
        entity: str,
        target: np.ndarray,
        dt: float,
    ) -> None:
        cfg, rink, rng = self._config, self._rink, self._rng
        to_target = target - pos[entity]
        dist = float(np.linalg.norm(to_target))
        if dist > 1e-6:
            accel = cfg.skater_accel * to_target / dist
        else:
            accel = np.zeros(2)
        vel[entity] = vel[entity] + accel * dt + rng.normal(0.0, 0.4, size=2)
        speed = float(np.linalg.norm(vel[entity]))
        if speed > cfg.max_skater_speed:
            vel[entity] *= cfg.max_skater_speed / speed
        pos[entity] = pos[entity] + vel[entity] * dt
        pos[entity][0] = float(np.clip(pos[entity][0], rink.x_min + 1, rink.x_max - 1))
        pos[entity][1] = float(np.clip(pos[entity][1], rink.y_min + 1, rink.y_max - 1))

    @staticmethod
    def _fly(
        pos: dict[str, np.ndarray],
        entity: str,
        target: np.ndarray,
        speed: float,
        dt: float,
    ) -> bool:
        """Advance a flying puck toward ``target``; True once it arrives."""
        to_target = target - pos[entity]
        dist = float(np.linalg.norm(to_target))
        step = speed * dt
        if dist <= step:
            pos[entity] = target.copy()
            return True
        pos[entity] = pos[entity] + to_target / dist * step
        return False

    def _decide(
        self, frame_id: int, pos: dict[str, np.ndarray], carrier: str
    ) -> tuple[list[dict], str, str | None, bool]:
        """Sample the carrier's action; returns (events, puck_mode, receiver, will_score)."""
        rng, cfg, rink = self._rng, self._config, self._rink
        net = np.array(rink.attacking_net)
        dist_to_net = float(np.linalg.norm(net - pos[carrier]))
        in_zone = pos[carrier][0] > rink.blue_line_x

        p_shot = cfg.p_shot_base * max(0.0, 1.0 - dist_to_net / 70.0) if in_zone else 0.0
        roll = rng.random()
        if roll < p_shot:
            will_score = rng.random() < 0.55 * np.exp(-dist_to_net / 20.0)
            return [self._event(frame_id, EventType.SHOT, carrier)], "shot", None, will_score
        if roll < p_shot + cfg.p_pass:
            teammates = [s for s in HOME_SKATERS if s != carrier]
            receiver = teammates[int(rng.integers(len(teammates)))]
            return [self._event(frame_id, EventType.PASS, carrier)], "pass", receiver, False
        if roll < p_shot + cfg.p_pass + cfg.p_turnover:
            return [self._event(frame_id, EventType.TURNOVER, carrier)], "carried", None, False
        return [], "carried", None, False

    @staticmethod
    def _event(frame_id: int, event_type: EventType, player_id: str) -> dict:
        return {
            "frame_id": frame_id,
            "event_type": event_type.value,
            "player_id": player_id,
        }

    def _emit_frame(self, frame_id: int, pos: dict[str, np.ndarray]) -> list[dict]:
        rows = []
        for entity_id, xy in pos.items():
            if entity_id == PUCK_ID:
                team, position = "none", Position.PUCK.value
            else:
                team = Team.HOME.value if entity_id.startswith("home") else Team.AWAY.value
                position = (
                    Position.GOALIE.value if "goalie" in entity_id else Position.SKATER.value
                )
            rows.append(
                {
                    "frame_id": frame_id,
                    "entity_id": entity_id,
                    "team": team,
                    "position": position,
                    "x": float(xy[0]),
                    "y": float(xy[1]),
                }
            )
        return rows
