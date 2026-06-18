@echo off
chcp 65001 >nul
REM ============================================================
REM  Fund Tracker -- One-Click Launcher (Windows Command Prompt)
REM ============================================================

setlocal

set "PROJECT_DIR=%~dp0"
set "ENV_NAME=fund_tracker"

echo.
echo ========================================
echo   Fund Tracker -- Real-time NAV Estimator
echo ========================================
echo.

REM Check if conda is available
where conda >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Conda not found. Please install Anaconda or Miniconda first.
    pause
    exit /b 1
)

REM Initialize conda for the current shell
call conda activate %ENV_NAME% 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to activate conda environment: %ENV_NAME%
    echo Please create it with: conda create -n %ENV_NAME% python=3.12
    pause
    exit /b 1
)

echo [ OK ] Conda environment "%ENV_NAME%" activated
echo [ OK ] Project directory: %PROJECT_DIR%
echo.

REM Launch the application
cd /d "%PROJECT_DIR%"
python main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Application exited with code %ERRORLEVEL%
    pause
)

endlocal
