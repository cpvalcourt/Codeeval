import { describe, expect, it } from "vitest";

import { samplePositions, trailPositions } from "../lib/interpolate";
import { makeRinkTransform } from "../lib/rinkTransform";
import { makeGame, makePossession } from "../lib/testFixtures";
import { LIGHT } from "../lib/theme";
import { drawEntities, drawTrails, Trail } from "./drawEntities";
import { makeStubContext } from "./stubContext";

const GAME = makeGame();
const TR = makeRinkTransform(GAME.rink, 800, 400);

describe("drawEntities", () => {
  it("draws one mark per entity: circles for skater+puck, rect for goalie", () => {
    const { ctx, count } = makeStubContext();
    const samples = samplePositions(makePossession(), 0);
    drawEntities(ctx, TR, samples, LIGHT);
    expect(count("arc")).toBe(2); // skater + puck
    expect(count("rect")).toBe(1); // goalie square
    expect(count("fill")).toBe(3);
  });

  it("labels skaters with their jersey number", () => {
    const { ctx, calls } = makeStubContext();
    drawEntities(ctx, TR, samplePositions(makePossession(), 0), LIGHT);
    const texts = calls.filter((c) => c.method === "fillText");
    expect(texts).toHaveLength(1); // only the skater, not goalie/puck
    expect(texts[0].args[0]).toBe("1");
  });

  it("uses team colors for fills", () => {
    const { ctx, calls } = makeStubContext();
    drawEntities(ctx, TR, samplePositions(makePossession(), 0), LIGHT);
    const fillColors = calls
      .filter((c) => c.method === "set:fillStyle")
      .map((c) => c.args[0]);
    expect(fillColors).toContain(LIGHT.home);
    expect(fillColors).toContain(LIGHT.away);
    expect(fillColors).toContain(LIGHT.inkPrimary); // puck
  });
});

describe("drawTrails", () => {
  function trailsFor(cursor: number, length: number): Trail[] {
    const p = makePossession();
    return p.entities.map((_, e) => ({
      entityIndex: e,
      points: trailPositions(p, e, cursor, length),
    }));
  }

  it("draws fading segments for each entity trail", () => {
    const { ctx, count } = makeStubContext();
    const samples = samplePositions(makePossession(), 3);
    drawTrails(ctx, TR, samples, trailsFor(3, 4), LIGHT);
    // 3 entities x 4 segments (4 stored points + cursor point - 1).
    expect(count("stroke")).toBe(12);
  });

  it("skips degenerate single-point trails without drawing", () => {
    const { ctx, count } = makeStubContext();
    const samples = samplePositions(makePossession(), 0);
    const trails: Trail[] = [{ entityIndex: 0, points: [{ x: 0, y: 0 }] }];
    drawTrails(ctx, TR, samples, trails, LIGHT);
    expect(count("stroke")).toBe(0);
  });

  it("restores globalAlpha to 1 after fading", () => {
    const { ctx, calls } = makeStubContext();
    const samples = samplePositions(makePossession(), 3);
    drawTrails(ctx, TR, samples, trailsFor(3, 3), LIGHT);
    const alphaWrites = calls.filter((c) => c.method === "set:globalAlpha");
    expect(alphaWrites[alphaWrites.length - 1].args[0]).toBe(1);
  });
});
