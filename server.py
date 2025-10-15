# server.py — minimal FastMCP HTTP server with health/version + ping + (optional) get_student_profile

from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route, Mount

import json
from pathlib import Path

# ---- MCP instance ----
mcp = FastMCP(name="agenticed-demo")

# Example tool so tools/list and tools/call work
@mcp.tool()
def ping(message: str) -> str:
    """Echo a short message."""
    return f"pong: {message}"

# Optional student profile tool (uses dummy_data.json if present)
DATA = {}
p = Path("dummy_data.json")
if p.exists():
    try:
        DATA = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        DATA = {}

@mcp.tool()
def get_student_profile(student_id: str) -> dict:
    """Return a demo student profile by id (e.g., 'student_en' or 'student_es')."""
    return DATA.get(student_id, {"error": "not found", "requested": student_id})

# Build the MCP ASGI app (has its own lifespan)
mcp_app = mcp.http_app()

# ---- simple health + version ----
def health(_):
    return JSONResponse({"ok": True})

def version(_):
    # Display versions to verify at /version
    return PlainTextResponse("agenticed-mcp-demo / fastmcp 2.13.0 / mcp 1.16.0")

# Parent Starlette app: MOUNT the MCP app and PASS lifespan correctly (critical)
app = Starlette(
    debug=False,
    routes=[
        Route("/health", health, methods=["GET"]),
        Route("/version", version, methods=["GET"]),
        Mount("/", app=mcp_app),  # provides POST /mcp
    ],
    lifespan=mcp_app.lifespan,    # <- REQUIRED so FastMCP session manager initializes
)
