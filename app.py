"""Vercel FastAPI entrypoint; the application remains implemented in backend.app.main."""

from backend.app.bootstrap import STARTED as _bootstrap_started
from backend.app.main import app

__all__ = ["app"]
