"""
Centralized exception handling for the Instagram Downloader API.
Provides custom exceptions and error handling utilities.
"""

from typing import Dict, Any, Optional
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class InstagramDownloaderError(Exception):
    """
    Base exception for Instagram Downloader API.
    """
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.details = details or {}
        super().__init__(self.message)


class ServiceError(InstagramDownloaderError):
    """
    Exception for service-related errors.
    """
    
    def __init__(self, service_name: str, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.service_name = service_name
        super().__init__(f"{service_name}: {message}", error_code, details)


class ConfigurationError(InstagramDownloaderError):
    """
    Exception for configuration-related errors.
    """
    
    def __init__(self, message: str, error_code: str = "CONFIG_ERROR", details: Dict[str, Any] = None):
        super().__init__(message, error_code, details)


class MediaProcessingError(InstagramDownloaderError):
    """
    Exception for media processing errors.
    """
    
    def __init__(self, message: str, error_code: str = "MEDIA_PROCESSING_ERROR", details: Dict[str, Any] = None):
        super().__init__(message, error_code, details)


class AudioExtractionError(MediaProcessingError):
    """
    Exception for audio extraction errors.
    """
    
    def __init__(self, message: str, error_code: str = "AUDIO_EXTRACTION_ERROR", details: Dict[str, Any] = None):
        super().__init__(message, error_code, details)


class VideoDownloadError(MediaProcessingError):
    """
    Exception for video download errors.
    """
    
    def __init__(self, message: str, error_code: str = "VIDEO_DOWNLOAD_ERROR", details: Dict[str, Any] = None):
        super().__init__(message, error_code, details)


class ValidationError(InstagramDownloaderError):
    """
    Exception for validation errors.
    """
    
    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR", details: Dict[str, Any] = None):
        super().__init__(message, error_code, details)


def create_error_response(
    status_code: int,
    message: str,
    error_code: str = None,
    details: Dict[str, Any] = None
) -> JSONResponse:
    """
    Create a standardized error response.
    """
    error_data = {
        "error": {
            "message": message,
            "code": error_code or "UNKNOWN_ERROR",
            "details": details or {}
        },
        "status": "error"
    }
    
    return JSONResponse(
        status_code=status_code,
        content=error_data
    )


def handle_instagram_downloader_error(request: Request, exc: InstagramDownloaderError) -> JSONResponse:
    """
    Handle InstagramDownloaderError exceptions.
    """
    logger.error(
        f"InstagramDownloaderError: {exc.message}",
        extra={
            "error_code": exc.error_code,
            "details": exc.details,
            "path": str(request.url.path),
            "method": request.method
        }
    )
    
    # Map error codes to HTTP status codes
    status_code_map = {
        "CONFIG_ERROR": 500,
        "VALIDATION_ERROR": 400,
        "MEDIA_PROCESSING_ERROR": 422,
        "AUDIO_EXTRACTION_ERROR": 422,
        "VIDEO_DOWNLOAD_ERROR": 422,
        "SERVICE_ERROR": 503,
        "UNKNOWN_ERROR": 500
    }
    
    status_code = status_code_map.get(exc.error_code, 500)
    
    return create_error_response(
        status_code=status_code,
        message=exc.message,
        error_code=exc.error_code,
        details=exc.details
    )


def handle_generic_exception(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle generic exceptions.
    """
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "exception_type": type(exc).__name__,
            "path": str(request.url.path),
            "method": request.method
        },
        exc_info=True
    )
    
    return create_error_response(
        status_code=500,
        message="Internal server error",
        error_code="INTERNAL_ERROR",
        details={"exception_type": type(exc).__name__}
    )


def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle FastAPI HTTPException.
    """
    logger.warning(
        f"HTTPException: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": str(request.url.path),
            "method": request.method
        }
    )
    
    return create_error_response(
        status_code=exc.status_code,
        message=str(exc.detail),
        error_code="HTTP_ERROR"
    )
