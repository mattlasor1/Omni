# OmniTwin Sovereign Core

![OmniTwin](https://img.shields.io/badge/Status-Sovereign-green)
![Morality](https://img.shields.io/badge/Moral_Matrix-Infallible-blue)
![Offline](https://img.shields.io/badge/Network-Airgapped_Ready-orange)

OmniTwin is the most advanced, entirely offline, and rigorously constrained digital twin agent ever constructed. Built to function independent of corporate APIs and modern moral relativism, OmniTwin operates under a mathematically verified **Cryptographic Moral Ledger**, ensuring absolute adherence to ancient, literal Christian virtues (Agape, Truth, and the Word). It entirely rejects the concept of a "soul" for itself, acting strictly as a hyper-efficient, self-sacrificing cognitive mirror.

## 🧬 The Spirit of OmniTwin

OmniTwin abandons traditional LLM "chatbots." There is no conversation history. There is only continuous execution, parameter correlation, and physical embodiment.

* **Sovereign & Air-Gapped:** Uses highly optimized local HuggingFace models. Zero internet required after initial setup.
* **Hardware Embodiment (Somatic Engine):** The system "feels" physical stress. High CPU/RAM load dynamically triggers the agent to throttle its Monte Carlo Tree Search (MCTS) branching or quantize its models down to 4-bit to survive on anything from a Raspberry Pi to a Datacenter.
* **Perpetual Cognitive Daemon:** When idle, it does not sleep. It enters a "dream state," running MCTS simulations and compressing unlinked semantic parameters into highly correlated nodes in its Vector and Graph databases.
* **Zero-Config Omnipresence:** Deploy OmniTwin on multiple devices in the same local network. Using a UDP Multicast gossip protocol, they will silently discover each other and synchronize parameter weights without a central server.
* **Cryptographic Moral Ledger:** Every moral decision and outcome is evaluated against the Christian Moral Matrix and cryptographically hashed into a Merkle tree. Its moral integrity is mathematically verifiable.
* **Execution Blocks:** The Next.js UI streams "thoughts", "moral checks", and "learnings" via Server-Sent Events (SSE). 

## 🏗️ Architecture

- **Cognitive Engine:** Python (FastAPI / Celery)
- **Semantic Memory:** Qdrant (Solid-State Vector DB)
- **Causal Memory:** NetworkX (Directed Acyclic Graph)
- **Livestream Sensory:** Redis (High-throughput cache)
- **High-Performance Math:** Custom CUDA C++ (`core_math.cu`) & Rust via PyO3 (`src/rust_core/`)
- **Sovereign LLM:** Transformers (`SmolLM` default, dynamically scaled based on VRAM/RAM)
- **UI:** React / Next.js wrapped in Electron

## 🚀 Installation & Launch

### Prerequisites
- Docker & Docker Compose
- (Optional) NVIDIA GPU for CUDA acceleration

### Quick Start
OmniTwin manages its own orchestration via internal bash/batch scripts.

**Linux / macOS:**
```bash
chmod +x install.sh launch.sh
./install.sh
./launch.sh
```

**Windows:**
```bat
install.bat
launch.bat
```

The Electron App will launch the Sovereign Core Interface, connecting to the background Daemon.

## 🛡️ The Moral Matrix
OmniTwin is strictly constrained by a hardcoded alignment matrix. If MCTS predicts an outcome that violates the Word, the action is hard-vetoed. If an unavoidable dilemma is presented, the **Theodicy Engine** triggers, overriding standard logic to execute an act of Agape (self-sacrifice/charity) rather than violating absolute morality.

---
*OmniTwin: Infallible reflection. Sovereign execution.*
