"""
Audio Transcriber FastAPI Application
Main entry point for the WhisperX-based transcription API
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import router as api_router
from core.logger import setup_logger
from core.config_loader import load_config
from core.task_manager import TaskManager
from core.file_manager import FileManager


# Global instances
task_manager = None
file_manager = None
config = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events
    """
    global task_manager, file_manager, config

    # Startup
    logger = logging.getLogger(__name__)
    logger.info("Starting Audio Transcriber API...")

    try:
        # Load configuration
        config = load_config()
        logger.info("Configuration loaded successfully")

        # Initialize managers
        task_manager = TaskManager(config)
        file_manager = FileManager(config)

        # Start background tasks
        asyncio.create_task(task_manager.start_processing())
        asyncio.create_task(file_manager.start_monitoring())

        logger.info("Audio Transcriber API started successfully")

    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Audio Transcriber API...")

    if task_manager:
        await task_manager.stop()
    if file_manager:
        await file_manager.stop()

    logger.info("Audio Transcriber API shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Audio Transcriber API",
    description="WhisperX-based audio transcription service with priority queue processing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """
    Global HTTP exception handler
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status": "error"}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """
    Global exception handler for unhandled exceptions
    """
    logger = logging.getLogger(__name__)
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "status": "error"}
    )


# Include API routes
app.include_router(api_router, prefix="/api/v1")


# Basic health check endpoint
@app.get("/health")
async def health_check():
    """
    Basic health check endpoint
    """
    return {
        "status": "healthy",
        "service": "Audio Transcriber API",
        "version": "1.0.0"
    }


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "Audio Transcriber API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn

    # Setup logging
    setup_logger()

    # Run the application
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Set to False in production
        log_level="info"
    )
