#!/usr/bin/env python
"""
run.py — Project bootstrap and health-check entry point.
=========================================================
This script:
  1. Checks that all required Python packages are installed.
  2. Creates the backend/.env file from .env.example if it doesn't exist.
  3. Creates the data/ directory for the SQLite database if it doesn't exist.
  4. Runs the import chain to verify no import errors exist in the codebase.
  5. Initialises the SQLite database (creates tables).
  6. Starts the uvicorn server.

Usage:
    cd backend
    python ../run.py          # from the repo root
    -- OR --
    cd Boring_work
    python run.py             # from the project root (this file)
"""

import sys
import os
import subprocess
import shutil
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
BACKEND = ROOT / "backend"
ENV_FILE = BACKEND / ".env"
ENV_EXAMPLE = BACKEND / ".env.example"
DATA_DIR = BACKEND / "data"
REQUIREMENTS = BACKEND / "requirements.txt"

REQUIRED_PACKAGES = [
    "fastapi",
    "uvicorn",
    "sqlalchemy",
    "aiosqlite",
    "pydantic",
    "pydantic_settings",
    "jose",
    "passlib",
    "multipart",
    "email_validator",
]

# ── Helpers ───────────────────────────────────────────────────────────────────────

def step(msg: str):
    print(f"\n✅  {msg}")

def warn(msg: str):
    print(f"\n⚠️   {msg}")

def fail(msg: str):
    print(f"\n❌  {msg}")
    sys.exit(1)


# ── Step 1: Check Python version ─────────────────────────────────────────────────

if sys.version_info < (3, 10):
    fail(f"Python 3.10+ required. You have {sys.version}. Please upgrade.")
step(f"Python version OK: {sys.version.split()[0]}")


# ── Step 2: Install / check dependencies ─────────────────────────────────────────

print("\n📦  Checking / installing dependencies from requirements.txt …")
result = subprocess.run(
    [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS), "--quiet"],
    capture_output=True,
    text=True,
)
if result.returncode != 0:
    fail(f"pip install failed:\n{result.stderr}")
step("All dependencies installed.")


# ── Step 3: Check each package imports ───────────────────────────────────────────

print("\n🔍  Verifying package imports …")
missing = []
for pkg in REQUIRED_PACKAGES:
    try:
        __import__(pkg)
    except ImportError:
        missing.append(pkg)

if missing:
    fail(f"The following packages failed to import: {missing}\nRun: pip install -r backend/requirements.txt")
step("All packages import successfully.")


# ── Step 4: Ensure .env exists ───────────────────────────────────────────────────

if not ENV_FILE.exists():
    if ENV_EXAMPLE.exists():
        shutil.copy(ENV_EXAMPLE, ENV_FILE)
        warn(f".env not found — copied from .env.example to {ENV_FILE}\n"
             f"    ⚡ Please update SECRET_KEY before deploying to production!")
    else:
        fail(f"Neither .env nor .env.example found in {BACKEND}. Cannot start.")
else:
    step(f".env file found at {ENV_FILE}")


# ── Step 5: Ensure data directory exists ─────────────────────────────────────────

DATA_DIR.mkdir(parents=True, exist_ok=True)
step(f"Data directory ready: {DATA_DIR}")


# ── Step 6: Verify module import chain ───────────────────────────────────────────

print("\n🔗  Verifying backend module imports …")
os.chdir(BACKEND)                          # must cd into backend so 'app' package resolves
sys.path.insert(0, str(BACKEND))

try:
    from app.core.config import settings
    from app.core.security import hash_password, verify_password, create_access_token, decode_token
    from app.core.exceptions import InvalidCredentialsError, EmailAlreadyExistsError
    from app.db.base import init_db, Base
    from app.models.user import User
    from app.models.schemas import RegisterRequest, LoginRequest, LoginResponse, UserOut
    from app.repositories.base import IUserRepository
    from app.repositories.sqlite_user_repository import SqliteUserRepository
    from app.services.auth_service import AuthService
    from app.middleware.auth_middleware import get_current_user_id
    from app.api.v1.auth import router
    from app.main import app
except Exception as e:
    fail(f"Import chain failed: {e}\nFix the error above before starting the server.")

step("All backend modules import successfully.")
print(f"   DB URL      : {settings.database_url}")
print(f"   Environment : {settings.app_env}")
print(f"   CORS origins: {settings.cors_origins}")


# ── Step 7: Init database (create tables) ────────────────────────────────────────

print("\n🗄️   Initialising database …")
import asyncio

async def _init():
    await init_db()

asyncio.run(_init())
step("Database tables created / verified.")


# ── Step 8: Quick sanity-check — hash + verify roundtrip ─────────────────────────

test_hash = hash_password("TestPassword123!")
assert verify_password("TestPassword123!", test_hash), "bcrypt roundtrip failed!"
step("bcrypt hash/verify roundtrip: PASSED")

token = create_access_token({"sub": "test-user-id"})
payload = decode_token(token)
assert payload.get("sub") == "test-user-id", "JWT roundtrip failed!"
step("JWT sign/verify roundtrip: PASSED")


# ── Step 9: Start server ──────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("🚀  All checks passed! Starting the server …")
print("=" * 60)
print(f"\n   API docs  →  http://localhost:8000/docs")
print(f"   ReDoc     →  http://localhost:8000/redoc")
print(f"   Health    →  http://localhost:8000/health\n")

import uvicorn
uvicorn.run(
    "app.main:app",
    host="0.0.0.0",
    port=8000,
    reload=True,
    log_level="info",
)
