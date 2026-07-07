"""调试 Chrome 端点 —— 连通状态 / 一键起。"""
from __future__ import annotations

import os
import subprocess
import urllib.request
from pathlib import Path

from browser_runner import config, constants
from fastapi import APIRouter

from browser_runner_api.complex.response.result import Result

router = APIRouter(prefix="/chrome", tags=["chrome"])


def _alive(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://localhost:{port}/json/version", timeout=1.2) as r:
            return b"webSocketDebuggerUrl" in r.read()
    except Exception:  # noqa: BLE001
        return False


@router.get("/status")
def status():
    port = config.debug_port()
    return Result.ok({"port": port, "alive": _alive(port)})


@router.post("/launch")
def launch():
    """跑 chrome_debug.sh 起 browser-runner 专属 profile 的调试 Chrome（显式喂解析好的 env）。"""
    script = Path(constants.__file__).parent / "chrome_debug.sh"
    env = {
        **os.environ,
        "BROWSER_RUNNER_DEBUG_PORT": str(config.debug_port()),
        "BROWSER_RUNNER_PROFILE_DIR": str(config.profile_dir()),
        "BROWSER_RUNNER_CHROME_PATH": config.chrome_path(),
    }
    try:
        p = subprocess.run(["bash", str(script)], capture_output=True, text=True, timeout=30, env=env)
        msg = ((p.stdout or "") + (p.stderr or "")).strip()
        return Result.ok({"ok": p.returncode == 0, "port": config.debug_port(), "message": msg[-800:]})
    except subprocess.TimeoutExpired:
        return Result.ok({"ok": False, "port": config.debug_port(), "message": "chrome_debug.sh 超时（30s 未就绪）"})
