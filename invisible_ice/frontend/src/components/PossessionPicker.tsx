/** Possession selector: one chip per possession in the loaded game. */

import { PossessionData } from "../lib/types";

interface Props {
  possessions: PossessionData[];
  selected: number;
  frameRate: number;
  onSelect(index: number): void;
}

export function PossessionPicker({ possessions, selected, frameRate, onSelect }: Props) {
  return (
    <div className="possession-picker" role="tablist" aria-label="Possessions">
      {possessions.map((p, i) => {
        const seconds = (p.frames.length - 1) / frameRate;
        const peak = Math.max(...p.series.epv);
        return (
          <button
            key={p.startFrame}
            role="tab"
            aria-selected={i === selected}
            className={i === selected ? "picker-chip active" : "picker-chip"}
            onClick={() => onSelect(i)}
          >
            <span className="chip-title">Possession {i + 1}</span>
            <span className="chip-meta">
              {seconds.toFixed(1)}s · peak EPV {peak.toFixed(2)}
            </span>
          </button>
        );
      })}
    </div>
  );
}
