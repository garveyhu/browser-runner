"""参数预设 CRUD。"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from browser_runner_api.complex.response.result import Result
from browser_runner_api.modules.preset.service import preset_service

router = APIRouter(prefix="/presets", tags=["presets"])


class PresetCreate(BaseModel):
    flow: str
    name: str
    params: dict = {}


class PresetUpdate(BaseModel):
    name: str | None = None
    params: dict | None = None


@router.get("")
def list_presets(flow: str | None = None):
    return Result.ok(preset_service.list_presets(flow))


@router.post("/create")
def create(req: PresetCreate):
    return Result.ok(preset_service.create_preset(req.flow, req.name, req.params))


@router.post("/{pid}/update")
def update(pid: str, req: PresetUpdate):
    return Result.ok(preset_service.update_preset(pid, req.name, req.params))


@router.post("/{pid}/delete")
def delete(pid: str):
    return Result.ok(preset_service.delete_preset(pid))
