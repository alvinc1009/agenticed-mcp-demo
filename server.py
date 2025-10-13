# server.py — minimal MCP HTTP server with health/version + ping tool (+ optional dummy data)
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route, Mount
import json
from pathlib import Path

# ---- MCP instance ----
mcp = FastMCP(name="agenticed-demo")

@mcp.tool()
def ping(message: str) -> str:
    """Echo a short message."""
    return f"pong: {message}"

# Optional: serve dummy student data if dummy_data.json exists
_dummy = None
data_path = Path(__file__).with_name("dummy_data.json")
if data_path.exists():
    with data_path.open("r", encoding="utf-8") as f:
        _dummy = json.load(f)

if _dummy and "students" in _dummy:
    @mcp.tool()
    def get_student_profile(student_id: str) -> dict:
        """Return test student profile from dummy_data.json by id."""
        return _dummy["students"].get(student_id, {})

# ---- Plain routes ----
def root(_):
    return PlainTextResponse("OK. Use POST /mcp for JSON-RPC. Try GET /health and /version.")

def health(_):
    return JSONResponse({"ok": True, "routes": ["/mcp"]})

def version(_):
    return PlainTextResponse("agenticed-mcp-demo / fastmcp 2.12.1 / mcp 1.16.0")

# ---- Build the ASGI app
# IMPORTANT: pass the MCP app's lifespan into Starlette
mcp_app = mcp.http_app()

app = Starlette(
    debug=False,
    routes=[
        Route("/", root, methods=["GET"]),
        Route("/health", health, methods=["GET"]),
        Route("/version", version, methods=["GET"]),
        Mount("/", mcp_app),  # provides POST /mcp
    ],
    lifespan=mcp_app.lifespan,  # <-- the crucial bit
)
