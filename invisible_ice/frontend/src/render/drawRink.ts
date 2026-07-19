/**
 * Canvas rink renderer: boards, zone lines, center circle, faceoff dots,
 * creases, and the Royal Road. Pure function of (ctx, transform, dims,
 * palette) so it can be exercised against a recording stub context.
 */

import { RinkTransform } from "../lib/rinkTransform";
import { ThemePalette } from "../lib/theme";
import { RinkDims } from "../lib/types";

const CORNER_RADIUS_FT = 28;

export function drawRink(
  ctx: CanvasRenderingContext2D,
  tr: RinkTransform,
  rink: RinkDims,
  palette: ThemePalette
): void {
  const [left, top] = tr.toPx(rink.xMin, rink.yMax);
  const [right, bottom] = tr.toPx(rink.xMax, rink.yMin);
  const r = CORNER_RADIUS_FT * tr.scale;

  ctx.clearRect(0, 0, tr.width, tr.height);

  // Ice sheet with rounded corners.
  ctx.beginPath();
  ctx.roundRect(left, top, right - left, bottom - top, r);
  ctx.fillStyle = palette.surface;
  ctx.fill();
  ctx.strokeStyle = palette.baseline;
  ctx.lineWidth = 1.5;
  ctx.stroke();

  const vline = (x: number, color: string, width: number) => {
    const [px, y0] = tr.toPx(x, rink.yMax);
    const [, y1] = tr.toPx(x, rink.yMin);
    ctx.beginPath();
    ctx.moveTo(px, y0);
    ctx.lineTo(px, y1);
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.stroke();
  };

  vline(0, palette.rinkLineRed, 2);
  vline(rink.blueLineX, palette.rinkLineBlue, 2);
  vline(-rink.blueLineX, palette.rinkLineBlue, 2);
  vline(rink.goalLineX, palette.rinkLineRed, 1);
  vline(-rink.goalLineX, palette.rinkLineRed, 1);

  // Center circle + dot.
  const [cx, cy] = tr.toPx(0, 0);
  ctx.beginPath();
  ctx.arc(cx, cy, 15 * tr.scale, 0, Math.PI * 2);
  ctx.strokeStyle = palette.rinkLineBlue;
  ctx.lineWidth = 1;
  ctx.stroke();
  ctx.beginPath();
  ctx.arc(cx, cy, 2, 0, Math.PI * 2);
  ctx.fillStyle = palette.rinkLineBlue;
  ctx.fill();

  // Faceoff dots in each zone.
  for (const sx of [-1, 1]) {
    for (const sy of [-1, 1]) {
      const [fx, fy] = tr.toPx(sx * 69, sy * 22);
      ctx.beginPath();
      ctx.arc(fx, fy, 2.5, 0, Math.PI * 2);
      ctx.fillStyle = palette.rinkLineRed;
      ctx.fill();
    }
  }

  // Goal creases.
  for (const sx of [-1, 1]) {
    const [gx, gy] = tr.toPx(sx * rink.goalLineX, 0);
    ctx.beginPath();
    ctx.arc(gx, gy, 6 * tr.scale, Math.PI / 2, (3 * Math.PI) / 2, sx > 0);
    ctx.fillStyle = palette.creaseFill;
    ctx.fill();
    ctx.strokeStyle = palette.rinkLineRed;
    ctx.lineWidth = 1;
    ctx.stroke();
  }

  // Royal Road: dashed midline of the offensive zone.
  const [rx0, ry] = tr.toPx(rink.blueLineX, 0);
  const [rx1] = tr.toPx(rink.goalLineX, 0);
  ctx.beginPath();
  ctx.setLineDash([6, 6]);
  ctx.moveTo(rx0, ry);
  ctx.lineTo(rx1, ry);
  ctx.strokeStyle = palette.gridline;
  ctx.lineWidth = 1;
  ctx.stroke();
  ctx.setLineDash([]);
}
