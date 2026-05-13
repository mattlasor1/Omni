# OmniTwin Offline Workbench

OmniTwin is an offline-first digital twin runtime for building a profession-shaped local assistant. The current repo focuses on the foundation for a downloadable desktop application that can:

- run without Redis, Qdrant, or Docker
- stay inside local memory and local tools by default
- accept explicit training lessons and a profession profile
- answer from its own local training state rather than pretending to know more than it has learned

## What Changed

The repo now ships with a stricter local-first core:

- **Offline defaults:** no model downloads, no swarm networking, no external device calls unless you explicitly opt in
- **Embedded fallbacks:** local JSON-backed cache and vector memory replace Redis/Qdrant when those services are unavailable
- **Profession training layer:** create a domain profile, add lessons, track competency coverage, and measure readiness
- **Workspace ingestion:** point Omni at a local repo or runbook directory and let it extract lessons from SQL, YAML, Python, and docs
- **Local execution tools:** query local lessons, generate task plans, inspect profile status, and keep execution grounded in offline-safe actions
- **Desktop startup:** Electron now boots the FastAPI backend and Next frontend itself instead of assuming a Docker cluster

## Core Intent

OmniTwin is moving toward a desktop twin that a user can train into a useful role-specific collaborator. A data engineer should be able to feed it domain rules, runbooks, review preferences, failure modes, architecture heuristics, and operational lessons until the twin becomes meaningfully better at helping with that work.

This repo is not yet a fully mature profession twin for every field. What it now has is the missing scaffolding for that direction:

- training profiles
- lesson ingestion
- workspace import and repo analysis
- competency tracking
- local retrieval
- readiness evaluation
- offline packaging defaults

## Installation

### Linux / macOS

```bash
chmod +x install.sh launch.sh
./install.sh
./launch.sh
```

### Windows

```bat
install.bat
launch.bat
```

## Local Model Bundles

For strict offline inference, place bundled models under:

- `models/smollm`
- `models/minilm`

If those bundles are missing, OmniTwin falls back to deterministic offline heuristics so the application still runs and learns from local lessons.

## Training Flow

1. Create a profession profile in the desktop UI or through `/api/v1/training/profile`
2. Import a local workspace through `/api/v1/training/workspace/analyze` or `/api/v1/training/workspace/import`
3. Add manual lessons through `/api/v1/training/lesson`
4. Review readiness and competency coverage through `/api/v1/training/plan` and `/api/v1/training/evaluate`
5. Query the twin through `/api/v1/query` or `/api/v1/query/stream`

## API Highlights

- `GET /health`
- `POST /api/v1/ingest/text`
- `POST /api/v1/query`
- `POST /api/v1/query/stream`
- `GET /api/v1/state`
- `GET /api/v1/training/templates`
- `POST /api/v1/training/profile`
- `POST /api/v1/training/lesson`
- `POST /api/v1/training/workspace/analyze`
- `POST /api/v1/training/workspace/import`
- `GET /api/v1/training/plan`
- `GET /api/v1/training/evaluate`

## Current Limits

This repo still needs deeper domain tooling to become a first-rate daily operator for professions like data engineering. The biggest remaining gaps are:

- real local integrations for SQL engines, dbt commands, DAG tooling, Spark execution, and observability systems
- artifact-aware reasoning that can inspect a specific model or DAG beyond heuristic repo signals
- stronger evaluation harnesses based on live task performance
- bundled production model artifacts for high-quality local reasoning
- signed desktop release packaging

That said, the project now has a usable local training spine rather than just an aspirational architecture.
