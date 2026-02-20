# server.py
# Role: Entry point for the backend server. Starts uvicorn pointing at app.main:app.
# Run with: python server.py  (or via run.py at the project root)

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
