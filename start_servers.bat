@echo off
echo Starting Backend...
start "Backend Server" cmd /k "call venv\Scripts\activate && uvicorn backend.main:app --reload --port 8001"

echo Starting Frontend...
start "Frontend Server" cmd /k "cd frontend && npm install && npm run dev"

echo Servers are initializing.
echo Backend: http://localhost:8001
echo Frontend: http://localhost:5173
