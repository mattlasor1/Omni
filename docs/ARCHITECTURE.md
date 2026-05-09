# System Architecture

## Overview
The OmniTwin architecture is designed to support a non-stop cycle of data ingestion, caching, and mathematical integration. The architecture consists of three primary layers: Ingestion & Caching, Mathematical Processing (Learning), and Long-Term Storage (Solid-State LLM Wiki).

## Components

### 1. Ingestion Layer (FastAPI)
- **Protocols**: Supports REST (for batch text/data) and WebSockets/streaming protocols (for live video/visuals).
- **Function**: Receives high-volume, multi-modal input streams. Performs very lightweight pre-processing (e.g., frame extraction, text normalization) before immediately dumping the raw signals into the short-term cache.

### 2. Livestream Data Cache (Redis)
- **Function**: Acts as the temporal buffer. It constantly absorbs the livestream data so that ingestion is never bottlenecked by complex processing.
- **Data Structure**: Stores temporal sequences, frames, and text chunks with precise timestamps and context metadata.

### 3. Learning & Regression Engine (PyTorch/NumPy)
- **Function**: The core intelligence. Operates heavily on mathematical representations rather than pure semantic graphs for maximum speed.
- **Parameterization**: Converts cached input signals into high-dimensional vectors (parameters).
- **Regression**: When new parameters are generated, the engine regresses them against existing parameters retrieved from long-term storage. It updates weights, identifies correlations, and resolves statistical deviations.

### 4. Background Maintenance (Celery)
- **Function**: Orchestrates the transition from short-term cache to long-term memory. 
- **Triggers**: Runs continuously in the background, or is triggered iteratively (e.g., "nightly" or "post-task").
- **Process**: Pops data from Redis, passes it through the Learning Engine, and commits the updated parameter matrices and vectors to the Solid-State LLM Wiki.

### 5. Solid-State LLM Wiki (Qdrant Vector DB)
- **Function**: The persistent, immutable-on-read, mutable-on-maintenance storage layer.
- **Structure**: High-dimensional vector space representing the complete learned state of the Digital Twin. The agent uses this to query its state and capabilities when operating or adapting.

## Pipeline Flow Diagram

```text
[ Visual/Text Source ] 
        | (Streaming / REST)
        v
[ FastAPI Ingestion Gateway ]
        |
        v
[ Redis Livestream Cache ] --- (Continuous Background Run) ---> [ Celery Maintenance Worker ]
                                                                       |
                                                                       v
                                                           [ Math & Regression Engine ]
                                                           (PyTorch Parameterization)
                                                                       |
                                                                       v
                                                           [ Qdrant Vector Database ]
                                                           (Solid-State LLM Wiki)
```
