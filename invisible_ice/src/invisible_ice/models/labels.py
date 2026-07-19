"""Training-label derivation (Phase 3).

Turns the discrete event stream into supervised targets:

- per-frame *action* labels for the transition model — what the attacking
  team did next within a look-ahead horizon (shoot / pass / turnover,
  else keep);
- per-shot *goal* labels for the xG model.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import LabelConfig
from ..domain import Action, EventType

#: Event types that define "the next action" for labeling purposes.
_ACTION_EVENTS = {
    EventType.SHOT.value: Action.SHOOT,
    EventType.PASS.value: Action.PASS,
    EventType.TURNOVER.value: Action.TURNOVER,
}

#: A goal within this many frames of a shot marks that shot as scoring.
GOAL_ATTACH_WINDOW = 45


def make_action_labels(
    frame_ids: np.ndarray, events: pd.DataFrame, config: LabelConfig | None = None
) -> np.ndarray:
    """Action label per frame, looking ahead ``horizon_frames``.

    ``events`` must be the event rows for the same game. Goal events are
    skipped (they are the resolution of an already-labeled shot).
    """
    cfg = config or LabelConfig()
    action_events = events[events["event_type"].isin(_ACTION_EVENTS)]
    event_frames = action_events["frame_id"].to_numpy()
    event_types = action_events["event_type"].to_numpy()
    order = np.argsort(event_frames, kind="stable")
    event_frames, event_types = event_frames[order], event_types[order]

    labels = np.empty(len(frame_ids), dtype=object)
    for i, fid in enumerate(np.asarray(frame_ids)):
        j = int(np.searchsorted(event_frames, fid, side="left"))
        if j < len(event_frames) and event_frames[j] - fid <= cfg.horizon_frames:
            labels[i] = _ACTION_EVENTS[event_types[j]].value
        else:
            labels[i] = Action.KEEP.value
    return labels.astype(str)


def make_shot_samples(
    features: pd.DataFrame, events: pd.DataFrame
) -> tuple[pd.DataFrame, np.ndarray]:
    """(features at shot frames, goal labels) for xG training.

    A shot is labeled 1 when a goal event occurs within
    :data:`GOAL_ATTACH_WINDOW` frames after it.
    """
    shots = events[events["event_type"] == EventType.SHOT.value]
    goals = events[events["event_type"] == EventType.GOAL.value]["frame_id"].to_numpy()

    indexed = features.set_index("frame_id")
    rows, labels = [], []
    for shot_frame in shots["frame_id"]:
        if shot_frame not in indexed.index:
            continue
        rows.append(shot_frame)
        scored = bool(
            np.any((goals >= shot_frame) & (goals <= shot_frame + GOAL_ATTACH_WINDOW))
        )
        labels.append(int(scored))

    X = indexed.loc[rows].reset_index() if rows else features.iloc[0:0]
    return X, np.asarray(labels, dtype=int)
