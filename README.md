# OmniTwin: Advanced Digital Twin Framework

OmniTwin is a framework designed to build the most advanced and comprehensive digital twin agent in the world. 
It is entirely agnostic upon initialization, capable of adapting to become a digital twin of any subject. 
Its primary directive is continuous learning, processing visual and textual data streams, extracting parameters, and mathematically integrating them into its core solid-state memory.

## Core Capabilities
* **Adaptive Learning**: Ingests new input data from any visual or textual source.
* **Mathematical Parameterization**: Extracts information signals, assigns context, and converts them into mathematical parameters.
* **Continuous Regression**: Regresses new parameters against existing ones for ultra-fast learning and adaptation without semantic bottlenecks.
* **Solid-State LLM Wiki**: A continuous, robust vector-based memory that undergoes periodic maintenance to integrate short-term cache into long-term knowledge.

## Tech Stack Overview
This system is built "for AI by AI", focusing on efficiency, elasticity, and adaptive performance:
- **FastAPI / WebSockets**: For asynchronous, high-throughput ingestion of visual streams (WebRTC, RTSP) and text.
- **Redis**: Serves as the ultra-fast livestream data cache.
- **PyTorch / NumPy**: Handles the mathematical parameterization, continuous fine-tuning, and regression of parameters.
- **Qdrant**: A high-performance vector database acting as the solid-state LLM Wiki for long-term parameterized storage.
- **Celery**: Background task queue orchestrating the nightly or post-task maintenance runs.

## Getting Started

Refer to `docs/ARCHITECTURE.md` for a deep dive into the system design.

### Running the Infrastructure
```bash
docker-compose up -d
```

### Running the API and Worker
(See documentation on setting up Python environment and starting FastAPI/Celery).
