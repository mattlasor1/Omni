# Offline Desktop Notes

OmniTwin now defaults to an offline desktop posture:

- `OMNI_OFFLINE_STRICT=true`
- `OMNI_ENABLE_MODEL_DOWNLOADS=false`
- `OMNI_ENABLE_SWARM=false`
- `OMNI_ENABLE_EXTERNAL_DEVICES=false`
- `OMNI_ALLOW_EXTERNAL_NETWORK=false`

Strict offline mode installs a runtime network guard in the backend. It allows loopback traffic for `127.0.0.1` and `localhost`, then blocks non-local socket access before a request can leave the machine. The Electron shell also blocks non-local `http`, `https`, `ws`, and `wss` requests from the renderer.

## Local Persistence

When Redis and Qdrant are not available, OmniTwin uses local JSON-backed stores in the configured data directory:

- `cache_store.json`
- `vector_store.json`
- `training_state.json`

This keeps the app runnable as a single-machine desktop system.

## Owner Training

The training layer stores:

- one active owner profile
- local lessons, preferences, corrections, and workflow notes
- workspace snapshots imported from local repos and operator folders
- competency evidence
- readiness evaluations
- artifact reviews and owner-model task evaluations
- live interaction history
- self-review reports and remediation items

Use the training API to build a twin around its owner before expecting strong results from the query path. The highest-leverage path is to import real local evidence so Omni can ground itself in actual notes, decisions, examples, configs, code, and workflow artifacts.

## Continuous Review

The local maintenance scheduler now includes a dedicated review cycle. That cycle:

- scores the active twin against workspace-derived evaluation scenarios
- records recent interaction coverage
- generates remediation tasks for weak areas
- writes self-reflection lessons back into local training memory when enough grounded evidence exists

You can trigger it directly through `POST /api/v1/training/self-review` or `POST /api/v1/maintenance/review`.

## Model Bundles

To stay fully offline and still get higher-quality local inference, bundle local models into:

- `models/smollm`
- `models/minilm`

Without those bundles, OmniTwin uses offline heuristic fallbacks for response generation and embedding.

## Desktop Package

Run `npm run build` in `frontend` before packaging. The Next frontend exports static files to `frontend/out`, and the packaged Electron app serves those files from a local loopback HTTP server instead of starting `npm`.

The Windows package command in `electron_app` includes:

- `src`
- `frontend/out`
- `.venv`
- `models`
- `requirements.txt`
- `.env.example`

That makes the release folder runnable as a local desktop bundle on the same platform after dependencies have been installed.
