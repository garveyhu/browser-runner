"""流程清单 —— registry 之上的薄封装 + 附上次参数（表单预填）。"""
from __future__ import annotations

from browser_runner import registry

from browser_runner_api.complex.response.code import ResultCode
from browser_runner_api.complex.response.exception import CustomException
from browser_runner_api.modules.preset.service import preset_service


def list_flows() -> list[dict]:
    return registry.load_flows()


def get_flow(name: str) -> dict:
    f = registry.find_flow(name)
    if not f:
        raise CustomException(ResultCode.NOT_FOUND, f"没有流程 {name}")
    f = dict(f)
    f["last_params"] = preset_service.get_last_params(name)
    return f
