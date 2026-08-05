# Invisible Ice — Framewise Expected Possession Value (EPV) Engine

Backend implementation of Phases 1–3 of the Invisible Ice framework:
turning raw hockey tracking data into a continuous, frame-by-frame
Expected Possession Value surface with per-player micro-attribution.

```
tracking + events
      │
      ▼
┌──────────────────────────────────────────────────────────────┐
│ Phase 1 · data/        ingestion, normalization, possession   │
│   schema.py            canonical long-format schema + checks  │
│   normalize.py         coordinate + direction normalization   │
│   possession.py        rule-based possession state machine    │
│   storage.py           partitioned Parquet repository         │
│   synthetic.py         deterministic synthetic data generator │
└──────────────────────────────┬───────────────────────────────┘
                               ▼
┌──────────────────────────────────────────────────────────────┐
│ Phase 2 · features/    spatial physics -> per-frame features  │
│   kinematics.py        finite-difference velocity/accel       │
│   pressure.py          nearest defender, gap-closure rate     │
│   lanes.py             passing-lane openness (geometry)       │
│   royal_road.py        Royal Road crossing flags              │
│   builder.py           extractor composition (FrameFeature-   │
│                        Builder)                               │
└──────────────────────────────┬───────────────────────────────┘
                               ▼
┌──────────────────────────────────────────────────────────────┐
│ Phase 3 · models/      probabilistic models + EPV surface     │
│   base.py              ProbabilityModel strategy interface    │
│   transition.py        P(shoot/pass/keep/turnover | state)    │
│   xg.py                framewise P(goal | shot now)           │
│   labels.py            event stream -> training targets       │
│   epv.py               backward Markov recursion -> EPV curve │
│   attribution.py       on-/off-puck EPV-added split           │
└──────────────────────────────┬───────────────────────────────┘
                               ▼
             pipeline.py — EPVPipeline facade (fit / analyze)
```

## Quick start

```bash
pip install -e ".[dev]"     # needs Python 3.11+
pytest                      # full unit + integration suite
```

**Real tracking data.** `data/bdc.py` adapts Stathletes Big Data Cup
files to the canonical schema; `scripts/make_real_data.py` runs the whole
chain — discover games, load, train, analyze, export payloads plus an
index manifest — and gates each stage on the checks in `diagnostics.py`,
exiting non-zero if any fail:

```bash
python3 scripts/inspect_raw_data.py rawdata   # what conventions does the feed use?
python3 scripts/make_real_data.py rawdata     # -> frontend/public/data/*.json + index.json
```

See `docs/REAL_DATA_GUIDE.md` for the measured conventions and the
step-by-step walkthrough.

```python
from invisible_ice import EPVPipeline, Team
from invisible_ice.data.synthetic import SyntheticGameGenerator

games = [SyntheticGameGenerator(seed=s).generate_game(f"g{s}") for s in range(10)]
pipeline = EPVPipeline().fit(games, team=Team.HOME)

tracking, _ = games[0]
for analysis in pipeline.analyze_game(tracking, team=Team.HOME):
    print(analysis.possession)
    print(analysis.epv.head())          # frame_id, epv, xg, p_shoot, ...
    print(analysis.attribution)         # per-player on-/off-puck EPV added
```

## The EPV computation

The engine implements the spatial Markov decomposition

    EPV(S_t) = P(shoot|S_t)·xG(S_t)
             + P(turnover|S_t)·0
             + [P(pass|S_t) + P(keep|S_t)]·E[EPV(S_{t+Δt})]

with the continuation term approximated by the realized next state
(one-step bootstrap), evaluated by backward recursion over each
possession (`models/epv.py`). The two learned components are:

- **TransitionModel** — multiclass gradient boosting over
  shoot / pass / keep / turnover, labeled by the next event within a
  configurable look-ahead horizon (`models/labels.py`).
- **XGModel** — binary gradient boosting trained on shot frames
  (goal vs. no goal), applied to *every* frame to answer "what if the
  carrier released the shot right now?".

