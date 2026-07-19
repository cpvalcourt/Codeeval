/**
 * Binds the pure PlaybackEngine to requestAnimationFrame and React state.
 * The engine owns all playback semantics; this hook only owns the clock.
 */

import { useCallback, useEffect, useRef, useState } from "react";

import { PlaybackEngine } from "../lib/playback";

export interface PlaybackControls {
  cursor: number;
  playing: boolean;
  speed: number;
  toggle(): void;
  seek(cursor: number): void;
  setSpeed(speed: number): void;
}

export function usePlayback(frameCount: number, frameRate: number): PlaybackControls {
  const engineRef = useRef<PlaybackEngine | null>(null);
  if (engineRef.current === null) {
    engineRef.current = new PlaybackEngine(frameCount, frameRate);
  }
  const engine = engineRef.current;

  const [cursor, setCursor] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeedState] = useState(1);

  // New clip: clamp cursor and rewind.
  useEffect(() => {
    engine.setFrameCount(frameCount);
    engine.seek(0);
    setCursor(0);
  }, [engine, frameCount]);

  useEffect(() => {
    let raf = 0;
    let last = performance.now();
    const loop = (now: number) => {
      const dt = Math.min((now - last) / 1000, 0.1); // clamp tab-switch jumps
      last = now;
      setCursor(engine.tick(dt));
      setPlaying(engine.playing);
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [engine]);

  const toggle = useCallback(() => {
    engine.toggle();
    setPlaying(engine.playing);
  }, [engine]);

  const seek = useCallback(
    (c: number) => {
      engine.seek(c);
      setCursor(engine.cursor);
    },
    [engine]
  );

  const setSpeed = useCallback(
    (s: number) => {
      engine.setSpeed(s);
      setSpeedState(s);
    },
    [engine]
  );

  return { cursor, playing, speed, toggle, seek, setSpeed };
}
