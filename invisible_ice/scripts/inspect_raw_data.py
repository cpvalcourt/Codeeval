"""Reconnaissance for real tracking data (Step 2 of docs/REAL_DATA_GUIDE.md).

Answers the "pin down the conventions" checklist automatically: which
files exist, what columns they carry, the coordinate extents and origin,
the frame rate, how the puck and goalies are marked, roster stability
per frame, and the event vocabulary. Read-only — it never modifies the
raw data.

Usage:

    python3 scripts/inspect_raw_data.py /path/to/rawdata
    python3 scripts/inspect_raw_data.py /path/to/rawdata --game 2026-01-17

Copy the printed findings into a comment block at the top of your
loader (src/invisible_ice/data/bdc.py); they become its constants.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd

MAX_UNIQUE_TO_LIST = 12
RULE = "=" * 72


def banner(title: str) -> None:
    print(f"\n{RULE}\n{title}\n{RULE}")


def find_files(root: Path) -> dict[str, list[Path]]:
    """Bucket the raw CSVs by kind using their filenames."""
    buckets: dict[str, list[Path]] = {
        "tracking": [],
        "events": [],
        "shifts": [],
        "orientations": [],
        "other": [],
    }
    for path in sorted(root.rglob("*.csv")):
        name = path.name.lower()
        if "tracking" in name:
            buckets["tracking"].append(path)
        elif "event" in name:
            buckets["events"].append(path)
        elif "shift" in name:
            buckets["shifts"].append(path)
        elif "orientation" in name or "camera" in name:
            buckets["orientations"].append(path)
        else:
            buckets["other"].append(path)
    return buckets


def describe_columns(df: pd.DataFrame, label: str) -> None:
    print(f"\n-- {label}: {len(df):,} rows x {len(df.columns)} columns --")
    for col in df.columns:
        series = df[col]
        nulls = int(series.isna().sum())
        detail = ""
        if pd.api.types.is_numeric_dtype(series):
            detail = f"range [{series.min():.4g}, {series.max():.4g}]"
        else:
            uniques = series.dropna().unique()
            if len(uniques) <= MAX_UNIQUE_TO_LIST:
                detail = f"values {sorted(map(str, uniques))}"
            else:
                detail = f"{len(uniques):,} distinct, e.g. {list(map(str, uniques[:4]))}"
        null_note = f", {nulls:,} null" if nulls else ""
        print(f"   {col!r:<28} {str(series.dtype):<10} {detail}{null_note}")


def pick(df: pd.DataFrame, *patterns: str) -> str | None:
    """First column whose name matches any regex (case-insensitive)."""
    for pattern in patterns:
        for col in df.columns:
            if re.search(pattern, col, re.IGNORECASE):
                return col
    return None


def numeric_frame_index(series: pd.Series) -> tuple[pd.Series, str]:
    """Coerce a frame column to sortable integers.

    Real feeds label frames with strings like
    ``"2025-10-11 Team A @ Team D_065468"``; the trailing digits are the
    sequence number. Returns (values, note describing what was done).
    """
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().any():
        return numeric, "already numeric"
    digits = series.astype(str).str.extract(r"(\d+)\s*$")[0]
    return (
        pd.to_numeric(digits, errors="coerce"),
        "string ids -> parsed trailing digits (your loader must do the same)",
    )


def analyze_tracking(paths: list[Path]) -> None:
    banner(f"TRACKING — {len(paths)} file(s); analyzing {paths[0].name}")
    df = pd.read_csv(paths[0], low_memory=False)
    describe_columns(df, "columns")

    frame_col = pick(df, r"image.?id", r"frame")
    clock_col = pick(df, r"game.?clock", r"clock", r"time")
    x_col = pick(df, r"(rink.?location.?)?x$", r"x.?coord", r"\bx\b")
    y_col = pick(df, r"(rink.?location.?)?y$", r"y.?coord", r"\by\b")
    kind_col = pick(df, r"player.?or.?puck", r"entity", r"type")
    team_col = pick(df, r"team")
    player_col = pick(df, r"player.?id", r"player")

    print("\n-- inferred column roles --")
    for role, col in [
        ("frame index", frame_col),
        ("clock", clock_col),
        ("x", x_col),
        ("y", y_col),
        ("player/puck kind", kind_col),
        ("team", team_col),
        ("player id", player_col),
    ]:
        print(f"   {role:<18} -> {col!r}")

    if x_col and y_col:
        print("\n-- coordinate system --")
        print(f"   x: [{df[x_col].min():.2f}, {df[x_col].max():.2f}]")
        print(f"   y: [{df[y_col].min():.2f}, {df[y_col].max():.2f}]")
        canonical = df[x_col].min() < -50 and df[y_col].min() < -20
        corner = df[x_col].min() >= -1 and df[x_col].max() > 150
        if canonical:
            print("   => looks CENTER-ORIGIN (canonical): pass coordinates through")
        elif corner:
            print("   => looks CORNER-ORIGIN 0..200 x 0..85: use CoordinateNormalizer(BIG_DATA_CUP)")
        else:
            print("   => unrecognized extent: build SourceCoordinateSystem with these bounds")
        missing = int(df[x_col].isna().sum() + df[y_col].isna().sum())
        if missing:
            pct = 100 * missing / (2 * len(df))
            print(f"   !! {missing:,} missing coordinate values ({pct:.2f}% of cells)")
            print("      -> drop or interpolate these rows before validation (guide Step 4.4)")

    frames = None
    if frame_col:
        frames_raw, note = numeric_frame_index(df[frame_col])
        print(f"\n-- frame index ({frame_col!r}: {note}) --")
        frames = frames_raw
        values = np.sort(np.asarray(frames.dropna().unique(), dtype=float))
        gaps = pd.Series(values).diff().dropna()
        if len(values):
            print(f"   {len(values):,} distinct, from {values[0]:.0f} to {values[-1]:.0f}")
            print(f"   step sizes: {gaps.value_counts().head(5).to_dict()}")
            print(f"   contiguous: {bool(len(gaps) and (gaps == 1).all())}")
            span = values[-1] - values[0] + 1
            if span > len(values):
                big = gaps[gaps > 1]
                print(f"   !! {span - len(values):,.0f} frame numbers absent inside the range, "
                      f"in {len(big):,} gap(s) (largest {big.max():,.0f})")
                print("      Ids run on broadcast time; tracking rows exist only during live")
                print("      play, so these gaps are STOPPAGES. Split the game into contiguous")
                print("      segments at them and process each separately (guide Step 4.1).")

        if clock_col:
            clock = pd.to_numeric(df[clock_col], errors="coerce")
            if clock.isna().all():  # mm:ss text
                parsed = df[clock_col].astype(str).str.extract(r"(\d+):(\d+)")
                clock = parsed[0].astype(float) * 60 + parsed[1].astype(float)
            paired = (
                pd.DataFrame({"f": frames, "c": clock}).dropna().drop_duplicates("f")
            )
            if len(paired) > 10:
                span_frames = paired["f"].max() - paired["f"].min()
                span_seconds = abs(paired["c"].max() - paired["c"].min())
                if span_seconds > 0:
                    n_frames = len(values)
                    print("\n-- frame rate --")
                    print(f"   captured: ~{n_frames / span_seconds:.2f} fps "
                          f"({n_frames:,} distinct frames over {span_seconds:,.0f}s of clock)")
                    print(f"   id counter: ~{span_frames / span_seconds:.2f} ids/s "
                          f"(spans {span_frames:,.0f} ids)")
                    print("   The CAPTURED rate is the real one; if the id rate is higher,")
                    print("   the counter keeps running through stoppages (see gaps above).")
                clock_step = pd.Series(np.sort(paired["c"].unique())).diff().dropna()
                if len(clock_step) and clock_step.mode()[0] >= 1.0:
                    print(f"   !! clock resolution is {clock_step.mode()[0]:.0f}s — one clock value")
                    print("      covers ~30 frames, so events cannot be aligned to a frame by")
                    print("      clock alone; disambiguate with the event's X/Y (guide Step 6).")
                counts_down = paired.sort_values("f")["c"].diff().mean() < 0
                print(f"   clock counts {'DOWN' if counts_down else 'UP'}"
                      " (derive timestamps from the frame index, not the clock)")

    if kind_col:
        print("\n-- puck vs players --")
        print(f"   {kind_col!r} values: {df[kind_col].value_counts().to_dict()}")

    if frames is not None:
        per_frame = df.groupby(frames).size()
        print("\n-- entities per frame (roster stability) --")
        print(f"   {per_frame.value_counts().head(6).to_dict()}")
        print(f"   min {per_frame.min()}, median {per_frame.median():.0f}, max {per_frame.max()}")
        if per_frame.min() < per_frame.median():
            print("   !! frames with partial rosters -> per-possession reindexing"
                  " needed (guide Step 4.3)")
        if kind_col:
            puck_mask = df[kind_col].astype(str).str.contains("puck", case=False, na=False)
            frames_with_puck = frames[puck_mask].nunique()
            total = int(frames.nunique())
            pct = 100 * frames_with_puck / total if total else 0
            print(f"   frames containing a puck row: {frames_with_puck:,}/{total:,} ({pct:.1f}%)")
            if pct < 100:
                print("   !! puck gaps present -> interpolation needed (guide Step 4.2)")

    # Which column actually identifies a *player*? A feed may carry a
    # per-detection track id (high cardinality) alongside a real identity
    # like the jersey number (low cardinality). Picking wrong makes every
    # entity_id unstable across frames.
    jersey_col = pick(df, r"jersey")
    identity_col = player_col
    if player_col:
        print("\n-- identity columns --")
        n_player = int(df[player_col].nunique())
        print(f"   {player_col!r}: {n_player:,} distinct")
        if jersey_col:
            n_jersey = int(df[jersey_col].nunique())
            print(f"   {jersey_col!r}: {n_jersey:,} distinct")
            if n_player > 3 * max(n_jersey, 1):
                identity_col = jersey_col
                print(f"   !! {player_col!r} looks like a per-detection TRACK id, not a player.")
                print(f"      Build entity_id from team + {jersey_col!r} instead, and expect")
                print("      the same skater to change track id mid-game.")
        if team_col:
            print(f"   distinct {identity_col!r} per team: "
                  f"{df.groupby(team_col)[identity_col].nunique().to_dict()}")
        unnamed = int(df[identity_col].isna().sum() - df[df[kind_col].astype(str)
                      .str.contains('puck', case=False, na=False)].shape[0]) if kind_col else 0
        if unnamed > 0:
            print(f"   !! ~{unnamed:,} player rows have no {identity_col!r} — unidentified")
            print("      detections; drop them (they cannot be given a stable entity_id).")

    # Goalies are rarely flagged in the feed; infer them from where they live.
    if identity_col and x_col and team_col:
        print("\n-- likely goalies (mean |x| nearest the goal line) --")
        players = df[df[identity_col].notna() & df[x_col].notna()]
        stats = players.groupby([team_col, identity_col]).agg(
            mean_x=(x_col, "mean"), rows=(x_col, "size")
        )
        stats = stats[stats["rows"] >= 200]  # ignore cameo detections
        for team, group in stats.groupby(level=0):
            ranked = group.reindex(group["mean_x"].abs().sort_values(ascending=False).index)
            print(f"   {team}:")
            for (_, pid), row in ranked.head(3).iterrows():
                print(f"      {str(pid):>8}  mean x {row['mean_x']:+7.1f}  ({row['rows']:,} rows)")
        print("   A goalie sits near ±89 while skaters average near 0; the gap between")
        print("   the 1st and 2nd row per team should be obvious. Confirm via Shifts,")
        print("   then set position='goalie' for those ids.")


def analyze_events(paths: list[Path]) -> None:
    banner(f"EVENTS — {len(paths)} file(s); analyzing {paths[0].name}")
    df = pd.read_csv(paths[0], low_memory=False)
    describe_columns(df, "columns")

    event_col = pick(df, r"^event$", r"event.?type", r"event")
    if event_col:
        print(f"\n-- event vocabulary ({event_col!r}) --")
        for name, count in df[event_col].value_counts().items():
            print(f"   {str(name):<24} {count:,}")
        print("\n   Map these per guide Step 6: Shot->shot, Goal->goal(+shot),")
        print("   Play->pass, Incomplete Play->turnover, Takeaway->turnover (flip team).")

    x_col = pick(df, r"x.?coord", r"\bx\b")
    y_col = pick(df, r"y.?coord", r"\by\b")
    if x_col and y_col:
        print(f"\n-- event coordinates --")
        print(f"   x: [{df[x_col].min():.2f}, {df[x_col].max():.2f}]  "
              f"y: [{df[y_col].min():.2f}, {df[y_col].max():.2f}]")


def analyze_orientations(paths: list[Path]) -> None:
    banner(f"CAMERA ORIENTATIONS — {paths[0].name}")
    df = pd.read_csv(paths[0])
    describe_columns(df, "columns")
    print("\n   Use this to build the DirectionNormalizer period map (guide Step 5):")
    print("   {period: True if the analyzed team already attacks +x}")
    with pd.option_context("display.max_rows", 20, "display.width", 200):
        print(df.head(20).to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="directory containing the raw CSVs")
    parser.add_argument("--game", help="only inspect files whose name contains this string")
    args = parser.parse_args()

    if not args.root.is_dir():
        raise SystemExit(f"not a directory: {args.root}")

    buckets = find_files(args.root)
    if args.game:
        buckets = {
            kind: [p for p in paths if args.game in p.name or kind == "orientations"]
            for kind, paths in buckets.items()
        }

    banner(f"FILE INVENTORY — {args.root}")
    for kind, paths in buckets.items():
        print(f"   {kind:<14} {len(paths):>4} file(s)")
        for path in paths[:4]:
            print(f"        {path.relative_to(args.root)}  "
                  f"({path.stat().st_size / 1e6:.1f} MB)")
        if len(paths) > 4:
            print(f"        ... and {len(paths) - 4} more")

    if buckets["tracking"]:
        analyze_tracking(buckets["tracking"])
    else:
        print("\n!! no tracking files found (expected '...Tracking_P1.csv')")
    if buckets["events"]:
        analyze_events(buckets["events"])
    if buckets["orientations"]:
        analyze_orientations(buckets["orientations"])

    banner("NEXT")
    print("   Paste this output into a comment block atop")
    print("   src/invisible_ice/data/bdc.py, then continue at guide Step 3.")


if __name__ == "__main__":
    main()