**Micro-attribution** (`models/attribution.py`) splits each
frame-to-frame ΔEPV between the carrier (on-puck) and teammates whose
movement changed the threat picture in the direction of the swing
(off-puck), via a pluggable `AttributionStrategy`.

## Architectural patterns

| Pattern | Where | Why |
| --- | --- | --- |
| Fail-fast schema validation | `data/schema.py` | one canonical contract at the ingestion boundary; downstream code never re-validates |
| Adapter | `data/normalize.py` | any source feed (e.g. Big Data Cup 0–200×0–85) maps onto the canonical rink via config, not code changes |
| State machine w/ hysteresis | `data/possession.py` | deterministic, tunable puck-state rules (control radius, min control frames, loose decay) |
| Repository | `data/storage.py` | Parquet partitioning (game/period) hidden behind an interface; storage backend is swappable |
| Composite / pipeline | `features/builder.py` | each feature family is one small extractor; new features = new extractor, builder untouched |
| Strategy | `models/base.py`, `models/attribution.py` | scikit-learn today, XGBoost/LightGBM/PyTorch tomorrow — swap the estimator, not the pipeline; same for attribution rules |
| Facade + dependency injection | `pipeline.py` | `EPVPipeline` owns dataflow only; every collaborator is injectable and mockable |
| Deterministic simulation | `data/synthetic.py` | seeded physics-plausible generator so the whole system trains and tests offline, reproducibly |

## Coordinate conventions

- Canonical rink: x ∈ [-100, 100], y ∈ [-42.5, 42.5] (feet); attacking
  net at (89, 0); offensive blue line at x = 25.
- After `DirectionNormalizer`, the team of interest always attacks +x.
- The Royal Road is y = 0 beyond the offensive blue line.

## Testing

Every module has a dedicated test file under `tests/` (183 Python tests
plus 49 in the frontend):
geometry and kinematics are verified against exact closed-form motion,
the possession machine against hand-constructed scenarios, the EPV
recursion against hand-computed arithmetic using stub models, and the
full pipeline end-to-end on a 10-game synthetic corpus (bounded EPV,
probability conservation, attribution conservation, and a sanity check
that EPV is higher near the net than in the neutral zone).

## Phase 4 — interactive frontend

`src/invisible_ice/export.py` serializes `PossessionAnalysis` results
into a compact, versioned JSON payload (structure-of-arrays layout,
coordinates quantized to 0.1 ft, probabilities to 4 decimals), and
`frontend/` is a Vite + React + TypeScript viewer for it:

- **Rink player** — HTML5 Canvas renderer (devicePixelRatio-aware) with
  full rink markings, the Royal Road, color-coded team dots with jersey
  numbers, goalie squares, and fading velocity trails, interpolated to
  the display refresh rate from 30 fps tracking.
- **EPV timeline** — d3-scale/d3-shape line + area chart with a
  synchronized playhead, crosshair + tooltip on hover (EPV, xG,
  P(shoot)), and click-to-seek into the replay.
- **Controls & context** — play/pause/scrub/speed, per-possession
  picker chips, live EPV readout, and the per-player on-/off-puck
  attribution table.
- **Multi-game catalog** — reads `data/index.json` when present and
  offers a game picker; falls back to the single bundled demo payload
  when no manifest has been exported.
- **Theming** — light and dark from a validated palette (the categorical
  team colors pass CVD-separation and contrast checks in both modes);
  identity is never color-alone (shapes for goalies/puck, numbered
  skaters, legend).

```bash
cd frontend
npm install
npm test                # 40 vitest unit tests (pure logic + stub-canvas draws)
npm run dev             # dev server against public/data/demo.json
npm run build           # type-check + production bundle (relative base,
                        # deployable to any static host / edge CDN)
python3 ../scripts/make_demo_data.py   # regenerate the demo payload
```

The playback engine, interpolation, payload validation, world→canvas
transform, and both canvas draw layers are unit-tested; rendering was
also verified by screenshotting the built app in both color schemes.
