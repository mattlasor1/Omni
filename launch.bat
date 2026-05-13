@echo off
echo Igniting OmniTwin Offline Workbench...

if exist .venv\Scripts\activate (
  call .venv\Scripts\activate
)

cd electron_app
call npm start
