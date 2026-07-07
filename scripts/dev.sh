#!/bin/bash
# 开发：并行起 uvicorn --reload + vite dev（前端 proxy /api → 后端）。
set -e
cd "$(dirname "$0")/.."
uv sync
uv run uvicorn browser_runner_api.app.main:app --host 127.0.0.1 --port 8760 --reload &
BACK=$!
trap "kill $BACK 2>/dev/null" EXIT
(cd frontend && yarn dev)
