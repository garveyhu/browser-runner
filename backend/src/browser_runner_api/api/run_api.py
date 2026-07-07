"""运行端点 —— 起跑 / SSE 订阅 / 取消 / 历史列表 / 详情 / 日志。

起跑立即返回 run_id（不阻塞）；SSE 订阅可重连/多看、断开不杀进程；取消杀 PID。
SSE 端点显式豁免 Result 信封（text/event-stream）。
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from browser_runner_api.complex.response.code import ResultCode
from browser_runner_api.complex.response.exception import CustomException
from browser_runner_api.complex.response.result import Result
from browser_runner_api.modules.run.service import history_service, run_service
from browser_runner_api.modules.run.service.run_registry import DONE, run_registry
from browser_runner_api.utils.sse import sse, sse_json

router = APIRouter(prefix="/runs", tags=["runs"])


class RunStartRequest(BaseModel):
    flow: str
    params: dict = {}
    dry_run: bool = False
    yes: bool = False


@router.post("")
async def start(req: RunStartRequest):
    # async 端点：run_registry.create 内部 asyncio.create_task 需要运行中的事件循环
    return Result.ok(run_service.start_run(req.flow, req.params, req.dry_run, req.yes))


@router.get("/{run_id}/events")
async def events(run_id: str):
    h = run_registry.get(run_id)
    if not h:
        raise CustomException(ResultCode.NOT_FOUND, "没有该 live 运行（历史运行看 /log）")

    async def gen():
        q = await run_registry.subscribe(h)
        try:
            while True:
                item = await q.get()
                if item is DONE:
                    yield sse_json("done", h.result or {"ok": h.status == "succeeded"})
                    return
                yield sse("log", item)
        finally:
            run_registry.unsubscribe(h, q)

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )


@router.post("/{run_id}/cancel")
async def cancel(run_id: str):
    return Result.ok(await run_service.cancel_run(run_id))


@router.get("")
def list_runs(flow: str | None = None, status: str | None = None, limit: int = 50, offset: int = 0):
    return Result.ok(history_service.list_runs(flow, status, limit, offset))


@router.get("/{run_id}")
def get_run(run_id: str):
    return Result.ok(history_service.get_run(run_id))


@router.get("/{run_id}/log")
def get_log(run_id: str, tail: int | None = None):
    return Result.ok(history_service.get_log(run_id, tail))
