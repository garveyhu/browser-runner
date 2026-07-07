"""参数预设 + 上次参数 —— 存 var/state/{presets.json, last_params.json}。"""
from __future__ import annotations

import secrets
from datetime import datetime

from browser_runner import registry

from browser_runner_api.complex.response.code import ResultCode
from browser_runner_api.complex.response.exception import CustomException
from browser_runner_api.complex.stores import preset_store

_PRESETS = "presets.json"
_LAST = "last_params.json"


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def list_presets(flow: str | None = None) -> list[dict]:
    presets = list(preset_store.load(_PRESETS, {}).values())
    if flow:
        presets = [p for p in presets if p.get("flow") == flow]
    return sorted(presets, key=lambda p: p.get("created_at", ""), reverse=True)


def create_preset(flow: str, name: str, params: dict) -> dict:
    if not registry.find_flow(flow):
        raise CustomException(ResultCode.NOT_FOUND, f"没有流程 {flow}")
    store = preset_store.load(_PRESETS, {})
    pid = "ps-" + secrets.token_hex(4)
    p = {"id": pid, "flow": flow, "name": name, "params": params,
         "created_at": _now(), "updated_at": _now()}
    store[pid] = p
    preset_store.save(_PRESETS, store)
    return p


def update_preset(pid: str, name: str | None, params: dict | None) -> dict:
    store = preset_store.load(_PRESETS, {})
    p = store.get(pid)
    if not p:
        raise CustomException(ResultCode.NOT_FOUND, "没有该预设")
    if name is not None:
        p["name"] = name
    if params is not None:
        p["params"] = params
    p["updated_at"] = _now()
    store[pid] = p
    preset_store.save(_PRESETS, store)
    return p


def delete_preset(pid: str) -> dict:
    store = preset_store.load(_PRESETS, {})
    if pid in store:
        del store[pid]
        preset_store.save(_PRESETS, store)
    return {"id": pid}


def save_last_params(flow: str, params: dict) -> None:
    store = preset_store.load(_LAST, {})
    store[flow] = params
    preset_store.save(_LAST, store)


def get_last_params(flow: str) -> dict:
    return preset_store.load(_LAST, {}).get(flow, {})
