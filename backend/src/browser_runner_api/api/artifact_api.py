"""产物端点 —— 清单 / 文件服务（report.html 沙箱 · csv 预览）。

文件服务显式豁免 Result 信封（FileResponse / 直出）。report.html 自包含、含 inline 脚本，
配 nosniff + 收紧 CSP（断 connect-src）；前端用 <iframe sandbox="allow-scripts"> 关进 opaque 源。
"""
from __future__ import annotations

import csv
from pathlib import Path

from fastapi import APIRouter, Query
from starlette.responses import FileResponse, JSONResponse

from browser_runner_api.complex.response.result import Result
from browser_runner_api.modules.run.service import history_service
from browser_runner_api.utils.paths import confine

router = APIRouter(prefix="/runs", tags=["artifacts"])

_MEDIA = {".html": "text/html", ".csv": "text/csv", ".json": "application/json",
          ".log": "text/plain; charset=utf-8", ".png": "image/png", ".txt": "text/plain; charset=utf-8"}
_REPORT_CSP = "default-src 'self' 'unsafe-inline' data: blob:; connect-src 'none'; base-uri 'none'"


@router.get("/{run_id}/artifacts")
def artifacts(run_id: str):
    wd = history_service.workdir_for(run_id)
    return Result.ok(history_service.list_artifacts(wd))


@router.get("/{run_id}/artifacts/{path:path}")
def artifact(run_id: str, path: str, download: bool = False, as_fmt: str | None = Query(None, alias="as")):
    wd = history_service.workdir_for(run_id)
    target = confine(wd, path)
    suffix = target.suffix.lower()

    # CSV → 结构化预览（限行，避免大文件撑爆前端）
    if as_fmt == "json" and suffix == ".csv":
        return JSONResponse(Result.ok(_csv_preview(target)).model_dump())

    media = _MEDIA.get(suffix, "application/octet-stream")
    disp = "attachment" if download else "inline"
    headers = {"Content-Disposition": f'{disp}; filename="{target.name}"'}
    if suffix == ".html":
        headers.update({"X-Content-Type-Options": "nosniff", "Content-Security-Policy": _REPORT_CSP})
    return FileResponse(target, media_type=media, headers=headers)


def _csv_preview(path: Path, max_rows: int = 1000) -> dict:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        return {"columns": [], "rows": [], "total": 0, "truncated": False}
    header, data = rows[0], rows[1:]
    return {"columns": header, "rows": data[:max_rows], "total": len(data),
            "truncated": len(data) > max_rows}
