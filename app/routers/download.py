from fastapi import APIRouter, HTTPException, Depends
from app.schemas import DownloadRequest, DownloadResponse, ErrorResponse
from app.services import InstagramService, TikTokService
from app.services.ffmpeg_utils import verify_ffmpeg_installation, get_ffmpeg_performance_info
from app.utils.url_validator import validate_url
from typing import Union
import logging

router = APIRouter(prefix="/api", tags=["download"])
logger = logging.getLogger(__name__)


def get_instagram_service() -> InstagramService:
    """
    Provide InstagramService instance as a dependency.
    """
    return InstagramService()

def get_tiktok_service() -> TikTokService:
    """
    Provide TikTokService instance as a dependency.
    """
    return TikTokService()


@router.post("/download/", response_model=Union[DownloadResponse, ErrorResponse])
async def download_video(
    request: DownloadRequest,
    ig_service: InstagramService = Depends(get_instagram_service),
    tt_service: TikTokService = Depends(get_tiktok_service),
) -> Union[DownloadResponse, ErrorResponse]:
    """
    Download video by URL from supported platforms (Instagram/TikTok) and
    return normalized metadata with a public video URL.
    
    Args:
        request: Download request containing the video URL
        ig_service: Instagram service dependency
        tt_service: TikTok service dependency
        
    Returns:
        DownloadResponse with video metadata and URLs
        
    Raises:
        HTTPException: For various error conditions with appropriate status codes
    """
    try:
        logger.info("Processing download request for URL: %s", request.url)
        
        # Manual URL validation to return 200 with error JSON instead of 422
        raw = str(request.url)
        lowered = raw.lower()
        
        # First check if it's a valid URL format
        if not (raw.startswith('http://') or raw.startswith('https://')):
            return ErrorResponse(
                error="Invalid URL format",
                error_code="INVALID_URL",
                details="URL must start with http:// or https://"
            )
        
        # Check if URL is supported platform
        from app.schemas.requests import INSTAGRAM_POST_REGEX, TIKTOK_POST_REGEX
        if not (INSTAGRAM_POST_REGEX.match(raw) or TIKTOK_POST_REGEX.match(raw)):
            return ErrorResponse(
                error="Unsupported URL format",
                error_code="INVALID_URL_FORMAT",
                details="URL must be a valid Instagram post/reel or TikTok video link"
            )
        
        # Determine platform and call appropriate service
        if "instagram.com" in lowered:
            logger.info("Processing Instagram URL with Instagram service")
            _, metadata = await ig_service.download_post(raw)
        elif "tiktok.com" in lowered or "vm.tiktok.com" in lowered or "vt.tiktok.com" in lowered:
            logger.info("Processing TikTok URL with TikTok service")
            _, metadata = await tt_service.download_post(raw)
        else:
            raise ValueError("Unsupported platform. Provide Instagram or TikTok URL")
        
        # Validate required fields are present
        required_fields = ["author", "created_at", "video_url"]
        for field in required_fields:
            if field not in metadata:
                logger.error(f"Missing required field '{field}' in metadata")
                raise HTTPException(status_code=500, detail=f"Missing required field: {field}")
        
        # Ensure only the required fields are returned
        filtered = {
            "author": metadata.get("author"),
            "description": metadata.get("description"),
            "created_at": metadata.get("created_at"),
            "video_url": metadata.get("video_url"),
            "audio_url": metadata.get("audio_url"),
        }
        
        logger.info("Download completed successfully for URL: %s", request.url)
        return DownloadResponse(**filtered)
        
    except ValueError as e:
        logger.warning("Validation error: %s", e)
        return ErrorResponse(
            error=str(e),
            error_code="INVALID_URL",
            details="The provided URL is not valid or not supported"
        )
    except Exception as e:
        logger.error("Download error: %s", e)
        message = str(e)
        
        # Map common errors to appropriate error responses
        lowered_msg = message.lower()
        if any(key in lowered_msg for key in ["403", "authorization", "login", "private", "forbidden"]):
            return ErrorResponse(
                error="Account is private",
                error_code="PRIVATE_ACCOUNT",
                details="The Instagram account is private or requires login"
            )
        elif "timeout" in lowered_msg or "timed out" in lowered_msg:
            return ErrorResponse(
                error="Request timeout",
                error_code="TIMEOUT",
                details="The request timed out, please try again later"
            )
        elif "not found" in lowered_msg or "404" in lowered_msg or "fetching post metadata failed" in lowered_msg:
            return ErrorResponse(
                error="Post not found",
                error_code="POST_NOT_FOUND",
                details="The Instagram post may have been deleted or the URL is incorrect"
            )
        else:
            return ErrorResponse(
                error="Download failed",
                error_code="DOWNLOAD_ERROR",
                details=f"Failed to download content: {message}"
            )


@router.get("/health/")
async def health_check():
    """
    Health check endpoint to verify service status and dependencies.
    
    Returns:
        Dict containing service status and dependency information
    """
    try:
        from app.config import AppConfig
        from app.main import app_manager
        
        # Check FFmpeg availability
        ffmpeg_available = verify_ffmpeg_installation()
        ffmpeg_info = get_ffmpeg_performance_info()
        
        # Get configuration summary
        config_summary = AppConfig.get_config_summary()
        
        # Get service status from application manager
        service_status = app_manager.get_service_status()
        
        return {
            "status": "healthy",
            "app": {
                "name": AppConfig.APP_NAME,
                "version": AppConfig.APP_VERSION,
                "debug": AppConfig.DEBUG
            },
            "services": {
                "instagram": "available" if service_status["instagram_service"] == "initialized" else "unavailable",
                "tiktok": "available" if service_status["tiktok_service"] == "initialized" else "unavailable",
                "ffmpeg": "available" if ffmpeg_available else "unavailable",
                "cleanup_task": service_status["cleanup_task"]
            },
            "ffmpeg_info": ffmpeg_info,
            "configuration": config_summary
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "app": {
                "name": "Instagram Downloader API",
                "version": "0.1.0"
            }
        }
