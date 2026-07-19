/**
 * Frame interpolation: tracking is 30 fps but the display loop runs at the
 * monitor's refresh rate, so entity positions are sampled at fractional
 * frame cursors with linear interpolation between captured frames.
 */

import { EntitySample, PossessionData } from "./types";

/** Clamp a fractional cursor into the possession's valid range. */
export function clampCursor(p: PossessionData, cursor: number): number {
  return Math.min(Math.max(cursor, 0), p.frames.length - 1);
}

/** Positions of every entity at fractional frame index `cursor`. */
export function samplePositions(p: PossessionData, cursor: number): EntitySample[] {
  const t = clampCursor(p, cursor);
  const i0 = Math.floor(t);
  const i1 = Math.min(i0 + 1, p.frames.length - 1);
  const alpha = t - i0;
  return p.entities.map((meta, e) => ({
    ...meta,
    x: p.x[e][i0] + (p.x[e][i1] - p.x[e][i0]) * alpha,
    y: p.y[e][i0] + (p.y[e][i1] - p.y[e][i0]) * alpha,
  }));
}

/**
 * Recent path of one entity, oldest first, ending at the cursor position —
 * the renderer draws this as a fading velocity trail.
 */
export function trailPositions(
  p: PossessionData,
  entityIndex: number,
  cursor: number,
  length: number
): Array<{ x: number; y: number }> {
  const t = clampCursor(p, cursor);
  const end = Math.floor(t);
  const start = Math.max(0, end - length + 1);
  const points: Array<{ x: number; y: number }> = [];
  for (let i = start; i <= end; i++) {
    points.push({ x: p.x[entityIndex][i], y: p.y[entityIndex][i] });
  }
  const sample = samplePositions(p, t)[entityIndex];
  points.push({ x: sample.x, y: sample.y });
  return points;
}

/** Linearly interpolated value of a series at a fractional cursor. */
export function sampleSeries(values: number[], cursor: number): number {
  if (values.length === 0) return 0;
  const t = Math.min(Math.max(cursor, 0), values.length - 1);
  const i0 = Math.floor(t);
  const i1 = Math.min(i0 + 1, values.length - 1);
  return values[i0] + (values[i1] - values[i0]) * (t - i0);
}
