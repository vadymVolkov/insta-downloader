"""
Main application module for Instagram Downloader API.
Provides centralized application initialization, configuration, and lifecycle management.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
import os
import asyncio
import signal
import sys
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from app.services import InstagramService, TikTokService
from app.services.ffmpeg_utils import verify_ffmpeg_installation, cleanup_audio_files
from app.config import AppConfig
from app.utils.logger import get_logger, get_request_logger, get_service_logger
from app.utils.exceptions import (
    InstagramDownloaderError, ServiceError, ConfigurationError,
    handle_instagram_downloader_error, handle_generic_exception, handle_http_exception
)
from app.middleware.logging_middleware import LoggingMiddleware


class ApplicationManager:
    """
    Manages application lifecycle, services, and background tasks.
    """
    
    def __init__(self):
        self.logger = get_logger("app.manager")
        self.instagram_service: Optional[InstagramService] = None
        self.tiktok_service: Optional[TikTokService] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
    
    def log_to_file(self, message: str, log_path: str):
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

    async def initialize_services(self):
        """
        Initialize all application services with proper error handling.
        """
        # Initialize Instagram service
        self.logger.info("Initializing Instagram service")
        try:
            self.instagram_service = InstagramService()
            self.logger.info("Instagram service initialized successfully")
        except Exception as e:
            self.logger.error("Failed to initialize Instagram service", error=str(e))
            raise ServiceError("Instagram", f"Service initialization failed: {str(e)}")
        
        # Initialize TikTok service
        self.logger.info("Initializing TikTok service")
        try:
            self.tiktok_service = TikTokService()
            self.logger.info("TikTok service initialized successfully")
        except Exception as e:
            self.logger.error("Failed to initialize TikTok service", error=str(e))
            raise ServiceError("TikTok", f"Service initialization failed: {str(e)}")
    
    def get_service_status(self) -> dict:
        """
        Get the current status of all services.
        """
        return {
            "instagram_service": "initialized" if self.instagram_service else "not_initialized",
            "tiktok_service": "initialized" if self.tiktok_service else "not_initialized",
            "cleanup_task": "running" if self.cleanup_task and not self.cleanup_task.done() else "stopped"
        }
    
    async def start_background_tasks(self):
        """
        Start background tasks and scheduled operations.
        """
        log_path = os.path.join(AppConfig.LOG_DIR, "app.log")
        
        # Start scheduled audio cleanup background task
        self.log_to_file("🧹 Starting scheduled audio cleanup background task...", log_path)
        self.cleanup_task = asyncio.create_task(self._scheduled_audio_cleanup())
        self.log_to_file("✅ Scheduled audio cleanup task started", log_path)
    
    async def _scheduled_audio_cleanup(self):
        """
        Background task that runs audio cleanup at configured intervals.
        """
        log_path = os.path.join(AppConfig.LOG_DIR, "app.log")
        
        # Check if scheduled cleanup is enabled
        if not AppConfig.AUDIO.ENABLE_SCHEDULED_CLEANUP:
            self.log_to_file("ℹ️ Scheduled audio cleanup is disabled", log_path)
            return
        
        while not self._shutdown_event.is_set():
            try:
                # Wait for configured interval or shutdown signal
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=AppConfig.AUDIO.AUDIO_CLEANUP_INTERVAL
                )
                break  # Shutdown requested
            except asyncio.TimeoutError:
                # Timeout reached, run cleanup
                pass
            
            try:
                self.log_to_file("🧹 Running scheduled audio cleanup...", log_path)
                deleted_files = cleanup_audio_files()
                
                if deleted_files:
                    self.log_to_file(f"✅ Scheduled cleanup completed: removed {len(deleted_files)} old audio files", log_path)
                else:
                    self.log_to_file("ℹ️ Scheduled cleanup: no audio files needed cleanup", log_path)
                    
            except Exception as e:
                error_msg = f"❌ Error in scheduled audio cleanup: {str(e)}"
                self.log_to_file(error_msg, log_path)
                # Continue running even if cleanup fails
                await asyncio.sleep(300)  # Wait 5 minutes before retrying
    
    async def shutdown(self):
        """
        Gracefully shutdown all services and background tasks.
        """
        log_path = os.path.join(AppConfig.LOG_DIR, "app.log")
        self.log_to_file("🛑 Starting graceful shutdown...", log_path)
        
        try:
            # Signal shutdown to background tasks
            self._shutdown_event.set()
            self.log_to_file("📡 Shutdown signal sent to background tasks", log_path)
            
            # Cancel background tasks with timeout
            if self.cleanup_task and not self.cleanup_task.done():
                self.log_to_file("🔄 Cancelling background cleanup task...", log_path)
                self.cleanup_task.cancel()
                try:
                    # Wait for task cancellation with timeout
                    await asyncio.wait_for(self.cleanup_task, timeout=3.0)
                    self.log_to_file("✅ Background cleanup task cancelled", log_path)
                except asyncio.CancelledError:
                    self.log_to_file("✅ Background cleanup task cancelled", log_path)
                except asyncio.TimeoutError:
                    self.log_to_file("⚠️ Background cleanup task cancellation timed out", log_path)
            
            # Cleanup services
            if self.instagram_service:
                self.log_to_file("🔧 Shutting down Instagram service...", log_path)
                # Add any service-specific cleanup here
                self.instagram_service = None
            
            if self.tiktok_service:
                self.log_to_file("🔧 Shutting down TikTok service...", log_path)
                # Add any service-specific cleanup here
                self.tiktok_service = None
            
            # Cancel any remaining asyncio tasks
            current_task = asyncio.current_task()
            for task in asyncio.all_tasks():
                if task != current_task and not task.done():
                    self.log_to_file(f"🔄 Cancelling remaining task: {task.get_name()}", log_path)
                    task.cancel()
            
            # Wait a moment for tasks to cancel
            await asyncio.sleep(0.1)
            
            self.log_to_file("✅ Graceful shutdown completed", log_path)
            
        except Exception as e:
            self.log_to_file(f"❌ Error during shutdown: {str(e)}", log_path)
            raise


# Global application manager instance
app_manager = ApplicationManager()


def setup_signal_handlers():
    """
    Setup signal handlers for graceful shutdown.
    """
    def signal_handler(signum, frame):
        print(f"\n🛑 Received signal {signum}, initiating graceful shutdown...")
        
        # Set shutdown event to trigger graceful shutdown
        if hasattr(app_manager, '_shutdown_event'):
            app_manager._shutdown_event.set()
        
        # CRITICAL FIX: Call app_manager.shutdown() directly
        # This ensures proper cleanup of background tasks and resources
        try:
            import asyncio
            # Get the current event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Schedule the shutdown coroutine
                asyncio.create_task(app_manager.shutdown())
            else:
                # Run the shutdown if no loop is running
                asyncio.run(app_manager.shutdown())
        except Exception as e:
            print(f"❌ Error during shutdown: {e}")
            # Force exit if graceful shutdown fails
            print("🔄 Force exiting due to shutdown error...")
            os._exit(1)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    # Also handle SIGHUP for terminal closure
    signal.signal(signal.SIGHUP, signal_handler)

def setup_logging():
    """
    Configure logging based on application settings.
    """
    log_dir = AppConfig.LOG_DIR
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "app.log")
    
    # Remove all existing handlers
    for h in list(logging.root.handlers):
        logging.root.removeHandler(h)
    
    # Set log level from configuration
    log_level = getattr(logging, AppConfig.LOGGING.LOG_LEVEL.upper(), logging.INFO)
    logging.root.setLevel(log_level)
    
    # File logging (if enabled)
    if AppConfig.LOGGING.ENABLE_FILE_LOGGING:
        handler = logging.FileHandler(log_path, mode='a', encoding='utf-8', delay=False)
        formatter = logging.Formatter(AppConfig.LOGGING.LOG_FORMAT)
        handler.setFormatter(formatter)
        logging.root.addHandler(handler)
        
        # Force immediate writing by disabling buffering
        handler.stream.reconfigure(line_buffering=True)
    
    # Console logging (if enabled)
    if AppConfig.LOGGING.ENABLE_CONSOLE_LOGGING:
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(AppConfig.LOGGING.LOG_FORMAT)
        console_handler.setFormatter(console_formatter)
        logging.root.addHandler(console_handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
    # Startup
    log_path = os.path.join(AppConfig.LOG_DIR, "app.log")
    app_manager.log_to_file("🚀 Starting Instagram Downloader API...", log_path)
    
    # Validate configuration
    app_manager.log_to_file("🔧 Validating configuration...", log_path)
    config_errors = AppConfig.validate_config()
    if config_errors:
        error_msg = "Configuration validation failed:\n" + "\n".join(config_errors)
        app_manager.log_to_file(f"❌ {error_msg}", log_path)
        raise RuntimeError(error_msg)
    
    # Log configuration summary
    config_summary = AppConfig.get_config_summary()
    app_manager.log_to_file(f"📋 Configuration: {config_summary}", log_path)
    
    # Check FFmpeg availability
    app_manager.log_to_file("🔧 Checking FFmpeg availability...", log_path)
    try:
        if verify_ffmpeg_installation():
            app_manager.log_to_file("✅ FFmpeg is available for audio extraction", log_path)
        else:
            app_manager.log_to_file("⚠️ FFmpeg not available - audio extraction will be disabled", log_path)
    except Exception as e:
        error_msg = f"❌ Error checking FFmpeg: {str(e)}"
        app_manager.log_to_file(error_msg, log_path)
        raise RuntimeError(error_msg)
    
    # Initialize services
    await app_manager.initialize_services()
    
    # Start background tasks
    await app_manager.start_background_tasks()
    
    app_manager.log_to_file("🎉 All services initialized successfully!", log_path)
    
    try:
        yield
    finally:
        # Shutdown - this will always run even if there's an exception
        try:
            app_manager.log_to_file("🛑 Application shutdown initiated...", log_path)
            await app_manager.shutdown()
            app_manager.log_to_file("✅ Application shutdown completed", log_path)
        except Exception as e:
            app_manager.log_to_file(f"❌ Error during shutdown: {str(e)}", log_path)
            # Force exit if graceful shutdown fails
            print(f"🔄 Force exiting due to shutdown error: {e}")
            os._exit(1)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application instance.
    """
    # Setup logging
    setup_logging()
    
    # Setup signal handlers
    setup_signal_handlers()

    app = FastAPI(
        title=AppConfig.APP_NAME,
        description="API for downloading Instagram and TikTok videos with audio extraction",
        version=AppConfig.APP_VERSION,
        debug=AppConfig.DEBUG,
        lifespan=lifespan
    )

    # Add logging middleware
    app.add_middleware(LoggingMiddleware)

    # CORS setup using configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=AppConfig.get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add exception handlers
    app.add_exception_handler(InstagramDownloaderError, handle_instagram_downloader_error)
    app.add_exception_handler(HTTPException, handle_http_exception)
    app.add_exception_handler(Exception, handle_generic_exception)

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
