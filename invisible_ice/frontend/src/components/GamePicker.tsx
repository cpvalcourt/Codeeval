/** Game selector, shown only when the manifest lists more than one game. */

import { ManifestEntry } from "../lib/types";

interface Props {
  games: ManifestEntry[];
  selected: string;
  onSelect(gameId: string): void;
}

export function GamePicker({ games, selected, onSelect }: Props) {
  if (games.length < 2) return null;
  return (
    <div className="game-picker">
      <label className="game-picker-label" htmlFor="game-select">
        Game
      </label>
      <select
        id="game-select"
        className="game-select"
        value={selected}
        onChange={(e) => onSelect(e.target.value)}
      >
        {games.map((game) => (
          <option key={game.gameId} value={game.gameId}>
            {game.gameId} · {game.possessions} possessions · peak EPV{" "}
            {game.peakEpv.toFixed(2)}
          </option>
        ))}
      </select>
    </div>
  );
}
