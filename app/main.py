"""
CodeMind AI - entry point. Wires up all routers, initializes the local
database, and serves the single-page frontend. Everything runs on your
machine: FastAPI (this process), Ollama (local LLM), ChromaDB (local vector
store), SQLite/Postgres (local DB). No external API calls required.
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.database import init_db
from app.routers import repo_router, chat_router, code_router, architecture_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("codemind.main")

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(repo_router.router)
app.include_router(chat_router.router)
app.include_router(code_router.router)
app.include_router(architecture_router.router)


@app.on_event("startup")
def on_startup():
    init_db()
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} starting up")
    logger.info(f"LLM: Ollama @ {settings.OLLAMA_HOST} (model={settings.OLLAMA_MODEL})")
    logger.info(f"Vector store: ChromaDB @ {settings.CHROMA_PERSIST_DIR}")
    logger.info(f"Database: {settings.DATABASE_URL}")


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


# ---- Serve the frontend (single-page app) ----
app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/")
def root():
    return FileResponse("frontend/index.html")
