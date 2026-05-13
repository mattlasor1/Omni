@echo off
echo Igniting OmniTwin Offline Workbench...

set OMNI_OFFLINE_STRICT=true
set OMNI_ENABLE_MODEL_DOWNLOADS=false
set OMNI_ENABLE_SWARM=false
set OMNI_ALLOW_LAN=false
set OMNI_ENABLE_EXTERNAL_DEVICES=false
set HF_HUB_OFFLINE=1
set TRANSFORMERS_OFFLINE=1
set HF_DATASETS_OFFLINE=1
set NEXT_TELEMETRY_DISABLED=1

if exist .venv\Scripts\activate (
  call .venv\Scripts\activate
)

cd electron_app
call npm start
