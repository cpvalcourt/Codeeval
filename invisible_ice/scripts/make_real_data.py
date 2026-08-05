"""Build the site's data from real Big Data Cup files (guide Steps 8-9).

Discovers games in a raw-data directory, loads them through the BDC
adapter, trains the EPV pipeline on the whole corpus, analyzes each game,
and writes one JSON payload per game plus an index manifest into the
frontend's public data directory. Diagnostics run at each stage so a bad
run reports why rather than silently producing an empty site.

    python3 scripts/make_real_data.py rawdata
    python3 scripts/make_real_data.py rawdata --games 3 --team home
    python3 scripts/make_real_data.py rawdata --min-coverage 0.5

Exit status is non-zero if any diagnostic check fails, so this is safe to
run in CI before a deploy.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402

from invisible_ice.data.bdc import (  # noqa: E402
    BigDataCupError,
    BigDataCupLoader,
    discover_games,
)
from invisible_ice.diagnostics import (  # noqa: E402
    corpus_report,
    epv_report,
    label_report,
)
from invisible_ice.domain import Team  # noqa: E402
from invisible_ice.export import (  # noqa: E402
    game_payload,
    manifest_entry,
    write_game_json,
    write_manifest,
)
from invisible_ice.pipeline import EPVPipeline  # noqa: E402

DEFAULT_OUT = Path(__file__).resolve().parents[1] / "frontend" / "public" / "data"
ORIENTATIONS = "camera_orientations.csv"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rawdata", type=Path, help="directory of BDC CSVs")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--team", choices=[t.value for t in Team], default=Team.HOME.value)
    parser.add_argument("--games", type=int, default=None, help="limit games loaded")
    parser.add_argument(
        "--min-coverage",
        type=float,
        default=0.7,
        help="drop entities tracked for less than this fraction of a segment",
    )
    parser.add_argument(
        "--min-segment-frames", type=int, default=60, help="drop shorter play runs"
    )
    return parser.parse_args(argv)


def load_corpus(
    rawdata: Path, loader: BigDataCupLoader, team: Team, limit: int | None
) -> dict[str, list[tuple[pd.DataFrame, pd.DataFrame]]]:
    """Load every discovered game into its list of play segments."""
    orientations = rawdata / ORIENTATIONS
    if not orientations.exists():
        raise SystemExit(f"missing {orientations}")

    discovered = discover_games(rawdata)
    if not discovered:
        raise SystemExit(f"no BDC game files found under {rawdata}")

    by_game: dict[str, list] = {}
    for game_id in sorted(discovered)[: limit or None]:
        spec = discovered[game_id]
        try:
            segments = loader.load_game(
                spec["tracking"],
                spec["events"],
                orientations,
                game_id=game_id,
                game_key=spec["game_key"],
                team=team,
            )
        except (BigDataCupError, ValueError) as exc:
            # One unusable game must not abort a whole-corpus run.
            print(f"  {game_id}: SKIPPED ({exc})")
            continue
        print(f"  {game_id}: {len(segments)} segments")
        if segments:
            by_game[game_id] = segments
    return by_game


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    team = Team(args.team)
    loader = BigDataCupLoader(
        min_entity_coverage=args.min_coverage,
        min_segment_frames=args.min_segment_frames,
    )

    print(f"Loading games from {args.rawdata} ...")
    by_game = load_corpus(args.rawdata, loader, team, args.games)
    corpus = [segment for segments in by_game.values() for segment in segments]

    print("\n== corpus ==")
    report = corpus_report(corpus, team)
    print(report)
    if not report.ok:
        print("\nCorpus checks failed; see docs/REAL_DATA_GUIDE.md Step 8.")
        return 1

    print("\nTraining ...")
    pipeline = EPVPipeline().fit(corpus, team=team)

    print("\n== labels ==")
    labels = label_report(pipeline, corpus[: min(len(corpus), 40)], team)
    print(labels)

    print("\n== export ==")
    entries = []
    all_analyses = []
    for game_id, segments in by_game.items():
        analyses = []
        # Each segment analyzes independently; merge for one payload per game.
        merged_tracking = pd.concat([t for t, _ in segments], ignore_index=True)
        for tracking, _ in segments:
            analyses.extend(pipeline.analyze_game(tracking, team=team))
        if not analyses:
            print(f"  {game_id}: no possessions, skipped")
            continue
        all_analyses.extend(analyses)
        file_name = f"{game_id}.json"
        payload = game_payload(game_id, merged_tracking, analyses)
        write_game_json(payload, args.out / file_name)
        entries.append(manifest_entry(payload, file_name))
        print(f"  {game_id}: {len(analyses)} possessions -> {file_name}")

    if not entries:
        print("\nNo game produced possessions; nothing written.")
        return 1

    write_manifest(entries, args.out / "index.json")
    print(f"\nWrote {len(entries)} game(s) + index.json to {args.out}")

    print("\n== epv ==")
    epv = epv_report(all_analyses)
    print(epv)

    ok = report.ok and labels.ok and epv.ok
    print("\nAll checks passed." if ok else "\nSome checks FAILED (see above).")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
