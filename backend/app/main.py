"""ArtForge Publisher - FastAPI Application Entry Point."""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    logger.info("Starting ArtForge Publisher API")
    # Startup: Initialize database connections, etc.
    yield
    # Shutdown: Clean up resources
    logger.info("Shutting down ArtForge Publisher API")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.VERSION,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    from app.api.routes import images, analysis, content, prompts
    app.include_router(images.router, prefix="/api/v1/images", tags=["images"])
    app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["analysis"])
    app.include_router(content.router, prefix="/api/v1/content", tags=["content"])
    app.include_router(prompts.router, prefix="/api/v1/prompts", tags=["prompts"])
    
    # Mount static files for images and thumbnails
    app.mount("/storage", StaticFiles(directory=str(settings.STORAGE_PATH)), name="storage")
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "artforge-publisher"}
    
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "ArtForge Publisher API",
            "version": settings.VERSION,
            "docs": "/api/docs"
        }
    
    return app


# Create the application instance
app = create_application()
