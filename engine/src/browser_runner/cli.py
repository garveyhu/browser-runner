"""browser-runner CLI —— 本机随时用。

  browser-runner list                  列出所有流程
  browser-runner run <flow> -p k=v ...  跑一个流程（--dry-run 只连不动作 / --yes 放行写操作）
  browser-runner run <flow> --params-json '{...}'
  browser-runner doctor                体检：浏览器连通 + 密钥齐不齐

看板/后端另起（scripts/run.sh），CLI 不含 serve（engine 不依赖 backend）。
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request

from . import config, registry
from .runexec import execute, new_run_id


def cmd_list(_a) -> int:
    flows = registry.load_flows()
    if not flows:
        print("（还没有流程。cp -r flows/_template flows/<name> 开一个。）")
        return 0
    group = None
    for f in flows:
        if f["group"] != group:
            group = f["group"]
            print(f"\n【{group}】")
        tag = " ✍️写" if f["write_ops"] else ""
        src = "" if f["source"] == "builtin" else " ·私有"
        print(f"  {f['name']}{tag}{src} — {f['description']}")
    print()
    return 0


def cmd_run(a) -> int:
    flow = registry.find_flow(a.flow)
    if not flow:
        sys.stderr.write(f"❌ 没有流程 `{a.flow}`（`browser-runner list` 看有哪些）\n")
        return 2
    raw = json.loads(a.params_json) if a.params_json else {}
    for kv in a.p or []:
        k, _, v = kv.partition("=")
        raw[k] = v
    if flow["write_ops"] and not a.yes and not a.dry_run:
        sys.stderr.write("⚠️ 写操作流程需 --yes 放行。流程仍会停在提交前。\n")
        return 3
    result = execute(a.flow, raw, new_run_id(), a.dry_run, a.yes, lambda line: print(line, flush=True))
    print("\n结果：" + json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


def _port_alive(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://localhost:{port}/json/version", timeout=1.5) as r:
            return b"webSocketDebuggerUrl" in r.read()
    except Exception:  # noqa: BLE001
        return False


def cmd_doctor(_a) -> int:
    ok = True
    print("browser-runner doctor")
    try:
        import playwright  # noqa: F401

        print("  ✅ playwright 已装")
    except ImportError:
        print("  ❌ playwright 未装（uv sync）")
        ok = False
    port = config.debug_port()
    alive = _port_alive(port)
    print(f"  {'✅' if alive else '⚠️'} Chrome 调试端口 {port} " + ("通" if alive else "不通（起调试 Chrome 后重试）"))
    flows = registry.load_flows()
    print(f"  · 流程 {len(flows)} 个")
    missing = sorted({s for f in flows for s in f["needs"] if not config.has_secret(s)})
    print(f"  · secrets 缺：{', '.join(missing)}" if missing else "  ✅ 各流程所需密钥齐（或无需）")
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="browser-runner", description="沉淀 & 复放浏览器自动化流程")
    sub = ap.add_subparsers(dest="cmd", required=False)
    sub.add_parser("list", help="列出所有流程").set_defaults(func=cmd_list)
    pr = sub.add_parser("run", help="跑一个流程")
    pr.add_argument("flow")
    pr.add_argument("-p", action="append", metavar="key=value", help="参数（可多次）")
    pr.add_argument("--params-json", help="参数 JSON")
    pr.add_argument("--dry-run", action="store_true", help="只连+导航+定位，不动作")
    pr.add_argument("--yes", action="store_true", help="放行写操作流程")
    pr.set_defaults(func=cmd_run)
    sub.add_parser("doctor", help="体检依赖/连通/密钥").set_defaults(func=cmd_doctor)
    a = ap.parse_args(argv)
    if not getattr(a, "func", None):
        ap.print_help()
        return 0
    return a.func(a)


if __name__ == "__main__":
    raise SystemExit(main())
