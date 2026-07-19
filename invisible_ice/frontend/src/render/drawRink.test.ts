import { describe, expect, it } from "vitest";

import { makeRinkTransform } from "../lib/rinkTransform";
import { makeGame } from "../lib/testFixtures";
import { DARK, LIGHT } from "../lib/theme";
import { drawRink } from "./drawRink";
import { makeStubContext } from "./stubContext";

const RINK = makeGame().rink;
const TR = makeRinkTransform(RINK, 800, 400);

describe("drawRink", () => {
  it("clears the full viewport before drawing", () => {
    const { ctx, calls } = makeStubContext();
    drawRink(ctx, TR, RINK, LIGHT);
    expect(calls[0]).toMatchObject({ method: "clearRect", args: [0, 0, 800, 400] });
  });

  it("draws the ice sheet, zone lines, circles, creases and royal road", () => {
    const { ctx, count } = makeStubContext();
    drawRink(ctx, TR, RINK, LIGHT);
    expect(count("roundRect")).toBe(1);
    // 5 zone/goal lines + 2 crease outlines + circle + royal road + sheet.
    expect(count("stroke")).toBeGreaterThanOrEqual(9);
    expect(count("setLineDash")).toBe(2); // dash on, dash off
  });

  it("renders with either theme palette without error", () => {
    for (const palette of [LIGHT, DARK]) {
      const { ctx, calls } = makeStubContext();
      drawRink(ctx, TR, RINK, palette);
      const fills = calls
        .filter((c) => c.method === "set:fillStyle")
        .map((c) => c.args[0]);
      expect(fills).toContain(palette.surface);
    }
  });
});
