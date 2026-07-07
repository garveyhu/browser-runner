"""产物路径 confine —— 防目录穿越（../../secrets.toml 之类）。"""
from __future__ import annotations

import os
from pathlib import Path

from browser_runner_api.complex.response.code import ResultCode
from browser_runner_api.complex.response.exception import CustomException


def confine(base: Path, rel: str) -> Path:
    """把 rel 限制在 base 目录内，返回真实文件路径；越界或不存在则抛。"""
    base_r = base.resolve()
    target = (base_r / rel).resolve()
    if target != base_r and not str(target).startswith(str(base_r) + os.sep):
        raise CustomException(ResultCode.FORBIDDEN, "非法路径")
    if not target.is_file():
        raise CustomException(ResultCode.NOT_FOUND, "产物不存在")
    return target
