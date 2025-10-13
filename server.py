# Minimal MCP HTTP server w/ dummy tools for FAFSA demo
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route, Mount
import json
import os
from datetime import datetime, timedelta

# ---------- Load demo data ----------
DATA_PATH = os.path.join(os.path.dirname(__file__), "dummy_data.json")
with open(DATA_PATH, "r", encoding="utf-8") as f:
    DATA = json.load(f)

# ---------- MCP app ----------
mcp = FastMCP(name="agenticed-demo")

# ---- Tools ----

@mcp.tool()
def ping(message: str) -> str:
    """Echo a short message."""
    return f"pong: {message}"

@mcp.tool()
def get_student_profile(student_id: str) -> dict:
    """Return demo profile (name, language, eligibility, state, school prefs)."""
    s = DATA["students"].get(student_id)
    if not s:
        return {"error": f"student_id not found: {student_id}"}
    return {
        "name": s["name"],
        "language": s["language"],
        "eligibility": s["eligibility"],
        "state": s["state"],
        "school_preferences": s.get("school_preferences", [])
    }

@mcp.tool()
def list_deadlines(year: str, school: str = "", state: str = "") -> dict:
    """Return FAFSA deadlines for 2025–26 demo."""
    if year not in ["2025–26", "2024–25", "2025-26", "2024-25"]:
        # normalize lightly, but this demo only has 2025–26
        pass
    d = DATA["deadlines_2025_26"]
    result = {
        "fafsa_open": "2024-10-01",
        "federal_deadline": d["federal_deadline"],
        "state_deadline": None,
        "school_priority_deadline": None,
        "source": "demo",
        "last_checked": datetime.utcnow().isoformat() + "Z"
    }
    if state and state in d["states"]:
        result["state_deadline"] = d["states"][state]["state_deadline"]
    if school and school in d["schools"]:
        result["school_priority_deadline"] = d["schools"][school]["priority"]
    return result

@mcp.tool()
def ensure_student_folder(student_id: str, year: str) -> dict:
    """Pretend to create a folder and return a URL."""
    folder_url = f"https://files.example.com/{student_id}/{year.replace(' ', '').replace('–','-')}"
    return {"folder_url": folder_url}

@mcp.tool()
def upload_placeholder(student_id: str, year: str, doc_type: str) -> dict:
    """Return an upload link for a required document."""
    link = f"https://files.example.com/upload/{student_id}/{year.replace(' ', '').replace('–','-')}/{doc_type}"
    return {"upload_link": link}

@mcp.tool()
def list_required_docs(student_id: str, year: str) -> dict:
    """Return a small checklist with statuses."""
    return {
        "docs": [
            {"type": "tax_2023_student", "description": "Student 2023 tax return / W-2", "required": True, "status": "missing"},
            {"type": "tax_2023_parent", "description": "Parent 2023 tax return / W-2", "required": True, "status": "missing"},
            {"type": "id_proof", "description": "Identity document (student)", "required": True, "status": "missing"},
            {"type": "school_list", "description": "Target schools list", "required": False, "status": "received"}
        ]
    }

@mcp.tool()
def create_calendar_event(student_id: str, title: str, start_iso: str, end_iso: str = "", description: str = "") -> dict:
    """Return a fake calendar event URL."""
    if not end_iso:
        try:
            start_dt = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
        except Exception:
            start_dt = datetime.utcnow()
        end_iso = (start_dt + timedelta(hours=1)).isoformat() + "Z"
    url = f"https://calendar.example.com/event/{student_id}/{abs(hash(title))%10_000_000}"
    return {"event_url": url, "start": start_iso, "end": end_iso, "title": title, "description": description}

@mcp.tool()
def record_state(student_id: str, state_json: dict) -> dict:
    """No-op persistence for demo."""
    return {"ok": True, "echo": state_json}

# ---------- Plain endpoints ----------
def health(_):
    return JSONResponse({"ok": True})

def version(_):
    return PlainTextResponse(f"agenticed-mcp-demo / fastmcp {mcp.__class__.__name__}")

# ---------- ASGI app ----------
# IMPORTANT: pass lifespan=mcp_app.lifespan to avoid stream init errors
app = Starlette(
    debug=False,
    routes=[
        Route("/health", health, methods=["GET"]),
        Route("/version", version, methods=["GET"]),
        Mount("/", mcp.http_app())
    ],
    lifespan=mcp.http_app().lifespan
)
