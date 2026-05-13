#!/bin/bash
set -e

echo "Igniting OmniTwin Offline Workbench..."

if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

cd electron_app
npm start
