from fastapi import FastAPI, Request, Response, Header
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional
import uuid, json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST","OPTIONS","GET"],
    allow_headers=["*"],
    expose_headers=["mcp-session-id"],
)

# in-memory sessions
SESSIONS: Dict[str, Dict[str, Any]] = {}

def j(body: Dict[str, Any]) -> str:
    # return UTF-8 JSON without escaping accents/dashes
    return json.dumps(body, ensure_ascii=False)

@app.get("/health")
def health():
    return {"ok": True}

@app.options("/mcp")
def preflight():
    # CORS preflight
    return Response(status_code=204)

@app.post("/mcp")
async def mcp(request: Request, mcp_session_id: Optional[str] = Header(default=None)):
    # robust JSON body parse with clear 400 if invalid
    try:
        payload = await request.json()
    except Exception:
        return Response(j({"jsonrpc":"2.0","id":None,
                           "error":{"code":-32700,"message":"Parse error"}}),
                        media_type="application/json", status_code=400)

    method = payload.get("method")
    rpc_id = payload.get("id")
    params = payload.get("params") or {}

    # initialize starts a new session and returns protocol/capabilities
    if method == "initialize":
        sid = uuid.uuid4().hex
        SESSIONS[sid] = {"ready": False}
        return Response(j({
            "jsonrpc":"2.0","id":rpc_id,
            "result":{"protocolVersion":"2024-11-05","capabilities":{}}
        }), media_type="application/json", headers={"mcp-session-id": sid})

    # everything else needs a valid session header
    sid = request.headers.get("mcp-session-id") or request.headers.get("x-mcp-session-id")
    if not sid or sid not in SESSIONS:
        return Response(j({"jsonrpc":"2.0","id":rpc_id,
                           "error":{"code":-32000,"message":"Invalid session"}}),
                        media_type="application/json", status_code=400)

    if method == "notifications/initialized":
        SESSIONS[sid]["ready"] = True
        return Response(status_code=204)

    if method == "tools/list":
        tools = [
            {
                "name": "ping",
                "description": "Echo a message",
                "inputSchema": {
                    "type": "object",
                    "properties": {"message": {"type": "string"}},
                    "required": ["message"]
                },
            },
            {
                "name": "get_student_profile",
                "description": "Return demo FAFSA student profile by id",
                "inputSchema": {
                    "type": "object",
                    "properties": {"student_id": {"type": "string"}},
                    "required": ["student_id"]
                },
            },
        ]
        return Response(j({"jsonrpc":"2.0","id":rpc_id,"result":{"tools": tools}}),
                        media_type="application/json")

    if method == "tools/call":
        name = (params.get("name") or "").strip()
        arguments = params.get("arguments") or {}

        if name == "ping":
            msg = arguments.get("message","")
            return Response(j({"jsonrpc":"2.0","id":rpc_id,
                               "result":{"content":[{"type":"text","text":f"pong: {msg}"}]}}),
                            media_type="application/json")

        if name == "get_student_profile":
            student_id = arguments.get("student_id")
            demo = {
                "student_en_001": {
                    "id":"student_en_001","first_name":"Ava","last_name":"Johnson","language":"en",
                    "eligible_fafsa":True,"year":"2025–26","dependency":"dependent",
                    "parent_status_2023":"divorced","contributors_expected":2,
                    "schools":["Harvard University"]
                },
                "student_es_001": {
                    "id":"student_es_001","first_name":"Mateo","last_name":"García","language":"es",
                    "eligible_fafsa":True,"year":"2025–26","dependency":"dependent",
                    "parent_status_2023":"divorciado","contributors_expected":2,
                    "schools":["Universidad de Harvard"]
                },
            }
            payload = demo.get(student_id) or {"error":"not found","student_id":student_id}
            return Response(j({"jsonrpc":"2.0","id":rpc_id,
                               "result":{
                                   "content":[{"type":"text","text":j(payload)}],
                                   "structuredContent": payload,
                                   "isError": False}}),
                            media_type="application/json")

        return Response(j({"jsonrpc":"2.0","id":rpc_id,
                           "error":{"code":-32601,"message":"Unknown tool"}}),
                        media_type="application/json")

    return Response(j({"jsonrpc":"2.0","id":rpc_id,
                       "error":{"code":-32601,"message":f"Unknown method: {method}"}}),
                    media_type="application/json")
