# Minimal Starlette + FastMCP with proper lifespan + mounted /mcp
import json, os
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route, Mount
from fastmcp import FastMCP

mcp = FastMCP(name="agenticed-demo")

@mcp.tool()
def ping(message: str) -> str:
    """Echo a short message."""
    return f"pong: {message}"

# Example: read a student profile from dummy_data.json
@mcp.tool()
def get_student_profile(student_id: str) -> dict:
    with open("dummy_data.json", "r", encoding="utf-8") as f:
        db = json.load(f)
    return db.get(student_id, {"error": "not found"})

def health(_):
    return JSONResponse({"ok": True})

def version(_):
    return PlainTextResponse("agenticed-mcp-demo / fastmcp 2.12.1 / mcp 1.16.0")

# Make sure lifespan is passed through to the parent app
app = Starlette(routes=[
    Route("/health", health, methods=["GET"]),
    Route("/version", version, methods=["GET"]),
    Mount("/", mcp.http_app()),
], lifespan=mcp.lifespan)
