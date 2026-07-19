import { describe, expect, it } from "vitest";

import { parseGamePayload, PayloadError } from "./payload";
import { makeGame, makePossession } from "./testFixtures";

describe("parseGamePayload", () => {
  it("accepts a well-formed payload", () => {
    const game = parseGamePayload(makeGame());
    expect(game.gameId).toBe("game_0");
    expect(game.possessions).toHaveLength(1);
  });

  it("rejects non-objects", () => {
    expect(() => parseGamePayload(null)).toThrow(PayloadError);
    expect(() => parseGamePayload("nope")).toThrow(PayloadError);
  });

  it("rejects unsupported versions", () => {
    expect(() => parseGamePayload(makeGame({ version: 99 }))).toThrow(
      /unsupported payload version 99/
    );
  });

  it("rejects missing rink or bad frame rate", () => {
    expect(() =>
      parseGamePayload({ ...makeGame(), rink: undefined })
    ).toThrow(/rink/);
    expect(() => parseGamePayload(makeGame({ frameRate: 0 }))).toThrow(
      /frameRate/
    );
  });

  it("rejects empty possessions", () => {
    expect(() => parseGamePayload(makeGame({ possessions: [] }))).toThrow(
      /no possessions/
    );
  });

  it("rejects coordinate rows not matching entity count", () => {
    const bad = makePossession();
    bad.x = bad.x.slice(0, 2);
    expect(() =>
      parseGamePayload(makeGame({ possessions: [bad] }))
    ).toThrow(/x\/y rows/);
  });

  it("rejects coordinate arrays not matching frame count", () => {
    const bad = makePossession();
    bad.y[0] = [0, 1];
    expect(() =>
      parseGamePayload(makeGame({ possessions: [bad] }))
    ).toThrow(/coordinate length/);
  });

  it("rejects missing or misaligned series", () => {
    const bad = makePossession();
    bad.series = { ...bad.series, epv: [0.1] };
    expect(() =>
      parseGamePayload(makeGame({ possessions: [bad] }))
    ).toThrow(/series 'epv'/);
  });
});
