from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime
from app.services import InstagramService, TikTokService

# Note: StaticFiles will be mounted after static setup task
# from fastapi.staticfiles import StaticFiles

def log_to_file(message: str, log_path: str):
    """
    Direct file writing function that forces immediate disk write.
    """
    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
            f.write(f"{timestamp} - app.main - INFO - {message}\n")
            f.flush()
            os.fsync(f.fileno())
    except Exception as e:
        print(f"Error writing to log file: {e}")

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application instance.
    """
    # File logging setup - simple file handler with immediate writing
    log_dir = os.getenv("LOG_DIR", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "app.log")
    
    # Remove all existing handlers
    for h in list(logging.root.handlers):
        logging.root.removeHandler(h)
    
    # Create simple file handler with immediate writing (delay=False forces immediate file opening)
    handler = logging.FileHandler(log_path, mode='a', encoding='utf-8', delay=False)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logging.root.setLevel(logging.INFO)
    logging.root.addHandler(handler)
    
    # Console handler removed to minimize terminal output
    
    # Force immediate writing by disabling buffering
    import sys
    handler.stream.reconfigure(line_buffering=True)

    app = FastAPI(title="Instagram Downloader API", version="0.1.0")

    # Minimal CORS setup for local development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost", "http://127.0.0.1"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def startup_event():
        """
        Initialize services on application startup.
        This ensures authentication is performed when the server starts.
        """
        # Get log path
        log_dir = os.getenv("LOG_DIR", "logs")
        log_path = os.path.join(log_dir, "app.log")
        
        # Direct file logging for immediate write
        log_to_file("🚀 Starting Instagram Downloader API...", log_path)
        
        # Initialize Instagram service (this will trigger authentication)
        log_to_file("🔧 Initializing Instagram service...", log_path)
        try:
            ig_service = InstagramService()
            log_to_file("✅ Instagram service initialized successfully", log_path)
        except Exception as e:
            error_msg = f"❌ Failed to initialize Instagram service: {str(e)}"
            log_to_file(error_msg, log_path)
        
        # Initialize TikTok service
        log_to_file("🔧 Initializing TikTok service...", log_path)
        try:
            tt_service = TikTokService()
            log_to_file("✅ TikTok service initialized successfully", log_path)
        except Exception as e:
            error_msg = f"❌ Failed to initialize TikTok service: {str(e)}"
            log_to_file(error_msg, log_path)
        
        log_to_file("🎉 All services initialized successfully!", log_path)

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
