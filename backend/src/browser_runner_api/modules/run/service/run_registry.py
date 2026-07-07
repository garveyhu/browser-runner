"""运行注册表 —— run_id → 子进程 / 状态 / 日志缓冲 / 多订阅者。

设计要点（见后端方案）：
- 每次运行起一个子进程（`python -m browser_runner.runexec`）：sync-playwright 完全隔离，
  可杀（取消）、可并发（多进程无 GIL），stdout 逐行当日志。
- 进程与 SSE 连接**解耦**：起跑即入表 + 后台 pump 拉子进程 stdout 广播给每个订阅者；
  订阅者断开只摘自己的队列、不动进程 → 可重连、可多看。
- 并发上限用 Semaphore；超额的 run 停在 pending 排队。
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from browser_runner import config
from loguru import logger

DONE = object()  # 广播终止哨兵
_TERMINAL = {"succeeded", "failed", "cancelled", "error"}
MAX_CONCURRENT = int(os.environ.get("BROWSER_RUNNER_MAX_CONCURRENT", "3"))
_GRACE_SECONDS = 6


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


@dataclass
class RunHandle:
    run_id: str
    flow: str
    params: dict
    workdir: Path
    dry_run: bool
    status: str = "pending"  # pending|running|succeeded|failed|cancelled|error
    started_at: str = ""
    ended_at: str | None = None
    exit_code: int | None = None
    result: dict | None = None
    proc: asyncio.subprocess.Process | None = None
    log_buffer: list[str] = field(default_factory=list)
    subscribers: set = field(default_factory=set)
    cancel_requested: bool = False

    def to_meta(self) -> dict:
        return {
            "run_id": self.run_id,
            "flow": self.flow,
            "params": self.params,
            "dry_run": self.dry_run,
            "status": self.status,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "exit_code": self.exit_code,
            "result": self.result,
        }


class RunRegistry:
    def __init__(self) -> None:
        self._runs: dict[str, RunHandle] = {}
        self._sem = asyncio.Semaphore(MAX_CONCURRENT)

    def get(self, run_id: str) -> RunHandle | None:
        return self._runs.get(run_id)

    def live(self) -> list[RunHandle]:
        return list(self._runs.values())

    def create(self, run_id: str, flow: str, params: dict, dry_run: bool, yes: bool) -> RunHandle:
        workdir = config.runs_dir() / flow / run_id
        h = RunHandle(run_id=run_id, flow=flow, params=params, workdir=workdir,
                      dry_run=dry_run, started_at=_now())
        self._runs[run_id] = h
        # 落 meta.json，供历史列表/详情读参数（子进程之外先写好）
        workdir.mkdir(parents=True, exist_ok=True)
        (workdir / "meta.json").write_text(
            json.dumps({"run_id": run_id, "flow": flow, "params": params,
                        "dry_run": dry_run, "started_at": h.started_at},
                       ensure_ascii=False, indent=2), "utf-8")
        asyncio.create_task(self._drive(h, yes))
        return h

    async def _drive(self, h: RunHandle, yes: bool) -> None:
        async with self._sem:  # 超并发上限则在此排队（status 仍是 pending）
            if h.cancel_requested:
                h.status = "cancelled"
                h.ended_at = _now()
                self._broadcast(h, DONE)
                return
            h.status = "running"
            cmd = [sys.executable, "-m", "browser_runner.runexec",
                   "--flow", h.flow, "--run-id", h.run_id,
                   "--params-json", json.dumps(h.params, ensure_ascii=False)]
            if h.dry_run:
                cmd.append("--dry-run")
            if yes:
                cmd.append("--yes")
            env = {**os.environ, "BROWSER_RUNNER_HOME": str(config.home())}
            try:
                h.proc = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
                    start_new_session=True, env=env)
            except Exception as e:  # noqa: BLE001
                logger.error("子进程起不来 {}: {}", h.run_id, e)
                h.status = "error"
                h.result = {"ok": False, "error": str(e)}
                h.ended_at = _now()
                self._broadcast(h, DONE)
                return
            await self._pump(h)

    async def _pump(self, h: RunHandle) -> None:
        assert h.proc and h.proc.stdout
        async for raw in h.proc.stdout:
            line = raw.decode("utf-8", "replace").rstrip("\n")
            if line.startswith("__RESULT__ "):
                try:
                    h.result = json.loads(line[len("__RESULT__ "):])
                except Exception:  # noqa: BLE001
                    h.result = {"ok": False, "error": "结果解析失败"}
                continue
            h.log_buffer.append(line)
            self._broadcast(h, line)
        await h.proc.wait()
        h.exit_code = h.proc.returncode
        h.ended_at = _now()
        if h.cancel_requested:
            h.status = "cancelled"
        elif h.result is not None:
            h.status = "succeeded" if h.result.get("ok") else "failed"
        else:
            h.status = "succeeded" if h.exit_code == 0 else "failed"
        self._broadcast(h, DONE)

    def _broadcast(self, h: RunHandle, item) -> None:
        for q in list(h.subscribers):
            try:
                q.put_nowait(item)
            except Exception:  # noqa: BLE001
                pass

    async def subscribe(self, h: RunHandle) -> asyncio.Queue:
        """新订阅：先灌历史日志（重放·迟到/重连也补齐），未终态则挂进广播集。

        全程无 await → asyncio 下原子，重放与挂载之间不会漏播。
        """
        q: asyncio.Queue = asyncio.Queue()
        for line in h.log_buffer:
            q.put_nowait(line)
        if h.status in _TERMINAL:
            q.put_nowait(DONE)
        else:
            h.subscribers.add(q)
        return q

    def unsubscribe(self, h: RunHandle, q: asyncio.Queue) -> None:
        h.subscribers.discard(q)

    async def cancel(self, h: RunHandle) -> None:
        h.cancel_requested = True
        if h.proc and h.proc.returncode is None:
            try:
                h.proc.terminate()
                try:
                    await asyncio.wait_for(h.proc.wait(), _GRACE_SECONDS)
                except asyncio.TimeoutError:
                    h.proc.kill()  # sync-playwright 可能吞第一个 SIGTERM
            except ProcessLookupError:
                pass


run_registry = RunRegistry()
