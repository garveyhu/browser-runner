"""JSON 状态存储（var/state/*.json）—— 原子写（临时文件 + os.replace）+ 锁串行化。

预设量小、单用户、可人读，无需 DB。抽象在此，日后要换 sqlite 只改本文件。
"""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

from browser_runner import config

_lock = threading.Lock()


def _state_dir() -> Path:
    d = config.home() / "state"
    d.mkdir(parents=True, exist_ok=True)
    return d


def load(name: str, default: Any) -> Any:
    f = _state_dir() / name
    if f.exists():
        try:
            return json.loads(f.read_text("utf-8"))
        except Exception:  # noqa: BLE001
            return default
    return default


def save(name: str, data: Any) -> None:
    with _lock:
        f = _state_dir() / name
        tmp = f.with_suffix(f.suffix + ".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
        os.replace(tmp, f)
