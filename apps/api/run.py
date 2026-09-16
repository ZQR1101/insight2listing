"""Local development server entrypoint.

On Windows, uvicorn runs its event loop on the ProactorEventLoop, which
psycopg's asyncio driver does not support. This launcher drives uvicorn on a
SelectorEventLoop instead, which is required for the database to be reachable.
Prefer this over ``uvicorn app.main:app`` on Windows:

    uv run python run.py
"""

from __future__ import annotations

import asyncio
import sys

import uvicorn

HOST = "0.0.0.0"
# 8100 (not 8000) to avoid clashing with other local projects' backends.
PORT = 8100


def main() -> None:
    config = uvicorn.Config("app.main:app", host=HOST, port=PORT, reload=False)
    server = uvicorn.Server(config)
    if sys.platform == "win32":
        # SelectorEventLoop (Proactor is unsupported by psycopg async).
        asyncio.run(server.serve(), loop_factory=asyncio.SelectorEventLoop)  # type: ignore[arg-type]
    else:
        asyncio.run(server.serve())


if __name__ == "__main__":
    main()
