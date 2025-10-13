# server.py — minimal MCP HTTP server with health/version + ping tool
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route, Mount

# Create the MCP server
mcp = FastMCP(name="agenticed-demo")

# Example tool so tools/list and tools/call work
@mcp.tool()
def ping(message: str) -> str:
    """Echo a short message."""
    return f"pong: {message}"

# Simple health + version endpoints
def health(_):
    return JSONResponse({"ok": True, "routes": ["/mcp"]})

def version(_):
    return PlainTextResponse("agenticed-mcp-demo / fastmcp 2.12.1")

# Starlette app with /mcp mounted (JSON-RPC over HTTP POST)
app = Starlette(routes=[
    Route("/health", health, methods=["GET"]),
    Route("/version", version, methods=["GET"]),
    Mount("/", mcp.http_app()),   # <- THIS provides POST /mcp
])
