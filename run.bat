@echo off
REM ============================================================
REM  Market Basket Analysis - one-click launcher
REM  Double-click this file to run the web app.
REM  First run installs dependencies and runs the analysis.
REM ============================================================
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo Python is not installed. Install it from https://www.python.org/downloads/
    echo Make sure to tick "Add Python to PATH" during installation.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv .venv
)

echo Installing dependencies...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt --quiet

if not exist "outputs\results\association_rules.csv" (
    echo Running the analysis pipeline (one-time)...
    ".venv\Scripts\python.exe" main.py
)

echo.
echo Starting the web app...
echo Open http://127.0.0.1:5000 in your browser
echo Press Ctrl+C to stop it.
echo.
".venv\Scripts\python.exe" app\app.py

pause
