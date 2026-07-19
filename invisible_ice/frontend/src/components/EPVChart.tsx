/**
 * The synchronized EPV timeline: a single-series line + area chart
 * (d3-scale/d3-shape, rendered as React SVG) with a moving playhead,
 * crosshair + tooltip on hover, and click-to-seek.
 */

import { scaleLinear } from "d3-scale";
import { area, line } from "d3-shape";
import { useMemo, useRef, useState } from "react";

import { PossessionData } from "../lib/types";

const WIDTH = 720;
const HEIGHT = 180;
const MARGIN = { top: 12, right: 16, bottom: 26, left: 44 };

interface Props {
  possession: PossessionData;
  frameRate: number;
  cursor: number;
  onSeek(cursor: number): void;
}

export function EPVChart({ possession, frameRate, cursor, onSeek }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [hover, setHover] = useState<number | null>(null);

  const epv = possession.series.epv;
  const duration = (epv.length - 1) / frameRate;

  const { xScale, yScale, linePath, areaPath } = useMemo(() => {
    const xScale = scaleLinear()
      .domain([0, duration])
      .range([MARGIN.left, WIDTH - MARGIN.right]);
    const yMax = Math.max(0.1, Math.max(...epv) * 1.15);
    const yScale = scaleLinear()
      .domain([0, yMax])
      .range([HEIGHT - MARGIN.bottom, MARGIN.top]);
    const toXY = (v: number, i: number): [number, number] => [
      xScale(i / frameRate),
      yScale(v),
    ];
    const linePath = line<number>()
      .x((v, i) => toXY(v, i)[0])
      .y((v, i) => toXY(v, i)[1])(epv);
    const areaPath = area<number>()
      .x((v, i) => toXY(v, i)[0])
      .y0(yScale(0))
      .y1((v, i) => toXY(v, i)[1])(epv);
    return { xScale, yScale, linePath, areaPath };
  }, [epv, duration, frameRate]);

  const cursorToSeconds = (c: number) => c / frameRate;

  function eventSeconds(evt: React.MouseEvent<SVGSVGElement>): number | null {
    const svg = svgRef.current;
    if (!svg) return null;
    const rect = svg.getBoundingClientRect();
    const px = ((evt.clientX - rect.left) / rect.width) * WIDTH;
    const t = xScale.invert(px);
    return Math.min(Math.max(t, 0), duration);
  }

  const hoverIndex = hover === null ? null : Math.round(hover * frameRate);
  const hovered =
    hoverIndex === null
      ? null
      : {
          t: hover as number,
          epv: epv[hoverIndex],
          xg: possession.series.xg[hoverIndex],
          pShoot: possession.series.p_shoot[hoverIndex],
        };

  return (
    <div className="epv-chart-wrap">
      <svg
        ref={svgRef}
        className="epv-chart"
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        onMouseMove={(e) => setHover(eventSeconds(e))}
        onMouseLeave={() => setHover(null)}
        onClick={(e) => {
          const t = eventSeconds(e);
          if (t !== null) onSeek(t * frameRate);
        }}
        role="application"
        aria-label="Expected possession value over time; click to jump the replay"
      >
        {yScale.ticks(4).map((tick) => (
          <g key={`y${tick}`}>
            <line
              className="grid-line"
              x1={MARGIN.left}
              x2={WIDTH - MARGIN.right}
              y1={yScale(tick)}
              y2={yScale(tick)}
            />
            <text className="tick-label" x={MARGIN.left - 6} y={yScale(tick)} dy="0.32em" textAnchor="end">
              {tick.toFixed(2)}
            </text>
          </g>
        ))}
        {xScale.ticks(6).map((tick) => (
          <text
            key={`x${tick}`}
            className="tick-label"
            x={xScale(tick)}
            y={HEIGHT - MARGIN.bottom + 16}
            textAnchor="middle"
          >
            {tick}s
          </text>
        ))}
        <line
          className="axis-line"
          x1={MARGIN.left}
          x2={WIDTH - MARGIN.right}
          y1={yScale(0)}
          y2={yScale(0)}
        />
        {areaPath && <path className="epv-area" d={areaPath} />}
        {linePath && <path className="epv-line" d={linePath} />}

        <line
          className="playhead"
          x1={xScale(cursorToSeconds(cursor))}
          x2={xScale(cursorToSeconds(cursor))}
          y1={MARGIN.top}
          y2={HEIGHT - MARGIN.bottom}
        />

        {hovered && (
          <g>
            <line
              className="crosshair"
              x1={xScale(hovered.t)}
              x2={xScale(hovered.t)}
              y1={MARGIN.top}
              y2={HEIGHT - MARGIN.bottom}
            />
            <circle
              className="hover-dot"
              cx={xScale(hovered.t)}
              cy={yScale(hovered.epv)}
              r={4}
            />
          </g>
        )}
      </svg>
      {hovered && (
        <div className="chart-tooltip" role="status">
          <span className="tooltip-time">{hovered.t.toFixed(2)}s</span>
          <span>EPV {hovered.epv.toFixed(3)}</span>
          <span>xG {hovered.xg.toFixed(3)}</span>
          <span>P(shoot) {hovered.pShoot.toFixed(3)}</span>
        </div>
      )}
    </div>
  );
}
