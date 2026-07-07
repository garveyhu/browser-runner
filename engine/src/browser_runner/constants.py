"""路径锚点 —— 仓库根、运行时 home、流程目录。

engine/src/browser_runner/constants.py → parents[3] = 仓库根。
运行时 home 默认落项目内 var/（整目录 gitignore），可用 BROWSER_RUNNER_HOME 覆盖
（后端起子进程、CLI、测试都靠它把三处指向同一个 var/）。
"""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
VAR_PATH = Path(os.environ.get("BROWSER_RUNNER_HOME", REPO_ROOT / "var")).expanduser()
FLOWS_PATH = REPO_ROOT / "flows"  # 项目自带流程（tracked）
