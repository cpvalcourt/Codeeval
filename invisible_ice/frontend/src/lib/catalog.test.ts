import { describe, expect, it, vi } from "vitest";

import { DEMO_FILE, loadCatalog, loadGame } from "./catalog";
import { PayloadError } from "./payload";
import { makeGame } from "./testFixtures";

function respond(body: unknown, ok = true, status = 200): Response {
  return { ok, status, json: async () => body } as Response;
}

const MANIFEST = {
  version: 1,
  games: [
    { gameId: "g1", file: "g1.json", possessions: 4, seconds: 60, peakEpv: 0.3 },
    { gameId: "g2", file: "g2.json", possessions: 2, seconds: 30, peakEpv: 0.2 },
  ],
};

describe("loadCatalog", () => {
  it("returns the manifest's games when index.json exists", async () => {
    const games = await loadCatalog("/data/", async () => respond(MANIFEST));
    expect(games.map((g) => g.gameId)).toEqual(["g1", "g2"]);
  });

  it("falls back to the demo when index.json is absent", async () => {
    const games = await loadCatalog("/data/", async () =>
      respond(null, false, 404)
    );
    expect(games).toHaveLength(1);
    expect(games[0].file).toBe(DEMO_FILE);
  });

  it("falls back to the demo when the fetch itself rejects", async () => {
    const games = await loadCatalog("/data/", async () => {
      throw new Error("offline");
    });
    expect(games[0].file).toBe(DEMO_FILE);
  });

  it("rejects a malformed manifest rather than hiding it", async () => {
    await expect(
      loadCatalog("/data/", async () => respond({ version: 1, games: [] }))
    ).rejects.toBeInstanceOf(PayloadError);
    await expect(
      loadCatalog("/data/", async () => respond({ version: 99, games: [] }))
    ).rejects.toThrow(/unsupported manifest version/);
  });

  it("rejects unsafe file paths in the manifest", async () => {
    const evil = { version: 1, games: [{ gameId: "x", file: "../../etc/passwd" }] };
    await expect(
      loadCatalog("/data/", async () => respond(evil))
    ).rejects.toThrow(/unsafe file path/);
  });

  it("requests index.json relative to the base url", async () => {
    const fetcher = vi.fn(async () => respond(MANIFEST));
    await loadCatalog("/base/data/", fetcher);
    expect(fetcher).toHaveBeenCalledWith("/base/data/index.json");
  });
});

describe("loadGame", () => {
  it("fetches and validates a payload", async () => {
    const game = await loadGame("/data/", "g1.json", async () =>
      respond(makeGame({ gameId: "g1" }))
    );
    expect(game.gameId).toBe("g1");
  });

  it("throws on HTTP errors", async () => {
    await expect(
      loadGame("/data/", "missing.json", async () => respond(null, false, 404))
    ).rejects.toThrow(/HTTP 404/);
  });

  it("propagates payload validation errors", async () => {
    await expect(
      loadGame("/data/", "bad.json", async () => respond({ version: 42 }))
    ).rejects.toBeInstanceOf(PayloadError);
  });
});
