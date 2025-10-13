# server.py
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route, Mount

# Minimal MCP server
mcp = FastMCP("agenticed-mcp-demo")

@mcp.tool()
def ping(text: str) -> str:
    """Echo a string back."""
    return text

def health(_request):
    return JSONResponse({"ok": True, "routes": ["/mcp"]})

# ASGI app: /health + MCP JSON-RPC at /mcp
app = Starlette(
    debug=False,
    routes=[
        Route("/health", health),
        Mount("/", app=mcp.http_app()),  # POST /mcp
    ],
)
