"""FastAPI app entrypoint for the MGS5 EV Dashboard backend."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import advanced, battery_usage, history, latest, refresh, settings, soh
from app.config import get_settings, resolve_database_path
from app.db.database import init_db
from app.models.schemas import ErrorResponse


def _dev_origins(frontend_port: str) -> list[str]:
    """Vite dev server origin -- defaults to its standard port (5173), but must track
    FRONTEND_PORT (see config.py) so a custom port (e.g. via `scripts/start.sh`) doesn't get
    silently blocked by CORS."""
    return [f"http://localhost:{frontend_port}", f"http://127.0.0.1:{frontend_port}"]


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    app_settings = get_settings()
    init_db(resolve_database_path(app_settings.database_path))
    yield


app = FastAPI(title="MGS5 EV Dashboard API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_dev_origins(get_settings().frontend_port),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Reshapes FastAPI's default `{"detail": [...]}` validation-error body into
    this app's `{error, detail}` contract shape (see api_contract.md's error
    handling contract) -- applies to every route, e.g. GET /api/history's
    `from`/`to`/`limit` query params, not just one endpoint's hand-written checks.
    """
    messages = []
    for error in exc.errors():
        loc = ".".join(str(part) for part in error["loc"] if part != "query")
        messages.append(f"{loc}: {error['msg']}" if loc else str(error["msg"]))
    detail = "; ".join(messages) or "Invalid request."
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(error="validation_error", detail=detail).model_dump(),
    )


app.include_router(refresh.router)
app.include_router(latest.router)
app.include_router(advanced.router)
app.include_router(battery_usage.router)
app.include_router(history.router)
app.include_router(settings.router)
app.include_router(soh.router)
