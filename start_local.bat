@echo off
echo ========== AI Job Copilot Local Start ==========

echo 1/4 Starting infrastructure (PostgreSQL + Chroma)...
docker compose up -d db chroma

echo 2/4 Starting Sub-Agent services...
cd /d "%~dp0backend"

start "Profile Agent (8001)" cmd /c "conda run -n langchain uvicorn app.agents.profile.server:app --host 0.0.0.0 --port 8001"
start "Matching Agent (8002)" cmd /c "conda run -n langchain uvicorn app.agents.matching.server:app --host 0.0.0.0 --port 8002"
start "Interview Agent (8003)" cmd /c "conda run -n langchain uvicorn app.agents.interview.server:app --host 0.0.0.0 --port 8003"
start "Support Agent (8004)" cmd /c "conda run -n langchain uvicorn app.agents.support.server:app --host 0.0.0.0 --port 8004"

echo 3/4 Starting Supervisor...
timeout /t 3 /nobreak >nul
start "Supervisor (8080)" cmd /c "conda run -n langchain uvicorn app.main:app --host 0.0.0.0 --port 8080"

echo 4/4 Starting Frontend...
cd /d "%~dp0frontend"
start "Frontend (3000)" cmd /c "npm run dev -- --host 0.0.0.0 --port 3000"

echo.
echo ========== All services started ==========
echo Frontend: http://localhost:3000
echo Backend: http://localhost:8080
echo Agent Card: http://localhost:8001/.well-known/agent-card.json
pause