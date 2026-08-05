/** Wire types for the engine's game payload (see src/invisible_ice/export.py). */

export const SUPPORTED_PAYLOAD_VERSION = 1;

export interface RinkDims {
  xMin: number;
  xMax: number;
  yMin: number;
  yMax: number;
  goalLineX: number;
  blueLineX: number;
}

export type TeamId = "home" | "away" | "none";
export type PositionKind = "skater" | "goalie" | "puck";

export interface EntityMeta {
  id: string;
  team: TeamId;
  position: PositionKind;
}

export const SERIES_NAMES = [
  "epv",
  "xg",
  "p_shoot",
  "p_pass",
  "p_keep",
  "p_turnover",
] as const;
export type SeriesName = (typeof SERIES_NAMES)[number];

export interface AttributionRow {
  playerId: string;
  onPuck: number;
  offPuck: number;
  total: number;
}

export interface PossessionData {
  team: string;
  startFrame: number;
  endFrame: number;
  entities: EntityMeta[];
  frames: number[];
  /** x[entityIndex][frameIndex], canonical feet. */
  x: number[][];
  y: number[][];
  series: Record<SeriesName, number[]>;
  attribution: AttributionRow[];
}

export interface GamePayload {
  version: number;
  gameId: string;
  frameRate: number;
  rink: RinkDims;
  possessions: PossessionData[];
}

/** A dot on the ice at a (possibly interpolated) moment. */
export interface EntitySample {
  id: string;
  team: TeamId;
  position: PositionKind;
  x: number;
  y: number;
}

/** One row of data/index.json — the catalog of available games. */
export interface ManifestEntry {
  gameId: string;
  file: string;
  possessions: number;
  seconds: number;
  peakEpv: number;
}

export interface Manifest {
  version: number;
  games: ManifestEntry[];
}
