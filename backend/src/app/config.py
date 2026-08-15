"""Application configuration loaded from environment variables (backend/.env)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    saic_username: str | None
    saic_password: str | None
    saic_region: str
    database_path: str
    frontend_port: str


def get_settings() -> Settings:
    return Settings(
        saic_username=os.environ.get("SAIC_USERNAME") or None,
        saic_password=os.environ.get("SAIC_PASSWORD") or None,
        saic_region=os.environ.get("SAIC_REGION", "eu"),
        database_path=os.environ.get("DATABASE_PATH", "data/mgs5.db"),
        # Vite dev server's port -- only used to build the CORS allow-list (main.py). Not an
        # app setting so much as a "what port is the other local process on" fact; set by
        # scripts/start.sh to match whatever FRONTEND_PORT it actually started the frontend on.
        frontend_port=os.environ.get("FRONTEND_PORT", "5173"),
    )


def resolve_database_path(database_path: str) -> Path:
    """Resolve DATABASE_PATH relative to the backend/ working directory."""
    path = Path(database_path)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path
