# main.py
# Role: FastAPI app factory. Creates the app, registers routers, configures CORS, and runs DB init on startup.
# This is the composition root — the only place where concrete implementations are wired together.

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.db.base import init_db
from app.api.v1.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run DB table creation on startup."""
    await init_db()
    yield


app = FastAPI(
    title="Auth Module — Module 01",
    description="Production-grade authentication microservice (FastAPI + SQLite).",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS — explicit origins only. No wildcard in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)


@app.get("/health", tags=["health"])
async def health_check():
    """Liveness probe endpoint."""
    return {"status": "ok", "env": settings.app_env}


# Global exception handler — never leak stack traces to clients
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"}},
    )
