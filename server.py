import os
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route, Mount
import json, pathlib

PROFILE = os.getenv("AGENT_PROFILE", "fafsa").lower()  # fafsa, attendance, math, ontrack, cte, parent
NAME = {
    "fafsa":"faFSA Agent",
    "attendance":"Attendance Agent",
    "math":"College-Ready Math Agent",
    "ontrack":"On-Track & Dual Enrollment Agent",
    "cte":"CTE Pathway Agent",
    "parent":"Parent Advocate Agent",
}.get(PROFILE, PROFILE)

DATA_FILE = pathlib.Path(__file__).with_name(f"dummy_data_{PROFILE}.json")

mcp = FastMCP(name=f"agenticed-{PROFILE}")

@mcp.tool()
def ping(message: str) -> str:
    return f"{PROFILE}: pong: {message}"

@mcp.tool()
def get_student_profile(student_id: str) -> dict:
    if not DATA_FILE.exists():
        return {"error":"dummy data file not found", "file": DATA_FILE.name}
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        return {"error": f"bad json: {e}"}
    return data.get(student_id, {"error": "not found", "student_id": student_id})

mcp_app = mcp.http_app()

def health(_):  return JSONResponse({"ok": True})
def version(_): return PlainTextResponse(f"{NAME} / profile={PROFILE} / fastmcp 2.12.1 / mcp 1.16.0")

app = Starlette(
    routes=[
        Route("/health",  health,  methods=["GET"]),
        Route("/version", version, methods=["GET"]),
        Mount("/", app=mcp_app),
    ],
    lifespan=mcp_app.lifespan,
)
