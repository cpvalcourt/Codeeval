"""End-to-end orchestration: tracking + events -> framewise EPV + attribution.

The pipeline is a facade over the phase layers. It owns no algorithmic
logic of its own — it wires the possession state machine, the feature
builder, the models, and the attribution engine together, and defines the
train/inference dataflow. Every collaborator is injected (with sensible
defaults), so any layer can be swapped or mocked in tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .config import LabelConfig, PossessionConfig, RinkConfig
from .data.possession import PossessionStateMachine
from .domain import Possession, Team
from .features.builder import FeatureContext, FrameFeatureBuilder
from .features.kinematics import add_kinematics
from .models.attribution import MicroAttributionEngine
from .models.epv import EPVEngine
from .models.labels import make_action_labels, make_shot_samples
from .models.transition import TransitionModel
from .models.xg import XGModel


@dataclass
class PossessionAnalysis:
    """Everything the frontend needs to replay one possession."""

    possession: Possession
    features: pd.DataFrame
    epv: pd.DataFrame
    attribution: pd.DataFrame


@dataclass
class EPVPipeline:
    rink: RinkConfig = field(default_factory=RinkConfig)
    possession_config: PossessionConfig = field(default_factory=PossessionConfig)
    label_config: LabelConfig = field(default_factory=LabelConfig)
    feature_builder: FrameFeatureBuilder = field(default_factory=FrameFeatureBuilder)
    #: Possessions shorter than this are noise (won't train or score well).
    min_possession_frames: int = 20
    transition_model: TransitionModel | None = None
    xg_model: XGModel | None = None

    def __post_init__(self) -> None:
        self._state_machine = PossessionStateMachine(self.possession_config)

    # ------------------------------------------------------------------
    # shared per-game preparation
    # ------------------------------------------------------------------

    def prepare_game(
        self, tracking: pd.DataFrame, team: Team
    ) -> list[tuple[Possession, pd.DataFrame, pd.Series]]:
        """(possession, features, carrier_by_frame) for each qualifying
        possession by ``team`` in one game's canonical tracking data."""
        game_id = tracking["game_id"].iloc[0]
        states = self._state_machine.annotate(tracking)
        carrier_all = states.set_index("frame_id")["controller"]
        possessions = self._state_machine.extract_possessions(states, game_id)

        enriched = add_kinematics(tracking)
        out = []
        for possession in possessions:
            if possession.team != team:
                continue
            if possession.n_frames < self.min_possession_frames:
                continue
            mask = enriched["frame_id"].between(
                possession.start_frame, possession.end_frame
            )
            slice_df = enriched[mask]
            carrier = carrier_all.loc[possession.start_frame : possession.end_frame]
            ctx = FeatureContext(
                tracking=slice_df,
                attacking_team=team,
                carrier_by_frame=carrier,
                rink=self.rink,
            )
            features = self.feature_builder.build(ctx)
            out.append((possession, features, carrier))
        return out

    # ------------------------------------------------------------------
    # training
    # ------------------------------------------------------------------

    def fit(
        self,
        games: list[tuple[pd.DataFrame, pd.DataFrame]],
        team: Team = Team.HOME,
    ) -> "EPVPipeline":
        """Train transition and xG models from (tracking, events) games."""
        feature_frames: list[pd.DataFrame] = []
        action_labels: list[np.ndarray] = []
        shot_frames: list[pd.DataFrame] = []
        goal_labels: list[np.ndarray] = []

        for tracking, events in games:
            for _, features, _ in self.prepare_game(tracking, team):
                feature_frames.append(features)
                action_labels.append(
                    make_action_labels(
                        features["frame_id"].to_numpy(), events, self.label_config
                    )
                )
                shot_X, shot_y = make_shot_samples(features, events)
                if len(shot_X):
                    shot_frames.append(shot_X)
                    goal_labels.append(shot_y)

        if not feature_frames:
            raise ValueError("no qualifying possessions found in training games")
        X = pd.concat(feature_frames, ignore_index=True)
        y = np.concatenate(action_labels)
        names = self.feature_builder.feature_names
        self.transition_model = TransitionModel(names).fit(X, y)

        if not shot_frames:
            raise ValueError("no shots found in training games; cannot fit xG model")
        shots_X = pd.concat(shot_frames, ignore_index=True)
        shots_y = np.concatenate(goal_labels)
        self.xg_model = XGModel(names).fit(shots_X, shots_y)
        return self

    # ------------------------------------------------------------------
    # inference
    # ------------------------------------------------------------------

    def analyze_game(
        self, tracking: pd.DataFrame, team: Team = Team.HOME
    ) -> list[PossessionAnalysis]:
        """Framewise EPV + per-player attribution for each possession."""
        if self.transition_model is None or self.xg_model is None:
            raise RuntimeError("pipeline models are not fitted; call fit() first")
        epv_engine = EPVEngine(self.transition_model, self.xg_model)
        attribution_engine = MicroAttributionEngine(rink=self.rink)

        analyses = []
        for possession, features, carrier in self.prepare_game(tracking, team):
            epv = epv_engine.compute(features)
            mask = tracking["frame_id"].between(
                possession.start_frame, possession.end_frame
            )
            attribution = attribution_engine.attribute_possession(
                epv, tracking[mask], carrier, team
            )
            analyses.append(PossessionAnalysis(possession, features, epv, attribution))
        return analyses
