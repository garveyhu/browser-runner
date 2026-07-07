"""流程清单端点。"""
from __future__ import annotations

from fastapi import APIRouter

from browser_runner_api.complex.response.result import Result
from browser_runner_api.modules.flow.service import flow_service
from browser_runner_api.modules.preset.service import preset_service

router = APIRouter(prefix="/flows", tags=["flows"])


@router.get("")
def list_flows():
    return Result.ok(flow_service.list_flows())


@router.get("/{name}")
def get_flow(name: str):
    return Result.ok(flow_service.get_flow(name))


@router.get("/{name}/last_params")
def last_params(name: str):
    return Result.ok({"flow": name, "params": preset_service.get_last_params(name)})
