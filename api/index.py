"""
Vercel serverless entrypoint.

Vercel's legacy Python runtime auto-installs ``requirements.txt`` only when the
function entrypoint lives under an ``api/`` directory. The application itself
sits in ``app/main.py``; this module is the thin shim Vercel invokes per
request, re-exporting the existing ``app`` instance so the same FastAPI app
runs unchanged in both the container (uvicorn) and serverless (Vercel)
deployments.
"""

from app.main import app  # noqa: F401  (Vercel looks for the top-level `app`)