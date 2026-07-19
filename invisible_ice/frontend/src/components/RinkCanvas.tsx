/**
 * The 2D rink animation: draws the rink, velocity trails, and entity dots
 * for the current playback cursor on an HTML5 canvas, at devicePixelRatio.
 */

import { useEffect, useRef } from "react";

import { samplePositions, trailPositions } from "../lib/interpolate";
import { makeRinkTransform } from "../lib/rinkTransform";
import { ThemePalette } from "../lib/theme";
import { PossessionData, RinkDims } from "../lib/types";
import { drawEntities, drawTrails, Trail } from "../render/drawEntities";
import { drawRink } from "../render/drawRink";

const TRAIL_FRAMES = 12;

interface Props {
  possession: PossessionData;
  rink: RinkDims;
  cursor: number;
  palette: ThemePalette;
}

export function RinkCanvas({ possession, rink, cursor, palette }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const cssWidth = canvas.clientWidth;
    const cssHeight = (cssWidth * (rink.yMax - rink.yMin)) / (rink.xMax - rink.xMin);
    const dpr = window.devicePixelRatio || 1;
    canvas.width = Math.round(cssWidth * dpr);
    canvas.height = Math.round(cssHeight * dpr);
    canvas.style.height = `${cssHeight}px`;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    const tr = makeRinkTransform(rink, cssWidth, cssHeight);
    const samples = samplePositions(possession, cursor);
    const trails: Trail[] = possession.entities.map((_, e) => ({
      entityIndex: e,
      points: trailPositions(possession, e, cursor, TRAIL_FRAMES),
    }));

    drawRink(ctx, tr, rink, palette);
    drawTrails(ctx, tr, samples, trails, palette);
    drawEntities(ctx, tr, samples, palette);
  }, [possession, rink, cursor, palette]);

  return (
    <canvas
      ref={canvasRef}
      className="rink-canvas"
      role="img"
      aria-label="Animated rink view of the current possession"
    />
  );
}
