/** Shared hand-built fixtures for frontend unit tests. */

import { GamePayload, PossessionData } from "./types";

export function makePossession(overrides: Partial<PossessionData> = {}): PossessionData {
  const base: PossessionData = {
    team: "home",
    startFrame: 0,
    endFrame: 3,
    entities: [
      { id: "home_1", team: "home", position: "skater" },
      { id: "away_goalie", team: "away", position: "goalie" },
      { id: "puck", team: "none", position: "puck" },
    ],
    frames: [0, 1, 2, 3],
    x: [
      [0, 10, 20, 30],
      [87, 87, 87, 87],
      [0, 10, 20, 30],
    ],
    y: [
      [0, 0, 10, 10],
      [0, 1, 0, -1],
      [0, 0, 10, 10],
    ],
    series: {
      epv: [0.05, 0.06, 0.08, 0.07],
      xg: [0.01, 0.02, 0.03, 0.02],
      p_shoot: [0.1, 0.1, 0.2, 0.1],
      p_pass: [0.2, 0.2, 0.2, 0.2],
      p_keep: [0.6, 0.6, 0.5, 0.6],
      p_turnover: [0.1, 0.1, 0.1, 0.1],
    },
    attribution: [
      { playerId: "home_1", onPuck: 0.02, offPuck: 0.0, total: 0.02 },
    ],
  };
  return { ...base, ...overrides };
}

export function makeGame(overrides: Partial<GamePayload> = {}): GamePayload {
  const base: GamePayload = {
    version: 1,
    gameId: "game_0",
    frameRate: 30,
    rink: {
      xMin: -100,
      xMax: 100,
      yMin: -42.5,
      yMax: 42.5,
      goalLineX: 89,
      blueLineX: 25,
    },
    possessions: [makePossession()],
  };
  return { ...base, ...overrides };
}
