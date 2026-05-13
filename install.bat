@echo off
echo ========================================
echo  OmniTwin Offline Desktop Installer
echo ========================================

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python is required.
  exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Node.js/npm is required.
  exit /b 1
)

python -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

cd frontend
call npm install
call npm run build
cd ..

cd electron_app
call npm install
cd ..

echo [INFO] Installation complete.
echo [INFO] Place bundled local models under .\models for full local inference.
echo [INFO] Launch with: launch.bat
