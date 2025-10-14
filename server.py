# server.py
import json
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route, Mount
from fastmcp import FastMCP

# MCP server
mcp = FastMCP(name="agenticed-demo")

@mcp.tool()
def ping(message: str) -> str:
    """Echo a short message."""
    return f"pong: {message}"

@mcp.tool()
def get_student_profile(student_id: str) -> dict:
    """Lookup a student profile from dummy_data.json by ID."""
    with open("dummy_data.json", "r", encoding="utf-8") as f:
        db = json.load(f)
    return db.get(student_id, {"error": "not found"})

# Health/version endpoints for Render
def health(_):
    return JSONResponse({"ok": True})

def version(_):
    return PlainTextResponse("agenticed-mcp-demo / fastmcp 2.12.1 / mcp 1.12.4")

# IMPORTANT: no lifespan=... here
app = Starlette(
    routes=[
        Route("/health", health, methods=["GET"]),
        Route("/version", version, methods=["GET"]),
        # Mount FastMCP’s ASGI app; change to "/mcp" if you prefer a subpath
        Mount("/", mcp.http_app()),
    ]
)
