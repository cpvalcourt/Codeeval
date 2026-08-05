"""Corpus and model sanity checks (Phase 3 support).

A trained EPV pipeline can be silently wrong: if event alignment drifts,
the transition model never sees a shot and EPV collapses to zero; if the
direction map is inverted, every spatial feature is mirrored. These
checks turn those failure modes into numbers with explicit pass/fail
thresholds, so a real-data run reports its own health instead of
requiring a human to eyeball dataframes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .domain import Action, Position, Team
from .models.labels import make_action_labels
from .pipeline import EPVPipeline, PossessionAnalysis

#: Fraction of frames labeled SHOOT below which the transition model has
#: effectively no scoring signal to learn from.
MIN_SHOOT_LABEL_FRACTION = 0.001
#: Distance (ft) from the attacking net separating "dangerous" frames
#: from neutral-zone frames for the EPV gradient check.
NEAR_NET_FT = 30.0
FAR_FROM_NET_FT = 70.0


@dataclass
class Check:
    name: str
    passed: bool
    detail: str

    def __str__(self) -> str:
        return f"[{'PASS' if self.passed else 'FAIL'}] {self.name}: {self.detail}"


@dataclass
class Report:
    checks: list[Check] = field(default_factory=list)
    stats: dict[str, float] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return all(check.passed for check in self.checks)

    def add(self, name: str, passed: bool, detail: str) -> None:
        self.checks.append(Check(name, passed, detail))

    def __str__(self) -> str:
        lines = [str(check) for check in self.checks]
        if self.stats:
            lines.append("stats: " + ", ".join(
                f"{k}={v:,.4g}" for k, v in self.stats.items()
            ))
        return "\n".join(lines)


def corpus_report(
    games: list[tuple[pd.DataFrame, pd.DataFrame]], team: Team = Team.HOME
) -> Report:
    """Check a loaded corpus before spending time training on it."""
    report = Report()
    if not games:
        report.add("corpus non-empty", False, "no games loaded")
        return report

    frames = sum(t["frame_id"].nunique() for t, _ in games)
    events = pd.concat([e for _, e in games], ignore_index=True) if games else None
    counts = (
        events["event_type"].value_counts().to_dict()
        if events is not None and not events.empty
        else {}
    )
    report.stats.update(
        {
            "segments": len(games),
            "frames": frames,
            "minutes": frames / 30.0 / 60.0,
            **{f"event_{k}": v for k, v in counts.items()},
        }
    )

    report.add("corpus non-empty", True, f"{len(games)} segments, {frames:,} frames")
    shots = counts.get("shot", 0)
    report.add(
        "shots present",
        shots >= 20,
        f"{shots} shot events (need >=20 to fit xG meaningfully)",
    )
    goals = counts.get("goal", 0)
    report.add(
        "goals present",
        goals >= 3,
        f"{goals} goal events (xG needs both classes)",
    )

    # Direction: the analyzed team must attack +x, so its goalie defends -x.
    goalie_x = []
    for tracking, _ in games:
        goalies = tracking[
            (tracking["position"] == Position.GOALIE.value)
            & (tracking["team"] == team.value)
        ]
        if not goalies.empty:
            goalie_x.append(goalies["x"].mean())
    if goalie_x:
        mean_x = float(np.mean(goalie_x))
        report.stats["own_goalie_mean_x"] = mean_x
        report.add(
            "direction normalized",
            mean_x < 0,
            f"{team.value} goalie mean x = {mean_x:+.1f} (must be negative)",
        )
    else:
        report.add("direction normalized", False, "no goalie rows found")

    return report


def label_report(
    pipeline: EPVPipeline,
    games: list[tuple[pd.DataFrame, pd.DataFrame]],
    team: Team = Team.HOME,
) -> Report:
    """Check the action-label distribution the transition model will see."""
    report = Report()
    labels: list[np.ndarray] = []
    covered_count = 0
    total_frames = 0
    shots_total = 0
    shots_inside = 0
    for tracking, events in games:
        total_frames += tracking["frame_id"].nunique()
        # Frame ids repeat across games (each broadcast has its own
        # counter), so coverage must be accumulated per game rather than
        # pooled into one set.
        game_covered: set[int] = set()
        for _, features, _ in pipeline.prepare_game(tracking, team):
            frames = features["frame_id"].to_numpy()
            game_covered |= set(frames.tolist())
            labels.append(
                make_action_labels(frames, events, pipeline.label_config)
            )
        covered_count += len(game_covered)
        game_shots = set(
            events.loc[events["event_type"] == "shot", "frame_id"].tolist()
        )
        shots_total += len(game_shots)
        shots_inside += len(game_shots & game_covered)
    if not labels:
        report.add("possessions found", False, "no qualifying possessions")
        return report

    # A shot outside every possession can never become an xG training
    # sample, however many shots the corpus contains.
    coverage = covered_count / total_frames if total_frames else 0.0
    report.stats["possession_frame_coverage"] = coverage
    report.add(
        "possessions cover the play",
        coverage >= 0.15,
        f"{coverage:.1%} of frames sit inside a possession by {team.value} "
        "(too low usually means PossessionConfig.control_radius is tighter "
        "than the tracking noise)",
    )
    if shots_total:
        report.stats["shots_inside_possessions"] = shots_inside
        report.add(
            "shots land inside possessions",
            shots_inside > 0,
            f"{shots_inside}/{shots_total} shot frames are inside a possession "
            "(zero means xG cannot be fitted no matter how many shots exist)",
        )

    all_labels = np.concatenate(labels)
    values, counts = np.unique(all_labels, return_counts=True)
    fractions = dict(zip(values, counts / len(all_labels)))
    report.stats.update({f"label_{k}": v for k, v in fractions.items()})
    report.add(
        "possessions found",
        True,
        f"{len(labels)} possessions, {len(all_labels):,} labeled frames",
    )

    shoot = fractions.get(Action.SHOOT.value, 0.0)
    report.add(
        "shoot labels present",
        shoot >= MIN_SHOOT_LABEL_FRACTION,
        f"{shoot:.4%} of frames (below {MIN_SHOOT_LABEL_FRACTION:.2%} means "
        "event alignment or the label horizon is wrong)",
    )
    keep = fractions.get(Action.KEEP.value, 0.0)
    report.add(
        "labels not degenerate",
        keep < 0.999,
        f"{keep:.2%} of frames are KEEP",
    )
    return report


def epv_report(analyses: list[PossessionAnalysis]) -> Report:
    """Check that EPV varies and rises with scoring threat."""
    report = Report()
    if not analyses:
        report.add("analyses produced", False, "no possessions analyzed")
        return report

    merged = pd.concat(
        [a.features.merge(a.epv, on="frame_id") for a in analyses], ignore_index=True
    )
    epv = merged["epv"]
    report.stats.update(
        {
            "epv_mean": float(epv.mean()),
            "epv_max": float(epv.max()),
            "epv_std": float(epv.std()),
        }
    )
    report.add("analyses produced", True, f"{len(analyses)} possessions")
    report.add(
        "epv varies",
        float(epv.std()) > 1e-6,
        f"std={epv.std():.5f} (a flat curve means the models learned nothing)",
    )
    report.add(
        "epv in range",
        bool(((epv >= 0) & (epv <= 1)).all()),
        f"range [{epv.min():.4f}, {epv.max():.4f}]",
    )

    near = merged[merged["carrier_dist_to_net"] < NEAR_NET_FT]["epv"]
    far = merged[merged["carrier_dist_to_net"] > FAR_FROM_NET_FT]["epv"]
    if len(near) and len(far):
        report.stats.update({"epv_near_net": near.mean(), "epv_far": far.mean()})
        report.add(
            "epv rises near the net",
            near.mean() > far.mean(),
            f"near={near.mean():.4f} vs far={far.mean():.4f}",
        )
    else:
        report.add(
            "epv rises near the net",
            True,
            "skipped: corpus has no frames in both distance bands",
        )
    return report
