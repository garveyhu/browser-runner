"""交给 flow.run(page, params, ctx) 的运行上下文。"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from . import config


@dataclass
class RunContext:
    params: dict
    workdir: Path
    flow: dict
    dry_run: bool = False
    log: Callable[[str], None] = field(default=lambda m: None)

    def secret(self, spec: str):
        return config.get_secret(spec)
