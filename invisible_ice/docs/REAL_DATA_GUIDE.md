# Real Tracking Data: Integration Guide

A do-it-yourself walkthrough for replacing the synthetic corpus with real
tracking data from the **Stathletes Big Data Cup** (BDC). Everything
downstream of ingestion — features, models, EPV, attribution, export,
frontend — already works against the canonical schema, so the whole job
is building **one adapter** and checking its output:

```
BDC CSVs ──► [ YOUR ADAPTER: data/bdc.py ] ──► canonical tracking + events
                                                      │
                                     everything else already exists:
                             validate_tracking ► EPVPipeline ► export ► site
```

Work through the steps in order; each ends with a "you know you're done
when" check. Estimated effort: a focused weekend.

---

## Step 1 — Get the data

- Repo: https://github.com/bigdatacup/Big-Data-Cup-2026 (CSV downloads
  are under the repo's **Releases**; older editions live at
  `bigdatacup/Big-Data-Cup-2021` etc.).
- Read `legal.md` in the repo before using the data — it is provided for
  research/analytics purposes, and anything you publish (including the
  deployed site) should respect those terms and credit Stathletes.
- Per game you should find:
  - `... Events.csv` — play-by-play event data
  - `... Tracking_P1.csv`, `_P2`, `_P3` — tracking, one file per period
  - `... Shifts.csv` — line/shift information (optional for us)
  - `camera_orientations.csv` — which direction each team attacks, per
    period (you need this for direction normalization)

Put the raw files under `invisible_ice/rawdata/` (add that folder to
`.gitignore` — raw data does not belong in git; only tiny test fixtures
do, see Step 5).

**Done when:** you can open one game's tracking and event CSVs in pandas.

## Step 2 — Explore and pin down the conventions

Never trust a schema description, including this one. **Run the
reconnaissance script** — it answers the whole checklist below
automatically and is read-only:

```bash
python3 scripts/inspect_raw_data.py /path/to/rawdata
python3 scripts/inspect_raw_data.py /path/to/rawdata --game 2026-01-17
```

It reports the file inventory, every column with dtype/range/values,
the inferred column roles, the coordinate extents (and which
normalization path they imply), frame contiguity, the measured frame
rate, clock direction, puck-row coverage with a warning if there are
gaps, entities-per-frame stability, roster ids per team, and the event
vocabulary. Save its output:

```bash
python3 scripts/inspect_raw_data.py /path/to/rawdata > docs/raw_data_findings.txt
```

Spot-check anything surprising by hand in pandas before trusting it.

Checklist to resolve:

| Question | How to check | Feeds into |
| --- | --- | --- |
| Frame rate | count distinct `Image Id` per second of `Game Clock` | `frameRate` everywhere (likely ~30, broadcast video) |
| Are frames contiguous or gappy? | `sorted(image_ids); np.diff(...)` | gap handling (Step 4) |
| Tracking x/y units & origin | min/max of Rink Location X/Y; compare to −100..100 / −42.5..42.5 | whether you need `CoordinateNormalizer` at all |
| Direction convention | `camera_orientations.csv` + eyeball a rush | `DirectionNormalizer` mapping |
| How is the puck marked? | distinct values of the Player-or-Puck column | puck row emission |
| How are goalies identified? | Player Id ↔ roster, or position in crease | `position` column ("goalie" vs "skater") |
| How many entities per frame? | `t.groupby("Image Id").size().value_counts()` | roster stability handling (Step 4) |
| Event coords already canonical? | min/max of event X/Y (2026 events are −100..100 / −42.5..42.5) | event mapping (Step 6) |
| Clock direction | does `Game Clock` count down? | timestamp derivation |

**Done when:** every row of that table has an answer written in a comment
block at the top of your new `bdc.py`.

## Step 3 — Write the loader skeleton

Create `src/invisible_ice/data/bdc.py`. Its one job: produce dataframes
that pass the existing validators. Target schema (from
`data/schema.py`):

**Tracking** (one row per frame per entity):

| column | rule for BDC |
| --- | --- |
| `game_id` | derive from filename, e.g. `"2026-01-17-teamA-teamD"` |
| `period` | from the tracking file / Period column |
| `frame_id` | monotonically increasing **across the whole game** — offset each period's `Image Id` so periods don't collide (e.g. `period_offset + image_id_rank`) |
| `timestamp` | `frame_id / frame_rate` (seconds, increasing) |
| `entity_id` | stable per player: `"home_<n>"` / `"away_<n>"` / `"home_goalie"` / `"away_goalie"` / `"puck"`; build a `Player Id → entity_id` map once per game |
| `team` | `"home"` / `"away"` from the Team column; `"none"` for the puck |
| `position` | `"skater"` / `"goalie"` / `"puck"` |
| `x`, `y` | canonical feet (Step 5); drop the Z coordinate |

