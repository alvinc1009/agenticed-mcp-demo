# server.py
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route, Mount
from starlette.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware
import json
import traceback
import sys

# --- Version info endpoint helps sanity-check the environment ---
def version_info(_):
    try:
        import fastmcp, mcp, starlette, uvicorn
        info = {
            "fastmcp": getattr(fastmcp, "__version__", "unknown"),
            "mcp": getattr(mcp, "__version__", "unknown"),
            "starlette": getattr(starlette, "__version__", "unknown"),
            "uvicorn": getattr(uvicorn, "__version__", "unknown"),
            "python": sys.version,
            "routes": ["/", "/health", "/version", "POST /mcp"]
        }
        return JSONResponse(info)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# --- Minimal MCP server with a single tool so we can test tools/list & tools/call ---
mcp = FastMCP(name="agenticed-mcp-demo")

@mcp.tool()
def ping(message: str = "pong") -> str:
    """Health check tool."""
    return f"pong: {message}"

# --- Middleware to turn unexpected errors into JSON-RPC error envelopes instead of 500s ---
class JsonRpcShield(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path != "/mcp" or request.method != "POST":
            return await call_next(request)

        try:
            # read body early so we can re-use it if needed
            raw = await request.body()
            # capture for logs
            request.state.raw_body = raw
            return await call_next(request)
        except Exception as exc:
            # Last-resort JSON-RPC error wrapper so clients see *something* useful
            # Try to extract "id" if possible
            try:
                data = json.loads(getattr(request.state, "raw_body", b"") or b"{}")
                rpc_id = data.get("id")
            except Exception:
                rpc_id = None

            tb = traceback.format_exc()
            payload = {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "error": {
                    "code": -32603,  # Internal error (JSON-RPC)
                    "message": "Server internal error",
                    "data": {"traceback": tb}
                }
            }
            return JSONResponse(payload, status_code=200)

# --- GET handlers for root and /mcp (405 proves the route exists) ---
def root(_):
    return PlainTextResponse("OK. Try GET /health, GET /version, or POST /mcp (JSON-RPC)")

def health(_):
    return JSONResponse({"ok": True, "routes": ["/mcp"]})

def mcp_get(_):
    return PlainTextResponse("Method Not Allowed (POST JSON-RPC only)", status_code=405)

# --- Assemble Starlette app, mounting MCP JSON-RPC under "/" so POST /mcp works ---
app = Starlette(
    middleware=[JsonRpcShield],
    routes=[
        Route("/", root, methods=["GET"]),
        Route("/health", health, methods=["GET"]),
        Route("/version", version_info, methods=["GET"]),
        Route("/mcp", mcp_get, methods=["GET"]),  # explicit 405 on GET
        Mount("/", mcp.http_app()),               # provides POST /mcp
    ],
)
