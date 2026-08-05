/**
 * Resolves what the app should load: the manifest of real games when one
 * has been exported, otherwise the single bundled demo payload. Kept free
 * of React so the fallback logic is unit-testable.
 */

import { parseGamePayload, parseManifest } from "./payload";
import { GamePayload, Manifest, ManifestEntry } from "./types";

export const DEMO_FILE = "demo.json";

export type Fetcher = (url: string) => Promise<Response>;

function demoEntry(): ManifestEntry {
  return {
    gameId: "demo",
    file: DEMO_FILE,
    possessions: 0,
    seconds: 0,
    peakEpv: 0,
  };
}

/**
 * Read data/index.json if present. A missing manifest is the normal state
 * before any real export has run, so it falls back to the demo rather
 * than surfacing an error; a malformed one still throws.
 */
export async function loadCatalog(
  baseUrl: string,
  fetcher: Fetcher
): Promise<ManifestEntry[]> {
  let response: Response;
  try {
    response = await fetcher(`${baseUrl}index.json`);
  } catch {
    return [demoEntry()];
  }
  if (!response.ok) return [demoEntry()];
  return parseManifest(await response.json()).games;
}

export async function loadGame(
  baseUrl: string,
  file: string,
  fetcher: Fetcher
): Promise<GamePayload> {
  const response = await fetcher(`${baseUrl}${file}`);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status} loading ${file}`);
  }
  return parseGamePayload(await response.json());
}

export type { Manifest, ManifestEntry };
