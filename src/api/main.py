from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import settings
from .db import init_db
from .routers import auth, query, web

app = FastAPI(title="FreeAgent Reader")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/freeagent")
app.include_router(query.router, prefix="/api")
app.include_router(web.router)


# Health check
@app.get("/healthz")
def health():
    return {"status": "ok", "service": "freeagent-reader"}


# Web UI
@app.get("/", response_class=HTMLResponse)
def index():
    return FileResponse("templates/index.html")


@app.get("/templates/{path:path}", response_class=FileResponse)
def serve_template(path: str):
    return FileResponse(f"templates/{path}")


@app.on_event("startup")
def startup():
    init_db()
