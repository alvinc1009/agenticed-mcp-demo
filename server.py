# server.py — MCP + ChatKit widget + session API

from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse, HTMLResponse
from starlette.routing import Route, Mount
from fastapi import FastAPI
from pydantic import BaseModel
import os, json, requests

# ---------------- MCP ----------------
mcp = FastMCP(name="agenticed-demo")

@mcp.tool()
def ping(message: str) -> str:
    """Echo a short message."""
    return f"pong: {message}"

# Optional: demo data tool
DATA_PATH = os.path.join(os.path.dirname(__file__), "dummy_data.json")
DUMMY = {}
if os.path.exists(DATA_PATH):
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        DUMMY = json.load(f)

@mcp.tool()
def get_student_profile(student_id: str) -> dict:
    """Return a demo student profile from local dummy_data.json."""
    return DUMMY.get("students", {}).get(student_id) or {"error": "not found"}

def health(_):
    return JSONResponse({"ok": True})

def version(_):
    try:
        import mcp as mcp_pkg, fastmcp as fastmcp_pkg
        ver = f"agenticed-mcp-demo / fastmcp {fastmcp_pkg.__version__} / mcp {mcp_pkg.__version__}"
    except Exception:
        ver = "agenticed-mcp-demo"
    return PlainTextResponse(ver)

# ------------- ChatKit session API (FastAPI sub-app) -------------
api = FastAPI()

class SessionIn(BaseModel):
    user: str | None = None
    metadata: dict | None = None

@api.post("/chatkit/session")
def chatkit_session(inp: SessionIn):
    api_key = os.environ.get("OPENAI_API_KEY")
    wf_id = os.environ.get("CHATKIT_WORKFLOW_ID")  # e.g., wf_68e7f0be6b3...
    if not api_key or not wf_id:
        return JSONResponse(
            {"error": "Missing OPENAI_API_KEY or CHATKIT_WORKFLOW_ID"},
            status_code=500,
        )
    body = {"workflow": {"id": wf_id}, "user": inp.user or "demo-user"}
    if inp.metadata:
        body["metadata"] = inp.metadata

    r = requests.post(
        "https://api.openai.com/v1/chatkit/sessions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "OpenAI-Beta": "chatkit_beta=v1",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=20,
    )
    return JSONResponse(r.json(), status_code=r.status_code)

# ------------- Simple homepage with ChatKit widget -------------
INDEX_HTML = """<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>AgentICED Demo</title>
<script src="https://cdn.platform.openai.com/deployments/chatkit/chatkit.js" async></script>
<style>
  body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin:0; }
  header { padding:12px 16px; border-bottom:1px solid #eee; }
  main { padding:16px; display:flex; }
  #chat { height: 620px; width: 380px; max-width: 100%; }
</style>
</head>
<body>
  <header><strong>AgentICED Demo</strong></header>
  <main>
    <div id="chat">Loading chat…</div>
  </main>
<script>
(async function(){
  // Wait for ChatKit global from the CDN
  while (!window.ChatKit || !window.ChatKit.mount) {
    await new Promise(r => setTimeout(r, 40));
  }

  // Stable per-device id
  let deviceId = localStorage.getItem("device_id");
  if (!deviceId) {
    deviceId = (crypto.randomUUID && crypto.randomUUID()) || String(Date.now());
    localStorage.setItem("device_id", deviceId);
  }

  // Ask the server for a client_secret
  let resp = await fetch('/api/chatkit/session', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ user: deviceId })
  });
  let data = await resp.json();
  if (!data.client_secret) {
    document.getElementById('chat').innerHTML =
      '<p style="color:red">Failed to create chat session.</p>';
    console.error('Session error:', data);
    return;
  }

  // Mount the ChatKit widget
  window.ChatKit.mount({
    el: document.getElementById('chat'),
    clientSecret: data.client_secret,
    title: 'FAFSA Guide',
    subtitle: 'I can help you apply, track deadlines, and organize docs',
  });
})();
</script>
</body></html>
"""

# ------------- Compose parent ASGI app (Starlette) -------------
mcp_asgi = mcp.http_app()
app = Starlette(
    routes=[
        Route("/", lambda req: HTMLResponse(INDEX_HTML), methods=["GET"]),
        Route("/health", health, methods=["GET"]),
        Route("/version", version, methods=["GET"]),
        Mount("/mcp", app=mcp_asgi, name="mcp"),
        Mount("/api", app=api, name="api"),
    ],
    lifespan=mcp_asgi.lifespan,  # important for FastMCP
)
