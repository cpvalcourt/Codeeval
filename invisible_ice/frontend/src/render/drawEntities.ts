/**
 * Draws skaters, goalies, and the puck at one playback instant, with
 * fading velocity trails. Identity is never color-alone: goalies get a
 * square mark, the puck is a small ink dot, and every mark carries a
 * 2px surface ring so overlapping dots stay separable.
 */

import { RinkTransform } from "../lib/rinkTransform";
import { ThemePalette } from "../lib/theme";
import { EntitySample } from "../lib/types";

export const SKATER_RADIUS_PX = 7;
export const PUCK_RADIUS_PX = 3.5;

export interface Trail {
  entityIndex: number;
  points: Array<{ x: number; y: number }>;
}

function teamColor(sample: EntitySample, palette: ThemePalette): string {
  if (sample.team === "home") return palette.home;
  if (sample.team === "away") return palette.away;
  return palette.inkPrimary; // puck
}

export function drawTrails(
  ctx: CanvasRenderingContext2D,
  tr: RinkTransform,
  samples: EntitySample[],
  trails: Trail[],
  palette: ThemePalette
): void {
  for (const trail of trails) {
    const sample = samples[trail.entityIndex];
    if (!sample || trail.points.length < 2) continue;
    const color = teamColor(sample, palette);
    // Fade by segment age: oldest segments faintest.
    for (let i = 1; i < trail.points.length; i++) {
      const alpha = 0.35 * (i / (trail.points.length - 1));
      const [x0, y0] = tr.toPx(trail.points[i - 1].x, trail.points[i - 1].y);
      const [x1, y1] = tr.toPx(trail.points[i].x, trail.points[i].y);
      ctx.beginPath();
      ctx.moveTo(x0, y0);
      ctx.lineTo(x1, y1);
      ctx.strokeStyle = color;
      ctx.globalAlpha = alpha;
      ctx.lineWidth = 2;
      ctx.stroke();
    }
    ctx.globalAlpha = 1;
  }
}

export function drawEntities(
  ctx: CanvasRenderingContext2D,
  tr: RinkTransform,
  samples: EntitySample[],
  palette: ThemePalette
): void {
  // Puck last so it stays visible on top of bodies.
  const ordered = [...samples].sort((a, b) =>
    a.position === "puck" ? 1 : b.position === "puck" ? -1 : 0
  );
  for (const sample of ordered) {
    const [px, py] = tr.toPx(sample.x, sample.y);
    const color = teamColor(sample, palette);
    ctx.beginPath();
    if (sample.position === "goalie") {
      const s = SKATER_RADIUS_PX;
      ctx.rect(px - s, py - s, 2 * s, 2 * s);
    } else {
      const r = sample.position === "puck" ? PUCK_RADIUS_PX : SKATER_RADIUS_PX;
      ctx.arc(px, py, r, 0, Math.PI * 2);
    }
    ctx.fillStyle = color;
    ctx.fill();
    ctx.strokeStyle = palette.surface;
    ctx.lineWidth = 2;
    ctx.stroke();

    if (sample.position === "skater") {
      // Jersey number from the entity id ("home_3" -> 3), ink-on-mark.
      const num = sample.id.split("_").pop() ?? "";
      ctx.fillStyle = palette.surface;
      ctx.font = `bold ${SKATER_RADIUS_PX + 2}px system-ui, sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(num, px, py + 0.5);
    }
  }
}
