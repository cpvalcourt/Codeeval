/** Playback controls: play/pause, scrubber, speed, and the clock. */

import { PlaybackControls } from "../hooks/usePlayback";

interface Props {
  playback: PlaybackControls;
  frameCount: number;
  frameRate: number;
}

function clock(seconds: number): string {
  return `${seconds.toFixed(1)}s`;
}

export function Controls({ playback, frameCount, frameRate }: Props) {
  const { cursor, playing, speed, toggle, seek, setSpeed } = playback;
  return (
    <div className="controls">
      <button className="play-button" onClick={toggle} aria-label={playing ? "Pause" : "Play"}>
        {playing ? "❚❚" : "▶"}
      </button>
      <input
        className="scrubber"
        type="range"
        min={0}
        max={frameCount - 1}
        step={0.01}
        value={cursor}
        onChange={(e) => seek(Number(e.target.value))}
        aria-label="Replay position"
      />
      <span className="clock">
        {clock(cursor / frameRate)} / {clock((frameCount - 1) / frameRate)}
      </span>
      <select
        className="speed"
        value={speed}
        onChange={(e) => setSpeed(Number(e.target.value))}
        aria-label="Playback speed"
      >
        <option value={0.25}>0.25×</option>
        <option value={0.5}>0.5×</option>
        <option value={1}>1×</option>
        <option value={2}>2×</option>
      </select>
    </div>
  );
}
