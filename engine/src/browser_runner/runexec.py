"""单次运行的执行核心 + 子进程入口。

- execute(...)：连 Chrome → 加载 flow → run → 落 result.json / run.log → 返回 result dict。
  后端子进程和 CLI 都复用它（sync playwright 只在这里跑，绝不进后端 async 事件循环）。
- main()：`python -m browser_runner.runexec` 子进程入口，逐行把日志打到 stdout（后端当 SSE log），
  末行 `__RESULT__ <json>`（后端当 done）。
"""
from __future__ import annotations

import argparse
import json
import secrets as _secrets
from datetime import datetime
from typing import Callable

from . import config, registry
from .flow_loader import load_flow_module
from .params import build_params
from .run_context import RunContext


def new_run_id() -> str:
    """<YYMMDD-HHMMSS>-<4位随机> —— 可读 + 唯一（避开同秒撞名）。"""
    return datetime.now().strftime("%y%m%d-%H%M%S") + "-" + _secrets.token_hex(2)


def execute(
    flow_name: str,
    raw_params: dict,
    run_id: str,
    dry_run: bool,
    yes: bool,
    on_log: Callable[[str], None],
) -> dict:
    flow = registry.find_flow(flow_name)
    if not flow:
        return {"ok": False, "error": f"没有流程 {flow_name}"}
    try:
        params = build_params(flow, raw_params or {})
    except ValueError as e:
        return {"ok": False, "error": str(e)}
    if flow["write_ops"] and not yes and not dry_run:
        return {"ok": False, "error": "写操作流程需放行(--yes)"}

    workdir = config.runs_dir() / flow["name"] / run_id
    workdir.mkdir(parents=True, exist_ok=True)
    logf = (workdir / "run.log").open("a", encoding="utf-8")

    def log(msg: str) -> None:
        line = f"· {msg}"
        on_log(line)
        logf.write(line + "\n")
        logf.flush()

    log(f"流程 {flow['name']} · dry_run={dry_run} · 产物 {workdir}")
    try:
        from .attach import connect, default_context, open_page
    except ImportError:
        logf.close()
        return {"ok": False, "error": "缺 playwright（uv sync 装依赖）"}
    try:
        pw, browser = connect()
    except RuntimeError as e:
        log(f"失败 ❌ {e}")
        logf.close()
        return {"ok": False, "error": str(e)}

    ctx = RunContext(params=params, workdir=workdir, flow=flow, dry_run=dry_run, log=log)
    result: dict = {"ok": False}
    try:
        page = open_page(default_context(browser), flow.get("landing_url") or "")
        mod = load_flow_module(flow["dir"])
        out = mod.run(page, params, ctx) or {}
        result = {"ok": True, **(out if isinstance(out, dict) else {"result": out})}
        log("完成 ✅")
    except Exception as e:  # noqa: BLE001 — 单个流程失败不带崩进程
        result = {"ok": False, "error": str(e)}
        log(f"失败 ❌ {e}")
    finally:
        browser.close()  # 只断 CDP，不关你的 Chrome
        pw.stop()
        logf.close()

    (workdir / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), "utf-8")
    return result


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="browser_runner.runexec")
    ap.add_argument("--flow", required=True)
    ap.add_argument("--params-json", default="{}")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--yes", action="store_true")
    a = ap.parse_args(argv)
    raw = json.loads(a.params_json or "{}")
    result = execute(a.flow, raw, a.run_id, a.dry_run, a.yes, lambda line: print(line, flush=True))
    print("__RESULT__ " + json.dumps(result, ensure_ascii=False), flush=True)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
