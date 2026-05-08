#!/bin/bash
# AI Job Copilot 本地一键启动
# 需要: conda (langchain 环境), PostgreSQL, Chroma
# PostgreSQL 和 Chroma 用 Docker 启动（轻量），Agent 和前端本地跑

set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "========== 1/4 启动基础设施 (PostgreSQL + Chroma) =========="
docker compose up -d db chroma 2>/dev/null || echo "(已运行)"

echo "========== 2/4 启动 Sub-Agent 服务 =========="
cd "$ROOT/backend"

# macOS/Linux 用 start，Windows Git Bash 不支持
if command -v start &>/dev/null && [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
  start "Profile Agent" bash -c "conda run -n langchain uvicorn app.agents.profile.server:app --host 0.0.0.0 --port 8001"
  start "Matching Agent" bash -c "conda run -n langchain uvicorn app.agents.matching.server:app --host 0.0.0.0 --port 8002"
  start "Interview Agent" bash -c "conda run -n langchain uvicorn app.agents.interview.server:app --host 0.0.0.0 --port 8003"
  start "Support Agent" bash -c "conda run -n langchain uvicorn app.agents.support.server:app --host 0.0.0.0 --port 8004"
else
  conda run -n langchain uvicorn app.agents.profile.server:app --host 0.0.0.0 --port 8001 &
  conda run -n langchain uvicorn app.agents.matching.server:app --host 0.0.0.0 --port 8002 &
  conda run -n langchain uvicorn app.agents.interview.server:app --host 0.0.0.0 --port 8003 &
  conda run -n langchain uvicorn app.agents.support.server:app --host 0.0.0.0 --port 8004 &
fi

echo "========== 3/4 启动 Supervisor =========="
sleep 2
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
  start "Supervisor" bash -c "conda run -n langchain uvicorn app.main:app --host 0.0.0.0 --port 8080"
else
  conda run -n langchain uvicorn app.main:app --host 0.0.0.0 --port 8080 &
fi

echo "========== 4/4 启动前端 =========="
cd "$ROOT/frontend"
npm run dev -- --host 0.0.0.0 --port 3000 &

echo ""
echo "========== 全部启动完成 =========="
echo "前端: http://localhost:3000"
echo "后端: http://localhost:8080"
echo "Agent Card: http://localhost:8001/.well-known/agent-card.json"
wait
