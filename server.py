# server.py — minimal MCP HTTP server with health/version + ping + dummy data
from __future__ import annotations
import json
from pathlib import Path

from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse, Response
from starlette.routing import Route, Mount

# ---- MCP instance ----
mcp = FastMCP(name="agenticed-demo")

@mcp.tool()
def ping(message: str) -> str:
    """Echo a short message."""
    return f"pong: {message}"

# Optional dummy data
DUMMY_PATH = Path(__file__).with_name("dummy_data.json")
if DUMMY_PATH.exists():
    try:
        _DUMMY = json.loads(DUMMY_PATH.read_text(encoding="utf-8"))
    except Exception:
        _DUMMY = {}
else:
    _DUMMY = {}

@mcp.tool()
def get_student_profile(student_id: str) -> dict:
    """Return a mock student profile from dummy_data.json."""
    if not _DUMMY:
        return {"error": "dummy_data.json not found on server"}
    return _DUMMY.get("students", {}).get(student_id, {"error": "student not found"})

# ---- Plain routes ----
def health(_):   return JSONResponse({"ok": True})
def version(_):  return PlainTextResponse("agenticed-mcp-demo / fastmcp 2.12.1 / mcp 1.16.0")
def mcp_get(_):  return Response("Method Not Allowed", status_code=405)  # must be 405, not 500

# ---- Mount MCP ASGI app and wire lifespan ----
mcp_asgi = mcp.http_app()

app = Starlette(
    debug=False,
    routes=[
        Route("/health", health, methods=["GET"]),
        Route("/version", version, methods=["GET"]),
        Route("/mcp", mcp_get, methods=["GET"]),  # 405 for GET checks
        Mount("/", mcp_asgi),                    # POST /mcp (JSON-RPC)
    ],
    lifespan=mcp_asgi.lifespan,                  # CRITICAL wiring for FastMCP
)
