"""FastAPI app 组装：日志 + lifespan + CORS + 全局异常 handler + 动态路由注册 + 前端托管。

无鉴权、无 DB —— 本机单用户工具，只绑 127.0.0.1。
所有端点在 api/ 下（自动扫描注册·加端点不改本文件），统一挂 /api 前缀。
"""
from __future__ import annotations

import importlib
import os
import pkgutil
import sys
from contextlib import asynccontextmanager

from browser_runner import constants
from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import FileResponse, JSONResponse

from browser_runner_api.complex.response.code import ResultCode
from browser_runner_api.complex.response.exception import CustomException
from browser_runner_api.complex.response.result import Result

LOG_LEVEL = os.environ.get("BROWSER_RUNNER_LOG_LEVEL", "INFO")
logger.remove()
logger.add(
    sys.stderr,
    level=LOG_LEVEL,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <7}</level> | "
    "<cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    (constants.VAR_PATH / "runs").mkdir(parents=True, exist_ok=True)
    (constants.VAR_PATH / "state").mkdir(parents=True, exist_ok=True)
    logger.info("browser-runner 后端启动 · home={}", constants.VAR_PATH)
    yield
    logger.info("browser-runner 后端停止")


def create_app() -> FastAPI:
    app = FastAPI(title="browser-runner", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.exception_handler(CustomException)
    async def _biz(request: Request, exc: CustomException):
        return JSONResponse(
            status_code=exc.result_code.code,
            content=Result(success=False, code=exc.result_code.code, message=exc.message).model_dump(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_exc(request: Request, exc: StarletteHTTPException):
        # SPA 深链兜底：非 /api 的 404 → index.html（生产托管前端时前端路由才不 404）
        if exc.status_code == 404 and not request.url.path.startswith("/api"):
            index = constants.REPO_ROOT / "frontend" / "dist" / "index.html"
            if index.is_file():
                return FileResponse(str(index))
        return JSONResponse(
            status_code=exc.status_code,
            content=Result(success=False, code=exc.status_code, message=exc.detail or "未找到").model_dump(),
        )

    @app.exception_handler(Exception)
    async def _all(request: Request, exc: Exception):
        logger.exception(exc)
        return JSONResponse(
            status_code=500,
            content=Result(
                success=False, code=ResultCode.SYSTEM_INNER_ERROR.code, message=str(exc)
            ).model_dump(),
        )

    _register_routers(app)
    _mount_frontend(app)
    return app


def _register_routers(app: FastAPI) -> None:
    """自动扫描 browser_runner_api.api 下所有 APIRouter 并注册（加端点不改本文件）。"""
    import browser_runner_api.api as api_pkg

    for _, name, _ in pkgutil.walk_packages(api_pkg.__path__, api_pkg.__name__ + "."):
        try:
            mod = importlib.import_module(name)
            for attr in dir(mod):
                obj = getattr(mod, attr)
                if isinstance(obj, APIRouter):
                    app.include_router(obj, prefix="/api")
                    logger.info("注册路由：{}", name)
        except Exception as e:  # noqa: BLE001
            logger.error("路由注册失败 {}: {}", name, e)


def _mount_frontend(app: FastAPI) -> None:
    """生产：托管 vite build 产物（frontend/dist）。dev 走 vite dev，不 mount。"""
    dist = constants.REPO_ROOT / "frontend" / "dist"
    if dist.is_dir():
        from fastapi.staticfiles import StaticFiles

        app.mount("/", StaticFiles(directory=str(dist), html=True), name="frontend")
        logger.info("托管前端：{}", dist)


app = create_app()


def serve() -> None:
    import uvicorn

    port = int(os.environ.get("BROWSER_RUNNER_PORT", "8760"))
    uvicorn.run("browser_runner_api.app.main:app", host="127.0.0.1", port=port)
