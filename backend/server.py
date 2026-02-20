"""
Server Entry Point
==================
Role: Production entry point for running the FastAPI application.
Uses Uvicorn ASGI server. Run with: python server.py
"""

import uvicorn

from app.core.config import settings


def main():
    """
    Start the Uvicorn server.
    Configuration varies based on APP_ENV setting.
    """
    # Development vs Production settings
    is_dev = settings.app_env == "development"
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=is_dev,  # Hot reload in development
        log_level="debug" if is_dev else "info",
    )


if __name__ == "__main__":
    main()
