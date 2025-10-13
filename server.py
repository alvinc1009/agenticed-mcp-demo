# server.py — minimal MCP HTTP server with health/version + ping + demo profile

from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route, Mount
import json, os

# ---------- MCP server ----------
mcp = FastMCP(name="agenticed-demo")

@mcp.tool()
def ping(message: str) -> str:
    """Echo a short message."""
    return f"pong: {message}"

# Fallback demo DB (used if dummy_data.json not present/invalid)
_FALLBACK_DB = {
    "students": {
        "student_001": {
            "name": "Demo Student",
            "email": "demo@example.com",
            "fa_eligible": True,
            "fa_years": ["2025–26"],
            "dependency": "dependent",
            "fsa_id_ready": True,
            "parent_status": "divorced",
            "contributors": 2,
            "schools": [
                "Harvard University",
                "Bunker Hill Community College",
                "Ohio Wesleyan University"
            ]
        }
    }
}

def _load_db():
    path = os.path.join(os.path.dirname(__file__), "dummy_data.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return _FALLBACK_DB

_DB = _load_db()

@mcp.tool()
def get_student_profile(student_id: str) -> dict:
    """Return a demo student profile from dummy_data.json (or fallback)."""
    return _DB.get("students", {}).get(student_id, {})

# ---------- HTTP utils ----------
def root(_):
    return PlainTextResponse("OK. Use POST /mcp for JSON-RPC. Try GET /health.")

def health(_):
    return JSONResponse({"ok": True, "routes": ["/mcp"]})

def version(_):
    return PlainTextResponse("agenticed-mcp-demo / fastmcp 2.12.1 / mcp 1.16.0")

# ---------- Starlette app ----------
app = Starlette(debug=False, routes=[
    Route("/", root, methods=["GET"]),
    Route("/health", health, methods=["GET"]),
    Route("/version", version, methods=["GET"]),
    # Provides POST /mcp (JSON-RPC) while keeping the routes above working
    Mount("/", mcp.http_app()),
])
