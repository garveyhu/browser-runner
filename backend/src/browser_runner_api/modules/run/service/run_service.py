"""起跑 / 取消 —— 编排 registry + 校验 + 记住上次参数。"""
from __future__ import annotations

from browser_runner import registry
from browser_runner.runexec import new_run_id

from browser_runner_api.complex.response.code import ResultCode
from browser_runner_api.complex.response.exception import CustomException
from browser_runner_api.modules.preset.service import preset_service
from browser_runner_api.modules.run.service.run_registry import run_registry


def start_run(flow_name: str, params: dict, dry_run: bool, yes: bool) -> dict:
    flow = registry.find_flow(flow_name)
    if not flow:
        raise CustomException(ResultCode.NOT_FOUND, f"没有流程 {flow_name}")
    # 写操作流程：非 dry-run 且未放行 → 拒（尽早失败，给前端明确 code）
    if flow["write_ops"] and not yes and not dry_run:
        raise CustomException(ResultCode.FORBIDDEN, "写操作流程需放行（勾确认后再跑）")
    run_id = new_run_id()
    preset_service.save_last_params(flow_name, params)  # 记住这次参数，下次预填
    h = run_registry.create(run_id, flow_name, params, dry_run, yes)
    return {"run_id": run_id, "status": h.status}


async def cancel_run(run_id: str) -> dict:
    h = run_registry.get(run_id)
    if not h:
        raise CustomException(ResultCode.NOT_FOUND, "没有该运行（可能已结束、不在内存）")
    await run_registry.cancel(h)
    return {"run_id": run_id, "status": "cancelled"}
