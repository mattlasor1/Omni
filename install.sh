#!/bin/bash
set -e

echo "========================================"
echo " OmniTwin Offline Desktop Installer"
echo "========================================"

if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is required."
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "[ERROR] Node.js/npm is required."
    exit 1
fi

export NEXT_TELEMETRY_DISABLED=1
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "[INFO] Building local frontend bundle..."
cd frontend
npm install
npm run build
cd ..

echo "[INFO] Installing Electron desktop wrapper..."
cd electron_app
npm install
cd ..

echo "[INFO] Installation complete."
echo "[INFO] Place bundled local models under ./models if you want full local inference."
echo "[INFO] Launch with: ./launch.sh"
