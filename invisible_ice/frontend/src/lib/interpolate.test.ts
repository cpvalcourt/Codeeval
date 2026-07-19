import { describe, expect, it } from "vitest";

import { clampCursor, samplePositions, sampleSeries, trailPositions } from "./interpolate";
import { makePossession } from "./testFixtures";

describe("samplePositions", () => {
  it("returns exact positions at integer frames", () => {
    const samples = samplePositions(makePossession(), 2);
    expect(samples[0]).toMatchObject({ id: "home_1", x: 20, y: 10 });
  });

  it("linearly interpolates between frames", () => {
    const samples = samplePositions(makePossession(), 0.5);
    expect(samples[0].x).toBeCloseTo(5);
    expect(samples[0].y).toBeCloseTo(0);
  });

  it("clamps cursors outside the clip", () => {
    const p = makePossession();
    expect(samplePositions(p, -5)[0].x).toBe(0);
    expect(samplePositions(p, 99)[0].x).toBe(30);
  });

  it("carries entity metadata through", () => {
    const samples = samplePositions(makePossession(), 0);
    expect(samples[1]).toMatchObject({ team: "away", position: "goalie" });
    expect(samples[2]).toMatchObject({ team: "none", position: "puck" });
  });
});

describe("trailPositions", () => {
  it("ends exactly at the interpolated cursor position", () => {
    const trail = trailPositions(makePossession(), 0, 2.5, 10);
    const last = trail[trail.length - 1];
    expect(last.x).toBeCloseTo(25);
  });

  it("limits history to the requested length", () => {
    const trail = trailPositions(makePossession(), 0, 3, 2);
    // 2 stored frames + the cursor sample.
    expect(trail).toHaveLength(3);
    expect(trail[0]).toMatchObject({ x: 20 });
  });

  it("handles the start of the clip without underflow", () => {
    const trail = trailPositions(makePossession(), 0, 0, 8);
    expect(trail[0]).toMatchObject({ x: 0, y: 0 });
  });
});

describe("sampleSeries", () => {
  it("interpolates and clamps", () => {
    const values = [0.0, 0.1, 0.3];
    expect(sampleSeries(values, 0.5)).toBeCloseTo(0.05);
    expect(sampleSeries(values, 10)).toBeCloseTo(0.3);
    expect(sampleSeries([], 1)).toBe(0);
  });
});

describe("clampCursor", () => {
  it("keeps cursors in [0, frames - 1]", () => {
    const p = makePossession();
    expect(clampCursor(p, -1)).toBe(0);
    expect(clampCursor(p, 1.5)).toBe(1.5);
    expect(clampCursor(p, 100)).toBe(3);
  });
});
