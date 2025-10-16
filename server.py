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

SESSIONS: Dict[str, Dict[str, Any]] = {}

@app.get("/health")
def health():
    return {"ok": True}

def ok(resp_obj: Dict[str, Any], session_id: Optional[str] = None, status: int = 200):
    body = json.dumps(resp_obj, ensure_ascii=False)
    headers = {}
    if session_id:
        headers["mcp-session-id"] = session_id
    return Response(content=body, media_type="application/json", headers=headers, status_code=status)

@app.options("/mcp")
def preflight():
    return Response(status_code=204)

@app.post("/mcp")
async def mcp(request: Request, mcp_session_id: Optional[str] = Header(default=None)):
    try:
        payload = await request.json()
    except Exception:
        return Response("Bad Request", status_code=400)

    method = payload.get("method")
    rpc_id = payload.get("id")
    params = payload.get("params") or {}

    if method == "initialize":
        session_id = uuid.uuid4().hex
        SESSIONS[session_id] = {"ready": False}
        return ok({"jsonrpc": "2.0", "id": rpc_id,
                   "result": {"protocolVersion": "2024-11-05", "capabilities": {}}}, session_id=session_id)

    sid = request.headers.get("mcp-session-id") or request.headers.get("x-mcp-session-id")
    if not sid or sid not in SESSIONS:
        return ok({"jsonrpc":"2.0","id":rpc_id,
                   "error":{"code":-32000,"message":"Invalid session header"}}, status=400)

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
        return ok({"jsonrpc": "2.0", "id": rpc_id, "result": {"tools": tools}})

    if method == "tools/call":
        name = (params.get("name") or "").strip()
        arguments = params.get("arguments") or {}

        if name == "ping":
            msg = arguments.get("message", "")
            return ok({"jsonrpc": "2.0", "id": rpc_id,
                       "result": {"content": [{"type": "text", "text": f"pong: {msg}"}]}})

        if name == "get_student_profile":
            student_id = arguments.get("student_id")
            demo = {
                "student_en_001": {
                    "id": "student_en_001",
                    "first_name": "Ava",
                    "last_name": "Johnson",
                    "language": "en",
                    "eligible_fafsa": True,
                    "year": "2025–26",
                    "dependency": "dependent",
                    "parent_status_2023": "divorced",
                    "contributors_expected": 2,
                    "schools": ["Harvard University"],
                },
                "student_es_001": {
                    "id": "student_es_001",
                    "first_name": "Mateo",
                    "last_name": "García",
                    "language": "es",
                    "eligible_fafsa": True,
                    "year": "2025–26",
                    "dependency": "dependent",
                    "parent_status_2023": "divorciado",
                    "contributors_expected": 2,
                    "schools": ["Universidad de Harvard"],
                },
            }
            if student_id in demo:
                obj = demo[student_id]
                return ok({"jsonrpc":"2.0","id":rpc_id,
                           "result":{
                               "content":[{"type":"text","text":json.dumps(obj, ensure_ascii=False)}],
                               "structuredContent": obj,
                               "isError": False}})
            not_found = {"error":"not found","student_id":student_id}
            return ok({"jsonrpc":"2.0","id":rpc_id,
                       "result":{
                           "content":[{"type":"text","text":json.dumps(not_found, ensure_ascii=False)}],
                           "structuredContent": not_found,
                           "isError": False}})

        return ok({"jsonrpc":"2.0","id":rpc_id,
                   "error":{"code":-32601,"message":"Unknown tool"}})

    return ok({"jsonrpc":"2.0","id":rpc_id,
               "error":{"code":-32601,"message":f"Unknown method: {method}"}})
