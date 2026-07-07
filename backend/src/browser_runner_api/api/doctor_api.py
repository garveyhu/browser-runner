"""体检端点 —— 连通 / 密钥 / 引擎 / 并发上限。"""
from __future__ import annotations

import urllib.request

from browser_runner import config, registry
from fastapi import APIRouter

from browser_runner_api.complex.response.result import Result
from browser_runner_api.modules.run.service.run_registry import MAX_CONCURRENT

router = APIRouter(tags=["doctor"])


def _alive(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://localhost:{port}/json/version", timeout=1.2) as r:
            return b"webSocketDebuggerUrl" in r.read()
    except Exception:  # noqa: BLE001
        return False


@router.get("/doctor")
def doctor():
    flows = registry.load_flows()
    missing = sorted({s for f in flows for s in f["needs"] if not config.has_secret(s)})
    try:
        import playwright  # noqa: F401

        engine_ok = True
    except ImportError:
        engine_ok = False
    port = config.debug_port()
    return Result.ok({
        "port": port,
        "flows": len(flows),
        "missing_secrets": missing,
        "chrome_alive": _alive(port),
        "engine_ok": engine_ok,
        "max_concurrent": MAX_CONCURRENT,
    })
