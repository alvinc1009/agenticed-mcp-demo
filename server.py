# server.py — minimal MCP HTTP server with health/version + ping + (optional) dummy profile

from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route, Mount

# ------------- MCP server -------------
mcp = FastMCP(name="agenticed-demo")

@mcp.tool()
def ping(message: str) -> str:
    """Echo a short message."""
    return f"pong: {message}"

@mcp.tool()
def get_student_profile(student_id: str) -> dict:
    """Return a profile from dummy_data.json (if present)."""
    import json, pathlib
    p = pathlib.Path(__file__).with_name("dummy_data.json")
    if not p.exists():
        return {"error": "dummy_data.json not found", "student_id": student_id}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        return {"error": f"bad dummy_data.json: {e}"}
    return data.get(student_id, {"error": "not found", "student_id": student_id})

# IMPORTANT: build the FastMCP ASGI app first
mcp_app = mcp.http_app()

# ------------- plain health/version -------------
def health(_):
    return JSONResponse({"ok": True})

def version(_):
    # helpful when you’re confirming what’s deployed
    return PlainTextResponse("agenticed-mcp-demo / fastmcp 2.12.1 / mcp 1.16.0")

# ------------- Starlette parent app -------------
# NOTE: Pass lifespan=mcp_app.lifespan so FastMCP can initialize its session manager
app = Starlette(
    routes=[
        Route("/health", health, methods=["GET"]),
        Route("/version", version, methods=["GET"]),
        # Mounting at "/" is what gives you POST /mcp
        Mount("/", app=mcp_app),
    ],
    lifespan=mcp_app.lifespan,
)
