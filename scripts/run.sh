#!/bin/bash
# 生产/本地统一启动：同步依赖 + 起后端（托管前端 build 产物）。
set -e
cd "$(dirname "$0")/.."
uv sync
[ -d frontend/dist ] || echo "（提示：前端未 build，页面暂不可用 —— cd frontend && yarn build）"
uv run browser-runner-serve
