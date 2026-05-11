@echo off
echo ========================================
echo  OmniTwin AGI Installer (Windows)
echo ========================================

:: Check for Docker
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed. OmniTwin requires Docker Desktop.
    echo Please install Docker Desktop: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

:: Check for Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed. Required for the OmniTwin orchestrator.
    pause
    exit /b 1
)

:: Check for Node.js
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js/npm is not installed. Required for the Desktop Application.
    pause
    exit /b 1
)

echo [INFO] Dependencies met. Installing Desktop Client dependencies...
cd electron_app
call npm install
cd ..

echo [INFO] Building Docker Cluster (This may take a while as it downloads PyTorch, Rust, and HuggingFace weights)...
docker-compose build

echo ========================================
echo  OmniTwin Installation Complete.
echo  To launch the application, run: launch.bat
echo ========================================
pause
