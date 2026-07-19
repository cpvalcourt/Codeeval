# Deployment Guide — Invisible Ice

The system deploys in two independent halves, by design:

1. **The engine (Python)** runs *offline, ahead of time*. It trains the
   models, computes EPV for each possession, and serializes the results
   to static JSON payloads. It is a batch job, not a runtime service —
   there is no Python server to host, scale, or secure.
2. **The viewer (frontend/)** is a fully static single-page app. The
   production build is plain HTML/CSS/JS plus the JSON payloads, so it
   can be served from any static host or edge CDN (Cloudflare Pages,
   Vercel, GitHub Pages, S3+CloudFront, nginx). No environment
   variables, no API keys, no backend.

```
engine (batch, anywhere Python runs)          edge / static host
┌─────────────────────────────────┐   deploy   ┌──────────────────┐
│ fit models → analyze games →    │  ───────►  │ dist/            │
│ export.py → public/data/*.json  │            │  index.html      │
└─────────────────────────────────┘            │  assets/*.js/css │
                                               │  data/*.json     │
                                               └──────────────────┘
```

---

## 1. Produce the data payloads

Each game becomes one JSON file under `frontend/public/data/`. Vite
copies everything in `public/` into the build output verbatim, so a
payload committed or generated there ships automatically.

Demo data (synthetic corpus):

```bash
cd invisible_ice
pip install -e ".[dev]"
python3 scripts/make_demo_data.py     # writes frontend/public/data/demo.json
```

Real data: run your ingestion + `EPVPipeline`, then serialize each game:

```python
from invisible_ice.export import game_payload, write_game_json

payload = game_payload(game_id, tracking, pipeline.analyze_game(tracking))
write_game_json(payload, "frontend/public/data/{game_id}.json")
```

Payloads are minified and quantized (0.1 ft coordinates, 4-decimal
probabilities); the demo game is ~58 KiB raw / ~15 KiB gzipped. Budget
roughly 15–25 KiB/possession raw for full games and let the CDN's
gzip/brotli handle the rest — no protobuf step is needed at this scale.

## 2. Build the frontend

```bash
cd invisible_ice/frontend
npm ci                 # reproducible install from package-lock.json
npm test               # 40 unit tests
npm run build          # tsc --noEmit + vite build → dist/
npm run preview        # optional: serve dist/ locally to smoke-test
```

The Vite config uses `base: "./"` (relative asset paths), so `dist/`
works from a domain root, a subpath, or even `file://` — no per-host
configuration.

## 3. Host it

### Cloudflare Pages (the plan's default)

One-time, from the dashboard: *Workers & Pages → Create → Pages →
connect the GitHub repo*, then set:

| Setting | Value |
| --- | --- |
| Root directory | `invisible_ice/frontend` |
| Build command | `npm ci && npm run build` |
| Build output directory | `dist` |

Every push to the production branch then deploys globally; other
branches get preview URLs automatically. CLI alternative (no repo
hookup) — build locally, then:

```bash
npx wrangler pages deploy dist --project-name invisible-ice
```

### Vercel

*Add New Project → import the repo*, set **Root Directory** to
`invisible_ice/frontend`; Vercel auto-detects Vite (`npm run build`,
output `dist`). Or `npx vercel deploy` from `frontend/`.

### GitHub Pages / any static server

Serve the contents of `dist/` as-is. For GitHub Pages, publish `dist/`
to the `gh-pages` branch (e.g. with `actions/deploy-pages`); the
relative base means the `/<repo>/` subpath works without changes.

## 4. Caching & headers (recommended)

- `assets/*` — filenames are content-hashed by Vite: cache forever
  (`Cache-Control: public, max-age=31536000, immutable`). Cloudflare
  Pages and Vercel apply this to hashed assets by default.
- `data/*.json` — cache but revalidate (`max-age=300` or
  `stale-while-revalidate`) so republished game payloads show up
  without a hard refresh.
- `index.html` — `no-cache` (both hosts default to this).
- Compression (gzip/brotli) is automatic on Cloudflare and Vercel.

## 5. Updating a deployed site with new games

1. Run the engine batch to produce/refresh `public/data/*.json`.
2. Commit the payloads (or generate them in the build step by adding
   `python3 ../scripts/make_demo_data.py &&` before `npm run build`
   if the host image has Python; committing is simpler and keeps
   builds fast and hermetic).
3. Push — the connected host rebuilds and deploys.

The app currently loads `data/demo.json`; pointing it at a game picker
over multiple payload files is a frontend-only change (fetch a
`data/index.json` manifest listing available games).

## 6. CI gate

Recommended checks before any deploy (all offline, no network flakes):

```bash
# engine
cd invisible_ice && python3 -m pytest -q
# viewer
cd frontend && npm ci && npm test && npm run build
```

Wire these as a GitHub Actions workflow on pull requests so the Pages/
Vercel deploy only ever ships a green build.
