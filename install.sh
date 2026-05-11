#!/bin/bash
echo "========================================"
echo " OmniTwin AGI Installer (macOS / Linux)"
echo "========================================"

# Check for Docker
if ! command -v docker &> /dev/null
then
    echo "[ERROR] Docker is not installed. OmniTwin requires Docker to orchestrate its Vector DB and Redis Cache."
    echo "Please install Docker Desktop: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check for Python
if ! command -v python3 &> /dev/null
then
    echo "[ERROR] Python 3 is not installed. Required for the OmniTwin orchestrator."
    exit 1
fi

# Check for Node.js (needed to build Electron/Next.js)
if ! command -v npm &> /dev/null
then
    echo "[ERROR] Node.js/npm is not installed. Required for the Desktop Application."
    exit 1
fi

echo "[INFO] Dependencies met. Installing Desktop Client dependencies..."
cd electron_app && npm install && cd ..

echo "[INFO] Building Docker Cluster (This may take a while as it downloads PyTorch, Rust, and HuggingFace weights)..."
docker-compose build

echo "========================================"
echo " OmniTwin Installation Complete."
echo " To launch the application, run: ./launch.sh"
echo "========================================"
