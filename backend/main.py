import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from database import init_db
from routers import user, task, energy
from config import get_settings

# Initialize settings
settings = get_settings()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Lifespan context manager (replaces deprecated on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    init_db()
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} started!")
    logger.info(f"📦 Database initialized")
    logger.info(f"🌍 Environment: {settings.ENVIRONMENT}")
    
    if settings.DEBUG:
        try:
            from api_logger import init_log_file
            init_log_file()
            logger.info("📋 API logging enabled - logs saved to api-logs.txt")
        except ImportError:
            pass
    
    yield
    
    # Shutdown
    logger.info(f"👋 {settings.APP_NAME} shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Friendo API",
    description="Neuro-Inclusive Executive Function Companion",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    openapi_url="/api/openapi.json" if settings.DEBUG else None,
)

# GZip middleware for compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# API logging middleware for development/testing only
if settings.DEBUG:
    try:
        from api_logger import APILoggerMiddleware
        app.add_middleware(APILoggerMiddleware)
    except ImportError:
        pass


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    if settings.DEBUG:
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "type": type(exc).__name__}
        )
    
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again later."}
    )


# Include routers
app.include_router(user.router)
app.include_router(task.router)
app.include_router(energy.router)


# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


# Serve static files (frontend build)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    # Serve assets with cache headers
    app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")
    
    @app.get("/manifest.json")
    async def serve_manifest():
        """Serve PWA manifest."""
        return FileResponse(
            os.path.join(static_dir, "manifest.json"),
            media_type="application/manifest+json"
        )
    
    @app.get("/")
    async def serve_root():
        """Serve the frontend application."""
        return FileResponse(os.path.join(static_dir, "index.html"))
    
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve SPA for all other routes."""
        # Don't serve static files for API routes
        if full_path.startswith("api/") or full_path.startswith("users/") or \
           full_path.startswith("tasks/") or full_path.startswith("energy/"):
            raise HTTPException(status_code=404, detail="Not found")
        
        file_path = os.path.join(static_dir, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(static_dir, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else settings.WORKERS,
        log_level="debug" if settings.DEBUG else "info"
    )
