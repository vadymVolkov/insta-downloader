from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
from logging.handlers import RotatingFileHandler
import os

# Note: StaticFiles will be mounted after static setup task
# from fastapi.staticfiles import StaticFiles

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application instance.
    """
    # File logging setup (disable console root handlers)
    log_dir = os.getenv("LOG_DIR", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "app.log")
    for h in list(logging.root.handlers):
        logging.root.removeHandler(h)
    handler = RotatingFileHandler(log_path, maxBytes=5*1024*1024, backupCount=3)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logging.root.setLevel(logging.INFO)
    logging.root.addHandler(handler)

    app = FastAPI(title="Instagram Downloader API", version="0.1.0")

    # Minimal CORS setup for local development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost", "http://127.0.0.1"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def health() -> dict:
        """
        Return a minimal health check payload to confirm the API is running.
        """
        return {"status": "ok", "service": "instagram-downloader"}

    # Include API routers
    from app.routers.download import router as download_router
    app.include_router(download_router)

    # Static files mounting
    app.mount("/static", StaticFiles(directory="app/media"), name="static")

    return app

app = create_app()
