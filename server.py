# Minimal, session-capable MCP HTTP server with health/version + two tools
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route, Mount
import json

mcp = FastMCP(name="agenticed-demo")

@mcp.tool()
def ping(message: str) -> str:
    """Echo a short message."""
    return f"pong: {message}"

# optional dummy data tool
@mcp.tool()
def get_student_profile(student_id: str) -> dict:
    """Return a demo profile by ID from dummy_data.json."""
    try:
        with open("dummy_data.json", "r", encoding="utf-8") as f:
            db = json.load(f)
        return db.get(student_id, {"error": "not_found"})
    except Exception as e:
        return {"error": str(e)}

def health(_):
    return JSONResponse({"ok": True})

def version(_):
    return PlainTextResponse("agenticed-mcp-demo / fastmcp 2.12.1 / mcp 1.16.0")

# IMPORTANT: pass lifespan=mcp.http_app().lifespan
app = Starlette(
    debug=False,
    routes=[
        Route("/health", health, methods=["GET"]),
        Route("/version", version, methods=["GET"]),
        Mount("/", mcp.http_app()),
    ],
    lifespan=mcp.http_app().lifespan,
)
