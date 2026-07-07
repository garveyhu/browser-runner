"""动态加载 flow.py + import shim —— 保住「flow 里 from primitives / from llm 裸导入」的作者契约。

flow.py 作者写 `from primitives import safe_fill`、`from llm import chat`（裸模块名）+ 可能
`import report`（同目录 sibling）。搬进包后真身在 browser_runner.primitives / .llm，这里注册
别名 + 把 flow 目录塞进 sys.path，让老写法零改动照跑。
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

from . import llm, primitives


def _install_shims() -> None:
    # 幂等：让 flow.py 的 `from primitives import ...` / `from llm import chat` 原样可用
    sys.modules.setdefault("primitives", primitives)
    sys.modules.setdefault("llm", llm)


def load_flow_module(flow_dir) -> ModuleType:
    _install_shims()
    flow_dir = Path(flow_dir)
    if str(flow_dir) not in sys.path:
        sys.path.insert(0, str(flow_dir))  # flow 内 sibling import（如 douyin 的 report.py）照旧
    py = flow_dir / "flow.py"
    mod_name = f"_flow_{flow_dir.name}".replace("-", "_")
    spec = importlib.util.spec_from_file_location(mod_name, py)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    if not hasattr(mod, "run"):
        raise RuntimeError(f"{py} 缺 run(page, params, ctx) 函数")
    return mod
