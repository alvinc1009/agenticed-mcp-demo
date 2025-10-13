from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route, Mount
from starlette.requests import Request

# --- Minimal MCP server with one tool ---
mcp = FastMCP(name="agenticed-mcp-demo")

@mcp.tool()
def ping(message: str = "pong") -> str:
    """Health check tool."""
    return f"pong: {message}"

# --- HTTP app: /health plus POST /mcp (JSON-RPC) ---
def health(_request: Request):
    return JSONResponse({"ok": True, "routes": ["/mcp"]})

def mcp_get(_request: Request):
    # /mcp only supports POST (JSON-RPC). 405 on GET proves route exists.
    return PlainTextResponse("Method Not Allowed", status_code=405)

app = Starlette(
    routes=[
        Route("/", lambda r: PlainTextResponse("OK. Try /health or POST /mcp"), methods=["GET"]),
        Route("/health", health, methods=["GET"]),
        Route("/mcp", mcp_get, methods=["GET"]),   # explicit 405 for GET
        Mount("/", mcp.http_app()),                # provides POST /mcp
    ]
)
