# server.py — minimal MCP HTTP server with health/version + two tools
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route, Mount
import json
from pathlib import Path

# ---- MCP server with tools ----
mcp = FastMCP(name="agenticed-demo")

# Simple echo to prove tools/list + tools/call works
@mcp.tool()
def ping(message: str) -> str:
    """Echo a short message."""
    return f"pong: {message}"

# Dummy data reader (for your agents)
DUMMY_PATH = Path(__file__).with_name("dummy_data.json")

@mcp.tool()
def get_student_profile(student_id: str) -> dict:
    """Return a dummy student profile by id."""
    data = json.loads(DUMMY_PATH.read_text())
    if student_id not in data:
        return {"ok": False, "error": f"student_id '{student_id}' not found"}
    return {"ok": True, "student": data[student_id]}

# ---- health + version (for Render and quick checks) ----
def health(_):
    return JSONResponse({"ok": True})

def version(_):
    return PlainTextResponse("agenticed-mcp-demo / ok")

# Starlette app with /mcp mounted (JSON-RPC over HTTP POST)
app = Starlette(routes=[
    Route("/health", health, methods=["GET"]),
    Route("/version", version, methods=["GET"]),
    Mount("/", mcp.http_app()),   # provides POST /mcp
])
