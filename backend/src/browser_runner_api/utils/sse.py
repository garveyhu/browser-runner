"""SSE 事件格式化。data 可能多行，逐行加 `data:` 前缀（SSE 规范）。"""
from __future__ import annotations

import json
from typing import Any


def sse(event: str, data: str) -> bytes:
    body = "".join(f"data: {ln}\n" for ln in data.split("\n"))
    return f"event: {event}\n{body}\n".encode("utf-8")


def sse_json(event: str, obj: Any) -> bytes:
    return sse(event, json.dumps(obj, ensure_ascii=False))