**Events** (one row per event): `game_id, frame_id, event_type, team,
player_id` — see Step 6 for the mapping.

Suggested public API (mirrors `synthetic.py` so the pipeline code
doesn't care which one it gets):

```python
class BigDataCupLoader:
    def __init__(self, rink=None, frame_rate=30.0): ...
    def load_game(self, tracking_paths: list[Path], events_path: Path,
                  orientations_path: Path, game_id: str
                  ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Returns (tracking, events) in canonical schema, validated."""
```

End `load_game` with the existing gates — this is the whole contract:

```python
from .schema import validate_tracking, validate_events
return validate_tracking(tracking), validate_events(events)
```

**Done when:** the file imports and the class instantiates (methods can
still be `NotImplementedError` stubs).

## Step 4 — Tracking: the fiddly parts

Real broadcast tracking is messy where the synthetic data was clean.
Handle these explicitly, in this order:

1. **Frame index** — build the game-wide `frame_id` (Step 3 rule), then
   deduplicate: if an `Image Id` appears twice for the same entity, keep
   the first.
2. **The puck row must exist every frame** — the possession state
   machine raises on frames with skaters but no puck. Where the puck is
   missing for short runs (occlusion), linearly interpolate its x/y
   between the surrounding known frames (`pandas` `Series.interpolate`
   after reindexing on the frame axis); drop frames inside long gaps
   (> ~1 s) instead of inventing positions.
3. **Roster stability inside a possession** — the exporter requires
   every entity present in **every** frame of a possession (players drop
   out of broadcast view constantly). Easiest robust policy: after
   possession detection, for each possession reindex each entity onto
   the possession's frame axis and interpolate small gaps; drop entities
   visible in < ~70% of the possession's frames, and drop possessions
   that lose the puck carrier's team below 3 skaters.
4. **Off-camera coordinates** — clamp nothing; drop rows whose x/y fall
   outside the rink by more than a foot or two (tracking glitches), then
   let interpolation refill.
5. **Timestamps** — derive from `frame_id / frame_rate`, not from `Game
   Clock` (the clock stops; kinematics needs wall-time spacing between
   frames, and stoppages should instead *split* possessions — the state
   machine's loose-puck decay handles most of this on its own).

**Done when:** for one real period,
`validate_tracking(loader_output)` passes and
`tracking.groupby("frame_id").size()` shows a puck row in every frame.

## Step 5 — Coordinates and direction

- **Units/origin:** if Step 2 showed tracking already in the canonical
  frame (x −100..100, y −42.5..42.5, center-ice origin — the 2026 event
  data is), pass coordinates through untouched. If it uses a
  corner-origin 0..200 × 0..85 frame (the 2021-era convention), reuse
  the existing adapter:

  ```python
  from invisible_ice.data.normalize import CoordinateNormalizer, BIG_DATA_CUP
  tracking = CoordinateNormalizer(BIG_DATA_CUP).transform(tracking)
  ```

  Any other extent: construct a `SourceCoordinateSystem(x_min, x_max,
  y_min, y_max)` with the observed bounds. Never hand-roll the affine
  math — the adapter exists and is tested.

- **Direction:** the engine assumes the analyzed team attacks **+x**.
  Build the per-period flip map from `camera_orientations.csv`:

  ```python
  from invisible_ice.data.normalize import DirectionNormalizer
  tracking = DirectionNormalizer({1: True, 2: False, 3: True}).transform(tracking)
  ```

  (`True` = the reference team already attacks +x that period.) Fallback
  if orientations are ambiguous: `DirectionNormalizer.infer(tracking,
  Team.HOME)` — but prefer the explicit metadata; verify either way by
  animating a possession (Step 8).

**Done when:** a plotted rush moves left→right for the team you analyze,
in every period.

## Step 6 — Map the event taxonomy

BDC events → canonical `EventType` (only four matter to the models;
ignore the rest):

| BDC event | canonical | notes |
| --- | --- | --- |
| `Shot` | `shot` | player = shooter |
| `Goal` | `goal` **and** a `shot` | our labeler treats goal as the resolution of a shot; if BDC logs a Goal without a paired Shot row, emit both at the same frame |
| `Play` (completed pass) | `pass` | player = passer |
| `Incomplete Play` | `turnover` | pass that missed |
| `Takeaway` | `turnover` | **attributed to the team that lost the puck** — our events are attacking-team events, so a Takeaway *by the defense* is a turnover *by the attackers*; flip the team column |
| `Puck Recovery`, `Dump In/Out`, `Zone Entry`, `Faceoff Win`, `Penalty` | *(skip)* | not part of the transition label set (v1) |

Event rows carry a Clock/Period, not an `Image Id` — align each event to
the nearest `frame_id` by clock time within the period; when the clock
maps between two frames, take the earlier one. Sanity-check the
alignment: at a Shot's frame, the puck should be near the shooter's
coordinates.

**Done when:** `validate_events(...)` passes and per-game counts look
like hockey (dozens of passes, ~5–15 shots per team, 0–5 goals).

## Step 7 — Commit a fixture and write the tests (before wiring further)

Cut a **tiny** sample from one real game — ~3 seconds of tracking
(~90 frames) plus the handful of events inside that window — into
`tests/fixtures/bdc_sample/` (a few KB of CSV; check `legal.md` allows
redistribution of an excerpt — if unsure, build the fixture by
*obfuscating* it: jitter coordinates, renumber players, keep structure).

Write `tests/test_bdc.py` mirroring `test_synthetic.py`'s shape:

- output passes `validate_tracking` / `validate_events`
- puck present every frame; entity ids stable across frames
- known hand-checked values: "at frame N, home_3 is at (x, y)"
- direction: mean home x in the fixture is the sign you expect
- event alignment: the fixture's shot lands on the right frame
- degenerate inputs: empty file, missing puck column → clear errors

Run the full suite (`python3 -m pytest -q`) — the existing 126 tests
must stay green; your adapter must not touch any existing module.

**Done when:** `pytest tests/test_bdc.py` passes offline, no rawdata
needed.

## Step 8 — First full run + eyeball check

```python
from invisible_ice.data.bdc import BigDataCupLoader
from invisible_ice.domain import Team
from invisible_ice.pipeline import EPVPipeline

loader = BigDataCupLoader()
games = [loader.load_game(...) for each game you downloaded]

pipeline = EPVPipeline()
pipeline.fit(games, team=Team.HOME)
analyses = pipeline.analyze_game(games[0][0], team=Team.HOME)
```

Numbers to check before believing anything:

- **Possession counts**: a period should yield tens of possessions, not
  2 and not 500. Too few → `PossessionConfig.control_radius` too small
  for noisy tracking (try 5–6 ft) or `loose_frames` too short; too many
  → the opposite.
- **Class balance**: print `np.unique(y, return_counts=True)` from the
  labeler. `shoot` should be a few percent; if it's ~0, your event
  alignment or the `LabelConfig.horizon_frames` (scale it to the real
  frame rate: ~0.5 s of frames) is off.
- **xG classes**: you need both goals and non-goal shots across the
  corpus. One game is not enough to train on — use every game you can
  download.
- **The smell test**: EPV near the net must beat EPV in the neutral zone
  (the integration test `test_epv_responds_to_scoring_threat` shows the
  pattern — add a real-data twin of it).

Then **watch a possession**: export it (Step 9), load the site locally
(`npm run dev`), and check the dots skate like hockey players and the
EPV curve spikes when your eyes say danger. This catches
direction-flip and alignment bugs nothing else will.

## Step 9 — Export and deploy

Generalize `scripts/make_demo_data.py` into a `make_real_data.py` that
loops over your games:

```python
payload = game_payload(game_id, tracking, analyses, frame_rate=FPS)
write_game_json(payload, f"frontend/public/data/{game_id}.json")
```

Either point `App.tsx`'s fetch at one game's file, or (better) also
write a `frontend/public/data/index.json` manifest and add the small
game-picker UI. Commit the JSON payloads, push, and the Vercel hookup
you already configured redeploys automatically from `master`.

## Step 10 — Definition of done

- [ ] `rawdata/` gitignored; only the small fixture is committed
- [ ] `test_bdc.py` green offline; whole suite green (126 + yours)
- [ ] One full game loads, validates, trains, and analyzes end-to-end
- [ ] Direction verified visually in every period
- [ ] Possession/shot/goal counts pass the Step 8 sanity numbers
- [ ] Payloads exported, site redeployed, replay looks like hockey
- [ ] Stathletes credited on the site / README per `legal.md`

## Troubleshooting quick reference

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `SchemaError: frame X has skaters but no puck row` | puck occluded in broadcast | Step 4.2 interpolation |
| all entity ids unstable frame to frame | using a track id as identity | Appendix: use team + jersey |
| `ValueError: entity ... missing frames in possession` (export) | players leaving camera view | Step 4.3 reindex/interpolate policy |
| EPV flat ~0 everywhere | no `shoot` labels reached the model | event→frame alignment; horizon in frames vs seconds |
| Possessions absurdly short/long | control radius vs tracking noise | tune `PossessionConfig`; try radius 5–6, `loose_frames` ≈ 0.3 s of frames |
| Team attacks the wrong way in P2 | period flip missed | `camera_orientations.csv` mapping in Step 5 |
| Kinematics speeds are insane (>50 ft/s) | frame gaps treated as 1/30 s | timestamps from frame_id after gap-dropping, not raw row order |
| xG model refuses to fit | zero goals in corpus | more games; confirm Goal events emit a paired `shot` |

---

# Appendix — Resolved conventions for BDC 2026 (2025-26 season files)

Measured from the real files (10 games, 33 tracking files) with
`scripts/inspect_raw_data.py`. These are answers, not guesses; they turn
Steps 2–6 into mechanical work.

## Tracking files (`<game>.Tracking_P<n>.csv`)

| Aspect | Finding | Consequence for `bdc.py` |
| --- | --- | --- |
| Coordinates | x ∈ [−100, 100], y ∈ [−41.9, 42.5] feet, center origin | **Already canonical** — no `CoordinateNormalizer`. Drop the Z column. |
| `Image Id` | string `"<game>_065468"` | Parse trailing digits to int; offset per period so P1/P2/P3 don't collide. |
| Frame rate | **30 fps** (34,413 frames / 1,200 s of clock) | `timestamp = frame_index / 30.0`. |
| Frame gaps | ids continue through stoppages; ~31 gaps/period, up to ~666 | Ids are broadcast time. **Split each period into contiguous segments at gaps** and process separately — never let kinematics span a whistle. |
| `Player or Puck` | `Player` / `Puck` | Sets `position` (with the goalie rule below). |
| `Team` | `Home` / `Away`, null on puck rows | Direct map to `Team`; puck gets `team="none"`. |
| `Player Id` | **1,058 distinct per period** (range 1–15,130) | A per-detection **track id**, not a player. Do **not** use for identity. |
| `Player Jersey Number` | 36 distinct | **The real identity.** `entity_id = f"{team}_{jersey}"`. |
| Goalies | jersey number is the literal string **`"Go"`** | `position = "goalie" if jersey == "Go" else "skater"`. No inference needed. |
| Unidentified rows | ~1,758 player rows/period with null jersey | Drop — they cannot get a stable `entity_id`. |
| Missing coordinates | ~1,957 null x/y per period (0.6%) | Drop those rows, then interpolate within a segment if needed. |
| Puck coverage | **100% of frames** | Step 4.2 interpolation is a **no-op** for this feed. |
| Roster completeness | median 10 entities/frame (max 13) | Partial rosters are the norm → per-possession reindexing (Step 4.3) is mandatory. |
| Goalie presence | goalies appear in only ~33–39% of frames | The xG model conditions on goalie location: forward-fill the goalie within a segment, or fall back to the crease (±87, 0) when absent. Decide explicitly. |

## Event files (`<game>.Events.csv`)

One file per game covering all periods; 1,878 rows in the sample game.

| Aspect | Finding |
| --- | --- |
| Coordinates | `X_Coordinate` / `Y_Coordinate`, already canonical |
| Identity | `Player_Id` holds **jersey numbers** (34 distinct) — joins to the tracking jersey column, *not* to `Player Id` |
| Clock | `Clock` mm:ss at **1-second resolution** + `Period` |
| Vocabulary | Play 672, Puck Recovery 511, Incomplete Play 174, Zone Entry 156, Dump In/Out 131, Shot 113, Faceoff Win 59, Takeaway 50, Penalty Taken 6, Goal 6 |
| Extras | `Detail_2` ∈ {Blocked, Missed, On Net}; `Player_Id_2` = pass receiver / second player |

**Event→frame alignment (amends Step 6):** a 1-second clock covers ~30
frames, so the clock alone cannot identify a frame. Narrow to the frames
inside that clock second, then pick the one whose **puck position is
nearest the event's X/Y**. Sanity-check by confirming the shooter is near
the puck at the chosen frame.

**Training volume:** ~113 shots and 6 goals per game → roughly **1,130
shots / 60 goals** across 10 games. Enough to fit xG.

## Direction (`camera_orientations.csv`)

One row per game: `GoalieTeamOnRightSideOfRink1stPeriod` ∈ {Home, Away}.
That names the team whose **goalie defends +x in period 1** — i.e. the
team that *attacks −x* in P1. Teams change ends each period, so:

```python
# For the team you analyze (say HOME):
home_attacks_right_p1 = (orientation_flag == "Away")
attacking_right = {p: home_attacks_right_p1 == (p % 2 == 1) for p in (1, 2, 3)}
DirectionNormalizer(attacking_right).transform(tracking)
```

Verified against the 2025-10-11 game: flag is `Away`, and the measured
mean x is **Away goalie +80.3 / Home goalie −85.4** in P1 — Home attacks
+x in P1, so `{1: True, 2: False, 3: True}`. Always re-verify per game by
checking goalie mean x per period; it is a one-line assertion and it
catches the single most damaging class of bug in this pipeline.

---

# Appendix B — `bdc.py` blueprint

The decomposition for Step 3. Each function does one thing and is
testable on its own; the orchestrator only wires them together.

## Pre-flight

Confirm whether `Image Id` continues across periods or restarts:

```bash
python3 scripts/inspect_raw_data.py rawdata --game 2025-10-11
# compare the P1 id range (65468-132578) with P2's
```

If P2 restarts near P1's start, add a per-period offset when building
`frame_id`; if it continues, the parsed id is already game-unique.

## Module constants

```python
TRACKING_COLS = {"frame": "Image Id", "clock": "Game Clock", ...}
GOALIE_JERSEY = "Go"
EVENT_MAP = {"Shot": EventType.SHOT, "Play": EventType.PASS,
             "Incomplete Play": EventType.TURNOVER,
             "Takeaway": EventType.TURNOVER, "Goal": EventType.GOAL}
TAKEAWAY_FLIPS_TEAM = True   # credited to the team that GAINS the puck
FRAME_RATE = 30.0
```

## Functions

| Function | Responsibility |
| --- | --- |
| `parse_frame_id(series, period)` | trailing digits -> int, plus period offset if needed |
| `build_entity_id(team, jersey, kind)` | `"puck"`, `"home_goalie"`, `"home_44"`; the single source of identity |
| `load_tracking_period(path, period)` | read one CSV -> canonical tracking rows for that period (no direction flip yet) |
| `direction_map(orientations, game_id, team)` | orientation flag -> `{period: attacks_right}` (see Appendix A) |
| `load_events(path, game_id, frame_lookup)` | events CSV -> canonical events, frames resolved |
| `align_event(event, frames_in_second, puck_xy)` | pick the frame whose puck is nearest the event's X/Y |
| `split_segments(tracking, events, max_gap=2)` | contiguous play runs -> separate units, each with its own `game_id` suffix |
| `BigDataCupLoader.load_game(...)` | orchestrate the above, end with `validate_tracking` / `validate_events` |

## Order of operations (this order matters)

1. Load each period's tracking; parse frame ids; drop null-jersey and
   null-coordinate rows; build `entity_id`; set `position` from the
   `"Go"` jersey rule.
2. **Align events to frames using RAW coordinates** — canonical events
   carry no x/y, so once tracking is flipped the geometric match is gone.
3. Apply `DirectionNormalizer` to tracking.
4. Apply the goalie-presence policy (forward-fill or crease fallback).
5. `split_segments(...)` — never let a possession or a velocity span a
   stoppage.
6. Validate each segment; return the list.

## Two mappings that bite

- **Event team names**: tracking says `Home`/`Away`, but events say
  `Team A`/`Team D`. Map via the events file's own `Home_Team` /
  `Away_Team` columns: `"home" if row.Team == row.Home_Team else "away"`.
- **Takeaway direction**: a Takeaway is credited to the team that *won*
  the puck, so emit it as a `turnover` for the **other** team.

## Suggested API

```python
class BigDataCupLoader:
    def __init__(self, frame_rate: float = 30.0, min_segment_frames: int = 60): ...

    def load_game(self, tracking_paths, events_path, orientations_path,
                  game_id, team=Team.HOME) -> list[tuple[DataFrame, DataFrame]]:
        """One (tracking, events) pair per contiguous play segment."""
```

Returning segments keeps the consumer trivial, since `EPVPipeline.fit`
already takes a list of games:

```python
games = []
for paths in discovered_games:
    games.extend(loader.load_game(*paths))
pipeline = EPVPipeline().fit(games, team=Team.HOME)
```

## Scope decision for v1

Analyze **one team** (HOME) first. The direction map is team-relative, so
covering both teams means loading the game twice with opposite maps.
Get one team end-to-end before doubling the surface area.

## Done when

- `load_game` on one real game returns segments that pass
  `validate_tracking` / `validate_events`
- every segment has a puck row in every frame and stable `entity_id`s
- a per-period assertion confirms the analyzed team's goalie sits at
  negative mean x (it defends −x once the team attacks +x)
