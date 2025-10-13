from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route

def root(_):
    return PlainTextResponse("OK. Try GET /health")

def health(_):
    return JSONResponse({"ok": True})

app = Starlette(debug=False, routes=[
    Route("/", root, methods=["GET"]),
    Route("/health", health, methods=["GET"]),
])
