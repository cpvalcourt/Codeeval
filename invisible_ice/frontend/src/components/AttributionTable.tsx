/**
 * Per-player EPV-added table for the selected possession — the table view
 * that backs the visualization, sorted by total contribution.
 */

import { AttributionRow } from "../lib/types";

interface Props {
  rows: AttributionRow[];
}

function fmt(v: number): string {
  const s = v.toFixed(3);
  return v > 0 ? `+${s}` : s;
}

export function AttributionTable({ rows }: Props) {
  if (rows.length === 0) {
    return <p className="empty-note">No attribution recorded for this possession.</p>;
  }
  const sorted = [...rows].sort((a, b) => b.total - a.total);
  return (
    <table className="attribution-table">
      <thead>
        <tr>
          <th scope="col">Player</th>
          <th scope="col">On-puck</th>
          <th scope="col">Off-puck</th>
          <th scope="col">Total EPV added</th>
        </tr>
      </thead>
      <tbody>
        {sorted.map((row) => (
          <tr key={row.playerId}>
            <td>
              <span className="swatch home" aria-hidden="true" />
              {row.playerId}
            </td>
            <td className="num">{fmt(row.onPuck)}</td>
            <td className="num">{fmt(row.offPuck)}</td>
            <td className="num total">{fmt(row.total)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
