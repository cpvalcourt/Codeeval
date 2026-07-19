/**
 * Payload validation at the boundary — mirrors the fail-fast philosophy of
 * the Python schema layer: parse once, then every component trusts the data.
 */

import {
  GamePayload,
  PossessionData,
  SERIES_NAMES,
  SUPPORTED_PAYLOAD_VERSION,
} from "./types";

export class PayloadError extends Error {}

function fail(message: string): never {
  throw new PayloadError(message);
}

function checkPossession(p: PossessionData, index: number): void {
  const where = `possession[${index}]`;
  const nFrames = p.frames.length;
  const nEntities = p.entities.length;
  if (nFrames === 0) fail(`${where}: no frames`);
  if (nEntities === 0) fail(`${where}: no entities`);
  if (p.x.length !== nEntities || p.y.length !== nEntities) {
    fail(`${where}: x/y rows (${p.x.length}/${p.y.length}) != entities (${nEntities})`);
  }
  for (let e = 0; e < nEntities; e++) {
    if (p.x[e].length !== nFrames || p.y[e].length !== nFrames) {
      fail(`${where}: entity ${p.entities[e].id} coordinate length != frames`);
    }
  }
  for (const name of SERIES_NAMES) {
    const series = p.series?.[name];
    if (!Array.isArray(series) || series.length !== nFrames) {
      fail(`${where}: series '${name}' missing or misaligned`);
    }
  }
}

/** Validate a fetched payload; throws PayloadError on any inconsistency. */
export function parseGamePayload(raw: unknown): GamePayload {
  const p = raw as GamePayload;
  if (typeof p !== "object" || p === null) fail("payload is not an object");
  if (p.version !== SUPPORTED_PAYLOAD_VERSION) {
    fail(`unsupported payload version ${p.version} (expected ${SUPPORTED_PAYLOAD_VERSION})`);
  }
  if (!p.rink || typeof p.rink.xMin !== "number") fail("missing rink dimensions");
  if (!(p.frameRate > 0)) fail("frameRate must be positive");
  if (!Array.isArray(p.possessions) || p.possessions.length === 0) {
    fail("payload has no possessions");
  }
  p.possessions.forEach(checkPossession);
  return p;
}
