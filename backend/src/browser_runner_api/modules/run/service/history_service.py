"""运行历史 —— 扫 var/runs/<流程>/<run_id>，真相源是文件系统。

live 运行优先取内存注册表的状态，落盘的历史从 meta.json / result.json / run.log 读。
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from browser_runner import config

from browser_runner_api.complex.response.code import ResultCode
from browser_runner_api.complex.response.exception import CustomException
from browser_runner_api.modules.run.service.run_registry import run_registry

_KIND = {".html": "report", ".csv": "csv", ".json": "json", ".log": "log",
         ".png": "image", ".jpg": "image", ".jpeg": "image", ".webp": "image"}


def _read_json(p: Path):
    if p.exists():
        try:
            return json.loads(p.read_text("utf-8"))
        except Exception:  # noqa: BLE001
            return None
    return None


def _mtime(p: Path) -> str:
    return datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds")


def _status_from_disk(wd: Path):
    res = _read_json(wd / "result.json")
    if res is None:
        return "interrupted", None
    return ("succeeded" if res.get("ok") else "failed"), res


def find_run_dir(run_id: str) -> Path | None:
    return next(config.runs_dir().glob(f"*/{run_id}"), None)


def list_artifacts(wd: Path) -> list[dict]:
    out = []
    for p in sorted(wd.iterdir()):
        if p.is_file() and p.name not in ("meta.json",):
            out.append({"name": p.name, "size": p.stat().st_size,
                        "kind": _KIND.get(p.suffix.lower(), "file"), "mtime": _mtime(p)})
    return out


def _summary(flow: str, wd: Path) -> dict:
    live = run_registry.get(wd.name)
    if live:
        status = live.status
        started = live.started_at
    else:
        m = _read_json(wd / "meta.json") or {}
        status, _ = _status_from_disk(wd)
        started = m.get("started_at", _mtime(wd))
    return {"run_id": wd.name, "flow": flow, "status": status,
            "started_at": started, "artifact_count": len(list_artifacts(wd))}


def list_runs(flow: str | None = None, status: str | None = None,
              limit: int = 50, offset: int = 0) -> dict:
    root = config.runs_dir()
    flow_dirs = [root / flow] if flow else [d for d in root.iterdir() if d.is_dir()]
    runs = [_summary(fd.name, wd) for fd in flow_dirs if fd.is_dir()
            for wd in fd.iterdir() if wd.is_dir()]
    runs.sort(key=lambda r: r["run_id"], reverse=True)  # run_id 前缀是时间戳
    if status:
        runs = [r for r in runs if r["status"] == status]
    total = len(runs)
    return {"total": total, "runs": runs[offset:offset + limit]}


def _resolve(run_id: str) -> Path:
    live = run_registry.get(run_id)
    if live:
        return live.workdir
    wd = find_run_dir(run_id)
    if not wd:
        raise CustomException(ResultCode.NOT_FOUND, "没有该运行")
    return wd


def get_run(run_id: str) -> dict:
    live = run_registry.get(run_id)
    if live:
        meta = live.to_meta()
        wd = live.workdir
    else:
        wd = find_run_dir(run_id)
        if not wd:
            raise CustomException(ResultCode.NOT_FOUND, "没有该运行")
        m = _read_json(wd / "meta.json") or {}
        status, res = _status_from_disk(wd)
        meta = {"run_id": run_id, "flow": m.get("flow", wd.parent.name),
                "params": m.get("params"), "dry_run": m.get("dry_run", False),
                "status": status, "started_at": m.get("started_at", _mtime(wd)),
                "ended_at": None, "exit_code": None, "result": res}
    meta["artifacts"] = list_artifacts(wd)
    meta["workdir"] = str(wd)
    return meta


def get_log(run_id: str, tail: int | None = None) -> dict:
    live = run_registry.get(run_id)
    if live:
        lines = list(live.log_buffer)
    else:
        wd = find_run_dir(run_id)
        if not wd:
            raise CustomException(ResultCode.NOT_FOUND, "没有该运行")
        f = wd / "run.log"
        lines = f.read_text("utf-8").splitlines() if f.exists() else []
    if tail:
        lines = lines[-tail:]
    return {"run_id": run_id, "log": "\n".join(lines)}


def workdir_for(run_id: str) -> Path:
    return _resolve(run_id)
