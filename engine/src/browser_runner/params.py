"""参数强转 + 校验 —— 吃 flow.toml 的 params schema。"""
from __future__ import annotations

from typing import Any


def _coerce(value: Any, typ: str):
    if value is None:
        return None
    if typ == "int":
        return int(value)
    if typ == "float":
        return float(value)
    if typ == "bool":
        return value in (True, "true", "1", "yes", "on") if isinstance(value, str) else bool(value)
    return str(value)


def build_params(flow: dict, raw: dict) -> dict:
    """按 params schema 校验 + 填默认 + 强转类型。缺必填则抛 ValueError。"""
    out: dict = {}
    for p in flow["params"]:
        key, typ = p["key"], p["type"]
        if key in raw and raw[key] not in (None, ""):
            out[key] = _coerce(raw[key], typ)
        elif p.get("default") is not None:
            out[key] = _coerce(p["default"], typ)
        elif p.get("required"):
            raise ValueError(f"缺必填参数：{key}（{p.get('label', key)}）")
        else:
            out[key] = None
    return out
