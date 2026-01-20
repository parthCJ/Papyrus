from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.config import settings
from app.api.routes import upload, query, documents
from app.utils.logger import setup_logger
from app.core.embedding_service import EmbeddingService
import os

logger = setup_logger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="RAG System for Research Papers with Hybrid Search",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    upload.router, prefix=f"{settings.API_V1_STR}/upload", tags=["upload"]
)
app.include_router(query.router, prefix=f"{settings.API_V1_STR}/query", tags=["query"])
app.include_router(
    documents.router, prefix=f"{settings.API_V1_STR}/documents", tags=["documents"]
)


@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(
        f"Elasticsearch: {settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}"
    )
    logger.info(f"Ollama: {settings.OLLAMA_HOST}")

    # Preload embedding model to avoid first-query delay
    logger.info("Preloading embedding model...")
    embedding_service = EmbeddingService()
    embedding_service.initialize()
    logger.info("Embedding model preloaded successfully")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }


# Serve frontend
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api") or full_path == "health":
            return {"error": "Not found"}

        if full_path == "" or full_path == "/":
            return FileResponse(os.path.join(frontend_path, "index.html"))

        file_path = os.path.join(frontend_path, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)

        return FileResponse(os.path.join(frontend_path, "index.html"))
