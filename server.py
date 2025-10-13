# server.py
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route, Mount

# --- MCP server -------------------------------------------------------------
mcp = FastMCP(name="Agenticed Demo")

@mcp.tool()
def ping(text: str = "pong") -> str:
    """Simple echo tool to verify MCP is alive."""
    return text

# --- HTTP app (for Render health checks, etc.) ------------------------------
def health(_request):
    return JSONResponse({"ok": True, "routes": ["/mcp"]})

# Expose both /health (GET) and /mcp (POST JSON-RPC via FastMCP)
app = Starlette(
    debug=False,
    routes=[
        Route("/health", health),
        Mount("/", mcp.http_app()),  # POST /mcp stays available here
    ],
)
