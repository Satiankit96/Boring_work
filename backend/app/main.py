"""
FastAPI Application Factory
===========================
Role: Create and configure the FastAPI application instance.
Includes router registration, CORS middleware, startup/shutdown events.
This is the central hub — all modules plug into this file.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.base import init_db, close_db
from app.api.v1.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    - Startup: Initialize database tables
    - Shutdown: Close database connections
    """
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


def create_app() -> FastAPI:
    """
    Application factory function.
    Creates and configures the FastAPI app with all middleware and routers.
    """
    app = FastAPI(
        title="Auth Module API",
        description="Module 01: Authentication microservice for scalable SaaS platform",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routers
    app.include_router(auth_router, prefix="/api/v1")

    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Simple health check endpoint."""
        return {"status": "healthy", "module": "auth"}

    return app


# Create app instance
app = create_app()
