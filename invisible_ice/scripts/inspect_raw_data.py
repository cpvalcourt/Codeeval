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


def analyze_tracking(paths: list[Path]) -> None:
    banner(f"TRACKING — {len(paths)} file(s); analyzing {paths[0].name}")
    df = pd.read_csv(paths[0])
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

    if frame_col:
        frames = df[frame_col].dropna().unique()
        frames.sort()
        gaps = pd.Series(frames).diff().dropna()
        print("\n-- frame index --")
        print(f"   {len(frames):,} distinct values, from {frames[0]} to {frames[-1]}")
        print(f"   step sizes: {gaps.value_counts().head(5).to_dict()}")
        print(f"   contiguous: {bool((gaps == gaps.mode()[0]).all())}")

        if clock_col:
            clock = pd.to_numeric(df[clock_col], errors="coerce")
            if clock.isna().all():  # mm:ss text
                parsed = df[clock_col].astype(str).str.extract(r"(\d+):(\d+)")
                clock = parsed[0].astype(float) * 60 + parsed[1].astype(float)
            paired = pd.DataFrame({"f": df[frame_col], "c": clock}).dropna().drop_duplicates("f")
            if len(paired) > 10:
                span_frames = paired["f"].max() - paired["f"].min()
                span_seconds = abs(paired["c"].max() - paired["c"].min())
                if span_seconds > 0:
                    print(f"\n-- frame rate --")
                    print(f"   ~{span_frames / span_seconds:.2f} frames/second "
                          f"({span_frames:,.0f} frames over {span_seconds:,.0f}s)")
                counts_down = paired.sort_values("f")["c"].diff().mean() < 0
                print(f"   clock counts {'DOWN' if counts_down else 'UP'}")

    if kind_col:
        print("\n-- puck vs players --")
        print(f"   {kind_col!r} values: {df[kind_col].value_counts().to_dict()}")

    if frame_col:
        per_frame = df.groupby(frame_col).size()
        print("\n-- entities per frame (roster stability) --")
        print(f"   {per_frame.value_counts().head(6).to_dict()}")
        print(f"   min {per_frame.min()}, median {per_frame.median():.0f}, max {per_frame.max()}")
        if kind_col:
            puck_mask = df[kind_col].astype(str).str.contains("puck", case=False, na=False)
            frames_with_puck = df.loc[puck_mask, frame_col].nunique()
            total = df[frame_col].nunique()
            pct = 100 * frames_with_puck / total if total else 0
            print(f"   frames containing a puck row: {frames_with_puck:,}/{total:,} ({pct:.1f}%)")
            if pct < 100:
                print("   !! puck gaps present -> interpolation needed (guide Step 4.2)")

    if player_col:
        print("\n-- player ids --")
        ids = df[player_col].dropna().unique()
        print(f"   {len(ids):,} distinct; sample {list(map(str, ids[:8]))}")
        if team_col:
            by_team = df.groupby(team_col)[player_col].nunique()
            print(f"   distinct players per team: {by_team.to_dict()}")
            print("   (a team with ~10-12 skaters over a period is normal; "
                  "goalies must be identified separately — check the roster or crease position)")


def analyze_events(paths: list[Path]) -> None:
    banner(f"EVENTS — {len(paths)} file(s); analyzing {paths[0].name}")
    df = pd.read_csv(paths[0])
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
