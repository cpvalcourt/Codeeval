import { describe, expect, it } from "vitest";

import { makeRinkTransform } from "./rinkTransform";
import { makeGame } from "./testFixtures";

const RINK = makeGame().rink;

describe("makeRinkTransform", () => {
  it("maps rink corners inside the padded viewport", () => {
    const tr = makeRinkTransform(RINK, 800, 400, 10);
    const [x0, y0] = tr.toPx(RINK.xMin, RINK.yMax); // top-left corner
    const [x1, y1] = tr.toPx(RINK.xMax, RINK.yMin); // bottom-right corner
    expect(x0).toBeGreaterThanOrEqual(10);
    expect(y0).toBeGreaterThanOrEqual(10);
    expect(x1).toBeLessThanOrEqual(790);
    expect(y1).toBeLessThanOrEqual(390);
  });

  it("preserves aspect ratio (uniform scale)", () => {
    const tr = makeRinkTransform(RINK, 800, 400, 0);
    const [x0] = tr.toPx(0, 0);
    const [x1] = tr.toPx(10, 0);
    const [, y0] = tr.toPx(0, 0);
    const [, y1] = tr.toPx(0, 10);
    expect(x1 - x0).toBeCloseTo(10 * tr.scale);
    expect(y0 - y1).toBeCloseTo(10 * tr.scale);
  });

  it("flips the y axis (world up = canvas up)", () => {
    const tr = makeRinkTransform(RINK, 800, 400);
    const [, yHigh] = tr.toPx(0, 40);
    const [, yLow] = tr.toPx(0, -40);
    expect(yHigh).toBeLessThan(yLow);
  });

  it("centers the rink when the viewport is wider than needed", () => {
    const tr = makeRinkTransform(RINK, 2000, 400, 0);
    const [cx] = tr.toPx(0, 0);
    expect(cx).toBeCloseTo(1000);
  });

  it("is centered vertically for letterboxed heights", () => {
    const tr = makeRinkTransform(RINK, 400, 1000, 0);
    const [, cy] = tr.toPx(0, 0);
    expect(cy).toBeCloseTo(500);
  });
});
