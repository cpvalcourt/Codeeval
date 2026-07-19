"""Generate a demo payload for the frontend from the synthetic corpus.

Trains the EPV pipeline on synthetic games, analyzes one of them, and
writes the serialized payload to frontend/public/data/demo.json. Run from
the invisible_ice directory:

    python3 scripts/make_demo_data.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from invisible_ice.data.synthetic import SyntheticGameGenerator
from invisible_ice.domain import Team
from invisible_ice.export import game_payload, write_game_json
from invisible_ice.pipeline import EPVPipeline

N_GAMES = 10
DEMO_GAME_INDEX = 0
OUT = Path(__file__).resolve().parents[1] / "frontend" / "public" / "data" / "demo.json"


def main() -> None:
    games = [
        SyntheticGameGenerator(seed=seed).generate_game(f"game_{seed}")
        for seed in range(N_GAMES)
    ]
    pipeline = EPVPipeline().fit(games, team=Team.HOME)

    tracking, _ = games[DEMO_GAME_INDEX]
    analyses = pipeline.analyze_game(tracking, team=Team.HOME)
    payload = game_payload(f"game_{DEMO_GAME_INDEX}", tracking, analyses)
    path = write_game_json(payload, OUT)
    size_kb = path.stat().st_size / 1024
    print(f"wrote {len(analyses)} possessions to {path} ({size_kb:.0f} KiB)")


if __name__ == "__main__":
    main()
