# Offline Desktop Notes

OmniTwin now defaults to an offline desktop posture:

- `OMNI_OFFLINE_STRICT=true`
- `OMNI_ENABLE_MODEL_DOWNLOADS=false`
- `OMNI_ENABLE_SWARM=false`
- `OMNI_ENABLE_EXTERNAL_DEVICES=false`

## Local Persistence

When Redis and Qdrant are not available, OmniTwin uses local JSON-backed stores in the configured data directory:

- `cache_store.json`
- `vector_store.json`
- `training_state.json`

This keeps the app runnable as a single-machine desktop system.

## Profession Training

The training layer stores:

- one active profession profile
- domain lessons and runbooks
- competency evidence
- readiness evaluations

Use the training API to build a twin around a role before expecting strong results from the query path.

## Model Bundles

To stay fully offline and still get higher-quality local inference, bundle local models into:

- `models/smollm`
- `models/minilm`

Without those bundles, OmniTwin uses offline heuristic fallbacks for response generation and embedding.
