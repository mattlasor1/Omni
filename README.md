# OmniTwin Offline Workbench

OmniTwin is an offline-first digital twin runtime for building a person-shaped local assistant. The current repo focuses on the foundation for a downloadable desktop application that can:

- run without Redis, Qdrant, or Docker
- stay inside local memory and local tools by default
- accept explicit training lessons and an owner profile
- answer from its own local training state rather than pretending to know more than it has learned

## What Changed

The repo now ships with a stricter local-first core:

- **Offline defaults:** no model downloads, no swarm networking, no external device calls unless you explicitly opt in
- **Runtime network guard:** strict offline mode blocks non-loopback Python socket access while keeping local backend/frontend traffic available
- **Embedded fallbacks:** local JSON-backed cache and vector memory replace Redis/Qdrant when those services are unavailable
- **Owner adaptation layer:** create an owner profile, add lessons, track competency coverage, and measure readiness
- **Continuous self-review:** record live interactions, score evaluation scenarios, generate remediation queues, and synthesize local reflection notes without leaving the machine
- **Workspace ingestion:** point Omni at local notes, projects, decisions, examples, and workflow artifacts so it can extract owner-model lessons
- **Local execution tools:** query local lessons, generate task plans, inspect profile status, and keep execution grounded in offline-safe actions
- **Desktop startup:** Electron now boots the FastAPI backend and Next frontend itself instead of assuming a Docker cluster
- **Desktop packaging:** the Windows package includes the backend source, static frontend bundle, local venv, and model directory resources

## Core Intent

OmniTwin is moving toward a desktop twin that adapts to its owner, not to a hard-coded career. The owner should be able to feed it goals, constraints, preferences, work artifacts, corrections, decision examples, vocabulary, failure modes, and daily operating lessons until the twin becomes meaningfully better at reasoning and responding like that person.

This repo is not yet a fully mature personal twin. What it now has is the missing scaffolding for that direction:

- owner profiles
- lesson ingestion
- workspace import and repo analysis
- competency tracking
- local retrieval
- readiness evaluation
- interaction logging and self-review
- remediation queue generation
- generic artifact review
- owner-model task evaluation
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

To build the Windows desktop bundle after installation:

```bat
cd electron_app
npm run pack
```

The package is written under `electron_app\release-builds\OmniTwin-win32-x64`.

## Local Model Bundles

For strict offline inference, place bundled models under:

- `models/smollm`
- `models/minilm`

If those bundles are missing, OmniTwin falls back to deterministic offline heuristics so the application still runs and learns from local lessons.

## Training Flow

1. Create an owner profile in the desktop UI or through `/api/v1/training/profile`
2. Import a local workspace through `/api/v1/training/workspace/analyze` or `/api/v1/training/workspace/import`
3. Add manual lessons through `/api/v1/training/lesson`
4. Review readiness, self-evaluation, artifact reviews, and owner-model coverage through `/api/v1/training/plan`, `/api/v1/training/evaluate`, `/api/v1/training/artifact/review`, `/api/v1/training/evals/run`, and `/api/v1/training/self-review`
5. Query the twin through `/api/v1/query` or `/api/v1/query/stream`
6. Let the local maintenance scheduler keep running `/maintenance/review` cycles in the background

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
- `GET /api/v1/training/adaptation-model`
- `POST /api/v1/training/artifact/review`
- `POST /api/v1/training/evals/run`
- `GET /api/v1/training/plan`
- `GET /api/v1/training/evaluate`
- `GET /api/v1/training/self-review`
- `POST /api/v1/training/self-review`
- `GET /api/v1/training/remediation`
- `POST /api/v1/maintenance/review`

## Current Limits

This repo still needs deeper owner-modeling to become a first-rate personal twin. The biggest remaining gaps are:

- a richer correction loop that turns user feedback into durable behavioral changes
- stronger identity/style modeling from long-running interaction history
- artifact-aware reasoning that can inspect any owner-provided file beyond generic heuristic signals
- stronger evaluation harnesses based on live task performance and owner satisfaction
- bundled production model artifacts for high-quality local reasoning
- signed desktop release packaging

That said, the project now has a usable local training spine rather than just an aspirational architecture.
