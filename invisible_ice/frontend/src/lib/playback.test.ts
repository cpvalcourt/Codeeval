import { describe, expect, it } from "vitest";

import { PlaybackEngine } from "./playback";

describe("PlaybackEngine", () => {
  it("does not advance while paused", () => {
    const engine = new PlaybackEngine(100, 30);
    expect(engine.tick(1)).toBe(0);
  });

  it("advances by dt * frameRate * speed while playing", () => {
    const engine = new PlaybackEngine(100, 30);
    engine.play();
    expect(engine.tick(0.5)).toBeCloseTo(15);
    engine.setSpeed(2);
    expect(engine.tick(0.5)).toBeCloseTo(45);
  });

  it("loops by default at the end of the clip", () => {
    const engine = new PlaybackEngine(11, 30); // lastFrame = 10
    engine.play();
    engine.seek(9);
    engine.tick(0.1); // +3 frames -> 12 -> wraps to 2
    expect(engine.cursor).toBeCloseTo(2);
    expect(engine.playing).toBe(true);
  });

  it("pauses on the last frame when looping is off", () => {
    const engine = new PlaybackEngine(11, 30, { loop: false });
    engine.play();
    engine.seek(9);
    engine.tick(1);
    expect(engine.cursor).toBe(10);
    expect(engine.playing).toBe(false);
  });

  it("restarts from the beginning when replayed from the end", () => {
    const engine = new PlaybackEngine(11, 30, { loop: false });
    engine.seek(10);
    engine.play();
    expect(engine.cursor).toBe(0);
  });

  it("clamps seeks into range", () => {
    const engine = new PlaybackEngine(11, 30);
    engine.seek(-4);
    expect(engine.cursor).toBe(0);
    engine.seek(99);
    expect(engine.cursor).toBe(10);
  });

  it("toggle flips play state", () => {
    const engine = new PlaybackEngine(11, 30);
    engine.toggle();
    expect(engine.playing).toBe(true);
    engine.toggle();
    expect(engine.playing).toBe(false);
  });

  it("setFrameCount clamps the cursor into the new clip", () => {
    const engine = new PlaybackEngine(100, 30);
    engine.seek(80);
    engine.setFrameCount(21);
    expect(engine.cursor).toBe(20);
  });

  it("rejects invalid construction and speeds", () => {
    expect(() => new PlaybackEngine(0, 30)).toThrow();
    expect(() => new PlaybackEngine(10, 0)).toThrow();
    const engine = new PlaybackEngine(10, 30);
    expect(() => engine.setSpeed(0)).toThrow();
  });
});
