import { useEffect, useMemo, useState } from "react";

import { AttributionTable } from "./components/AttributionTable";
import { Controls } from "./components/Controls";
import { EPVChart } from "./components/EPVChart";
import { PossessionPicker } from "./components/PossessionPicker";
import { RinkCanvas } from "./components/RinkCanvas";
import { usePlayback } from "./hooks/usePlayback";
import { parseGamePayload } from "./lib/payload";
import { sampleSeries } from "./lib/interpolate";
import { paletteFor } from "./lib/theme";
import { GamePayload } from "./lib/types";

function useDarkMode(): boolean {
  const [dark, setDark] = useState(
    () => window.matchMedia("(prefers-color-scheme: dark)").matches
  );
  useEffect(() => {
    const query = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = (e: MediaQueryListEvent) => setDark(e.matches);
    query.addEventListener("change", onChange);
    return () => query.removeEventListener("change", onChange);
  }, []);
  return dark;
}

function Viewer({ game }: { game: GamePayload }) {
  const [selected, setSelected] = useState(0);
  const dark = useDarkMode();
  const palette = paletteFor(dark);

  const possession = game.possessions[selected];
  const playback = usePlayback(possession.frames.length, game.frameRate);
  const liveEpv = sampleSeries(possession.series.epv, playback.cursor);

  return (
    <>
      <PossessionPicker
        possessions={game.possessions}
        selected={selected}
        frameRate={game.frameRate}
        onSelect={setSelected}
      />
      <section className="card">
        <div className="rink-header">
          <div className="legend" aria-label="Legend">
            <span className="legend-item">
              <span className="swatch home" aria-hidden="true" /> Home (attacking →)
            </span>
            <span className="legend-item">
              <span className="swatch away" aria-hidden="true" /> Away
            </span>
            <span className="legend-item">
              <span className="swatch goalie" aria-hidden="true" /> Goalie
            </span>
            <span className="legend-item">
              <span className="swatch puck" aria-hidden="true" /> Puck
            </span>
          </div>
          <div className="live-epv">
            <span className="live-epv-label">EPV now</span>
            <span className="live-epv-value">{liveEpv.toFixed(3)}</span>
          </div>
        </div>
        <RinkCanvas
          possession={possession}
          rink={game.rink}
          cursor={playback.cursor}
          palette={palette}
        />
        <Controls
          playback={playback}
          frameCount={possession.frames.length}
          frameRate={game.frameRate}
        />
      </section>
      <section className="card">
        <h2>Expected Possession Value</h2>
        <p className="hint">Hover to inspect · click anywhere on the curve to jump the replay</p>
        <EPVChart
          possession={possession}
          frameRate={game.frameRate}
          cursor={playback.cursor}
          onSeek={playback.seek}
        />
      </section>
      <section className="card">
        <h2>Player attribution</h2>
        <AttributionTable rows={possession.attribution} />
      </section>
    </>
  );
}

export default function App() {
  const [game, setGame] = useState<GamePayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  const dataUrl = useMemo(() => `${import.meta.env.BASE_URL}data/demo.json`, []);

  useEffect(() => {
    let cancelled = false;
    fetch(dataUrl)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status} loading ${dataUrl}`);
        return res.json();
      })
      .then((raw) => {
        if (!cancelled) setGame(parseGamePayload(raw));
      })
      .catch((err) => {
        if (!cancelled) setError(String(err));
      });
    return () => {
      cancelled = true;
    };
  }, [dataUrl]);

  return (
    <main className="app">
      <header className="masthead">
        <h1>Invisible Ice</h1>
        <p className="subtitle">
          Framewise Expected Possession Value {game ? `· ${game.gameId}` : ""}
        </p>
      </header>
      {error && <p className="error">Failed to load game data: {error}</p>}
      {!error && !game && <p className="hint">Loading game data…</p>}
      {game && <Viewer game={game} />}
    </main>
  );
}
