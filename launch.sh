#!/bin/bash
set -e

echo "Igniting OmniTwin Offline Workbench..."

export OMNI_OFFLINE_STRICT=true
export OMNI_ENABLE_MODEL_DOWNLOADS=false
export OMNI_ENABLE_SWARM=false
export OMNI_ALLOW_LAN=false
export OMNI_ENABLE_EXTERNAL_DEVICES=false
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export NEXT_TELEMETRY_DISABLED=1

if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

cd electron_app
npm start
