/**
 * World (canonical rink feet) -> canvas pixel transform. Preserves aspect
 * ratio, centers the rink in the padded viewport, and flips y (world +y is
 * up; canvas +y is down).
 */

import { RinkDims } from "./types";

export interface RinkTransform {
  toPx(x: number, y: number): [number, number];
  /** Pixels per foot. */
  scale: number;
  width: number;
  height: number;
}

export function makeRinkTransform(
  rink: RinkDims,
  width: number,
  height: number,
  padding = 12
): RinkTransform {
  const worldW = rink.xMax - rink.xMin;
  const worldH = rink.yMax - rink.yMin;
  const scale = Math.min(
    (width - 2 * padding) / worldW,
    (height - 2 * padding) / worldH
  );
  const offsetX = (width - worldW * scale) / 2;
  const offsetY = (height - worldH * scale) / 2;
  return {
    scale,
    width,
    height,
    toPx(x: number, y: number): [number, number] {
      return [offsetX + (x - rink.xMin) * scale, offsetY + (rink.yMax - y) * scale];
    },
  };
}
