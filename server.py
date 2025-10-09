from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route, Mount

# Minimal, version-compatible construction (no description kwarg)
mcp = FastMCP("AgentICED Demo", "0.1.0")

# A tiny tool to prove tools/list + tools/call work
@mcp.tool()
def ping(message: str = "pong") -> str:
    """Echo a message back (default 'pong')."""
    return message

def health(_request):
    return JSONResponse({"ok": True, "routes": ["/mcp"]})

# Starlette app that exposes:
#   GET  /health  -> JSON ok
#   POST /mcp     -> MCP JSON-RPC endpoint
app = Starlette(
    debug=False,
    routes=[
        Route("/health", health),
        Mount("/", mcp.http_app()),  # exposes POST /mcp
    ],
)
