# server.py — minimal MCP-over-HTTP server with a tiny Consent Ledger

import json
from typing import Dict, Set, DefaultDict
from collections import defaultdict

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route

SERVER_INFO = {"name": "AgentICED Demo", "version": "0.1.0"}
PROTO = "2024-11-05"  # Agent Builder MCP protocol version

# --- Demo persistence (in-memory) ---
# guardian_id -> set(scopes)
LEDGER: DefaultDict[str, Set[str]] = defaultdict(set)

async def health(_):
    return JSONResponse({"ok": True, "routes": ["/mcp"]})

async def mcp_get(_):
    # Helpful for quick checks
    return PlainTextResponse("Method Not Allowed", status_code=405)

def _rpc_result(id_, result):
    return {"jsonrpc": "2.0", "id": id_, "result": result}

def _rpc_error(id_, code, message, data=None):
    err = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": id_, "error": err}

# ---- Tool implementations ----
def tool_consent_list(guardian_id: str):
    scopes = sorted(list(LEDGER.get(guardian_id, set())))
    return {
        "content": [
            {"type": "text", "text": json.dumps({"guardian_id": guardian_id, "scopes": scopes})}
        ]
    }

def tool_consent_grant(guardian_id: str, scope: str):
    LEDGER[guardian_id].add(scope)
    return {
        "content": [
            {"type": "text", "text": json.dumps({"ok": True, "action": "grant", "guardian_id": guardian_id, "scope": scope})}
        ]
    }

def tool_consent_revoke(guardian_id: str, scope: str):
    LEDGER[guardian_id].discard(scope)
    return {
        "content": [
            {"type": "text", "text": json.dumps({"ok": True, "action": "revoke", "guardian_id": guardian_id, "scope": scope})}
        ]
    }

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
            res = {
                "protocolVersion": PROTO,
                "serverInfo": SERVER_INFO,
                "capabilities": {"tools": {}},
            }
            return JSONResponse(_rpc_result(id_, res))

        if method == "tools/list":
            tools = [
                {
                    "name": "ping",
                    "description": "Echo a message back.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {"message": {"type": "string"}},
                        "required": [],
                        "additionalProperties": False,
                    },
                },
                {
                    "name": "consent.list",
                    "description": "List granted scopes for a guardian_id.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {"guardian_id": {"type": "string"}},
                        "required": ["guardian_id"],
                        "additionalProperties": False,
                    },
                },
                {
                    "name": "consent.grant",
                    "description": "Grant a scope for a guardian_id.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "guardian_id": {"type": "string"},
                            "scope": {"type": "string"},
                        },
                        "required": ["guardian_id", "scope"],
                        "additionalProperties": False,
                    },
                },
                {
                    "name": "consent.revoke",
                    "description": "Revoke a scope for a guardian_id.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "guardian_id": {"type": "string"},
                            "scope": {"type": "string"},
                        },
                        "required": ["guardian_id", "scope"],
                        "additionalProperties": False,
                    },
                },
            ]
            return JSONResponse(_rpc_result(id_, {"tools": tools}))

        if method == "tools/call":
            name = (params or {}).get("name")
            args = (params or {}).get("arguments") or {}

            if name == "ping":
                message = args.get("message", "pong")
                return JSONResponse(_rpc_result(id_, {"content": [{"type": "text", "text": str(message)}]}))

            if name == "consent.list":
                gid = args.get("guardian_id")
                if not gid:
                    return JSONResponse(_rpc_error(id_, -32602, "guardian_id is required"))
                return JSONResponse(_rpc_result(id_, tool_consent_list(gid)))

            if name == "consent.grant":
                gid = args.get("guardian_id")
                scope = args.get("scope")
                if not (gid and scope):
                    return JSONResponse(_rpc_error(id_, -32602, "guardian_id and scope are required"))
                return JSONResponse(_rpc_result(id_, tool_consent_grant(gid, scope)))

            if name == "consent.revoke":
                gid = args.get("guardian_id")
                scope = args.get("scope")
                if not (gid and scope):
                    return JSONResponse(_rpc_error(id_, -32602, "guardian_id and scope are required"))
                return JSONResponse(_rpc_result(id_, tool_consent_revoke(gid, scope)))

            return JSONResponse(_rpc_error(id_, -32602, f"Unknown tool: {name}"))

        return JSONResponse(_rpc_error(id_, -32601, f"Method not found: {method}"))

    except Exception as e:
        return JSONResponse(_rpc_error(id_, -32000, "Server error", str(e)))

routes = [
    Route("/health", health, methods=["GET"]),
    Route("/mcp",   mcp_get, methods=["GET"]),
    Route("/mcp",   mcp_post, methods=["POST"]),
]

app = Starlette(debug=False, routes=routes)
