"""FastAPI application entrypoint for LangGraph Chatbot."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.config import settings
from app.routers import health_router, chat_router
from app.data import ingest_all

# Directorios de la aplicación
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
FRONTEND_INDEX = STATIC_DIR / "index.html"

# Ejecutar ingesta de datos en el arranque
ingest_all()

# Instancia ÚNICA de FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Production-ready Chatbot API built with FastAPI, LangChain, and LangGraph. "
        "Supports multi-turn memory checkpointer, tool-calling agent, streaming SSE, and fallback demo mode."
    ),
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(health_router)
app.include_router(chat_router)

# Servir archivos estáticos del frontend
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=JSONResponse, tags=["Root"])
async def root():
    """Root endpoint providing quick links and service status."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs_url": "/docs",
        "health_url": "/health",
        "chat_url": "/chat",
        "chat_stream_url": "/chat/stream",
        "tools_url": "/chat/tools",
        "graph_diagram_url": "/chat/graph?format=html",
        "demo_ui_url": "/demo",
    }


@app.get("/demo", response_class=HTMLResponse, tags=["UI"])
async def demo_ui():
    """Serve the React frontend (built output from frontend/)."""
    if FRONTEND_INDEX.exists():
        return HTMLResponse(content=FRONTEND_INDEX.read_text(encoding="utf-8"))
    return HTMLResponse(
        content=(
            "<h3>Frontend no compilado.</h3>"
            "<p>Ejecuta <code>cd frontend &amp;&amp; npm install &amp;&amp; npm run build</code> "
            "antes de acceder a la interfaz.</p>"
        ),
        status_code=200,
    )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )