from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route, Mount

mcp = FastMCP(
    "agenticed-consent",
    version="0.1.0",
    description="AgenticEd demo MCP: consent + ping (stub data)",
)

@mcp.tool()
def ping(message: str) -> str:
    "Roundtrip test tool"
    return f"pong: {message}"

# Consent stub data (demo only)
_DEMO_LEDGER = {
    "G-1001": [
        {"scope": "share_course_grades", "granted": True},
        {"scope": "share_attendance", "granted": True},
        {"scope": "share_discipline", "granted": False},
    ],
    "G-2002": [
        {"scope": "share_course_grades", "granted": False},
        {"scope": "share_attendance", "granted": True},
    ],
}

@mcp.tool()
def get_guardian_scopes(guardian_id: str) -> list[dict]:
    "Return current consent scopes for a guardian (stub)."
    return _DEMO_LEDGER.get(guardian_id, [])

def health(_):
    return JSONResponse({"ok": True, "routes": ["/mcp"]})

app = Starlette(
    debug=False,
    routes=[
        Route("/health", health),
        # POST /mcp (JSON-RPC 2.0 over HTTP) — this is what Agent Builder will hit
        Mount("/", mcp.http_app()),
    ],
)
