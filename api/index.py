"""Vercel entrypoint for the FastAPI application.

The application remains in ``app/main.py`` so Docker and uvicorn deployments
continue to use the same module. Vercel's Python builder detects the exported
FastAPI ``app`` and supplies the ASGI adapter itself.
"""

from app.main import app

__all__ = ["app"]
