"""Application entry point.

Run with::

    uv run uvicorn toolbridge.main:app --host 0.0.0.0 --port 8000

Or via the project script::

    uv run toolbridge
"""

from __future__ import annotations

import uvicorn

from toolbridge.server.app import app

__all__ = ["app"]


def run() -> None:
    """Start the uvicorn server (used by the ``toolbridge`` CLI script)."""
    uvicorn.run(
        "toolbridge.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
