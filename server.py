# server.py — minimal MCP-over-HTTP shim (Starlette + JSON-RPC 2.0)

import json
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route

SERVER_INFO = {"name": "AgentICED Demo", "version": "0.1.0"}
PROTO = "2024-11-05"  # Agent Builder speaks this

async def health(_):
    return JSONResponse({"ok": True, "routes": ["/mcp"]})

async def mcp_get(_):
    # Helpful for quick route checks
    return PlainTextResponse("Method Not Allowed", status_code=405)

def _rpc_result(id_, result):
    return {"jsonrpc": "2.0", "id": id_, "result": result}

def _rpc_error(id_, code, message, data=None):
    err = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": id_, "error": err}

async def mcp_post(request: Request):
    try:
        payload = await request.json()
    except Exception as e:
        return JSONResponse(_rpc_error(None, -32700, "Parse error", str(e)), status_code=200)

    id_ = payload.get("id")
    method = payload.get("method")
    params = payload.get("params") or {}

    try:
        if method == "initialize":
            # Minimal but valid per spec
            res = {
                "protocolVersion": PROTO,
                "serverInfo": SERVER_INFO,
                "capabilities": { "tools": {} },  # declaring tools support
            }
            return JSONResponse(_rpc_result(id_, res))

        if method == "tools/list":
            tools = [{
                "name": "ping",
                "description": "Echo a message back.",
                "inputSchema": {
                    "type": "object",
                    "properties": { "message": { "type": "string" } },
                    "required": [],
                    "additionalProperties": False
                }
            }]
            return JSONResponse(_rpc_result(id_, {"tools": tools}))

        if method == "tools/call":
            name = (params or {}).get("name")
            args = (params or {}).get("arguments") or {}
            if name != "ping":
                return JSONResponse(_rpc_error(id_, -32602, "Unknown tool"))
            message = args.get("message", "pong")
            # MCP tool result: content is a list of parts
            result = { "content": [ { "type": "text", "text": str(message) } ] }
            return JSONResponse(_rpc_result(id_, result))

        # Unknown method
        return JSONResponse(_rpc_error(id_, -32601, f"Method not found: {method}"))

    except Exception as e:
        # Surface the traceback to logs and send an RPC error
        return JSONResponse(_rpc_error(id_, -32000, "Server error", str(e)))

routes = [
    Route("/health", health, methods=["GET"]),
    Route("/mcp",   mcp_get, methods=["GET"]),
    Route("/mcp",   mcp_post, methods=["POST"]),
]

app = Starlette(debug=False, routes=routes)
