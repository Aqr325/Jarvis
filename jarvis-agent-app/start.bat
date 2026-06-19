@echo off
REM J.A.R.V.I.S. Agent — Quick Start
cd /d "%~dp0"
echo Starting J.A.R.V.I.S. Agent Server...
echo Open http://localhost:8000 in your browser
echo.
venv\Scripts\uvicorn server:app --host 0.0.0.0 --port 8000 --reload
pause