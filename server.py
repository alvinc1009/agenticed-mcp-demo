# server.py — MCP HTTP server with ping + FAFSA demo tools + calendar/files
from __future__ import annotations
import os, json, base64, uuid, datetime as dt
from typing import List, Optional, Dict, Any

from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route, Mount

# ---------- Helpers (demo persistence on disk) ----------
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(APP_DIR, "dummy_data.json")
CAL_DB = os.path.join(APP_DIR, "calendar_store.json")  # demo calendar
FILES_ROOT = os.path.join(APP_DIR, "files")            # demo “drive”

os.makedirs(FILES_ROOT, exist_ok=True)

def _load_json(path: str, default: Any) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def _save_json(path: str, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------- Starlette health/version ----------
def health(_):
    # Keep it minimal so Render health checks stay fast
    return JSONResponse({"ok": True})

def version(_):
    return PlainTextResponse("agenticed-mcp-demo / fastmcp 2.12.1 / mcp 1.16.0")

def root(_):
    return PlainTextResponse("OK. Try GET /health")

# ---------- FastMCP server ----------
mcp = FastMCP(name="agenticed-demo")

@mcp.tool()
def ping(message: str) -> str:
    """Echo a short message."""
    return f"pong: {message}"

# ---- FAFSA: get_student_profile (reads dummy_data.json) ----
@mcp.tool()
def get_student_profile(student_id: str) -> Dict[str, Any]:
    """
    Return a student profile by ID from dummy_data.json
    """
    db = _load_json(DATA_FILE, default={"students": []})
    for row in db.get("students", []):
        if row.get("student_id") == student_id:
            return row
    return {"error": f"student_id '{student_id}' not found"}

# ---- Calendar tool (demo) ----
@mcp.tool()
def add_calendar_event(
    student_id: str,
    title: str,
    start_iso: str,
    end_iso: Optional[str] = None,
    location: Optional[str] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a demo calendar event for the student.
    Times are ISO-8601 (e.g., 2025-10-13T15:00:00-04:00). Returns event_id.
    """
    # Validate minimal ISO shape; keep it light for demo
    try:
        dt.datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
        if end_iso:
            dt.datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
    except Exception:
        return {"error": "Invalid ISO datetimes. Use e.g. 2025-10-13T15:00:00-04:00"}

    store = _load_json(CAL_DB, default={})
    events = store.setdefault(student_id, [])
    event_id = str(uuid.uuid4())

    event = {
        "event_id": event_id,
        "title": title.strip(),
        "start": start_iso,
        "end": end_iso,
        "location": location,
        "notes": notes,
        "created_at": dt.datetime.utcnow().isoformat() + "Z",
    }
    events.append(event)
    _save_json(CAL_DB, store)
    return {"ok": True, "event": event}

# ---- Drive tools (demo) ----
@mcp.tool()
def create_drive_folder(student_id: str, folder_name: str) -> Dict[str, Any]:
    """
    Create a demo folder under /app/files/{student_id}/{folder_name}
    Returns a pseudo URL you can show to users.
    """
    safe_student = student_id.strip().replace("..", "")
    safe_folder = folder_name.strip().replace("..", "")
    path = os.path.join(FILES_ROOT, safe_student, safe_folder)
    os.makedirs(path, exist_ok=True)

    # For the Render demo, return a pseudo URL (not browseable unless you expose it).
    pseudo_url = f"/files/{safe_student}/{safe_folder}"
    return {"ok": True, "folder_path": path, "url": pseudo_url}

@mcp.tool()
def save_drive_file(
    student_id: str,
    folder_name: str,
    filename: str,
    content_base64: str,
    mime_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Save a base64 file into the student's folder. Use with create_drive_folder first.
    """
    safe_student = student_id.strip().replace("..", "")
    safe_folder = folder_name.strip().replace("..", "")
    safe_file = filename.strip().replace("..", "")

    path = os.path.join(FILES_ROOT, safe_student, safe_folder)
    os.makedirs(path, exist_ok=True)

    try:
        blob = base64.b64decode(content_base64)
    except Exception:
        return {"error": "content_base64 is not valid base64"}

    fpath = os.path.join(path, safe_file)
    with open(fpath, "wb") as f:
        f.write(blob)

    return {
        "ok": True,
        "saved": {"student_id": safe_student, "folder": safe_folder, "filename": safe_file, "bytes": len(blob)},
    }

# ---------- Build Starlette app; mount MCP with lifespan ----------
mcp_app = mcp.http_app()  # provides /mcp when mounted at "/"
app = Starlette(
    debug=False,
    routes=[
        Route("/", root, methods=["GET"]),
        Route("/health", health, methods=["GET"]),
        Route("/version", version, methods=["GET"]),
        Mount("/", app=mcp_app),  # includes POST /mcp (SSE JSON-RPC)
    ],
    lifespan=mcp_app.lifespan,    # IMPORTANT for FastMCP session manager
)
