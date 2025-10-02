from fastapi import APIRouter, HTTPException, Depends
from app.schemas import DownloadRequest, DownloadResponse
from app.services import InstagramService, TikTokService
from app.services.ffmpeg_utils import verify_ffmpeg_installation, get_ffmpeg_performance_info
from app.utils.url_validator import validate_url
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


@router.post("/download/", response_model=DownloadResponse)
async def download_video(
    request: DownloadRequest,
    ig_service: InstagramService = Depends(get_instagram_service),
    tt_service: TikTokService = Depends(get_tiktok_service),
) -> DownloadResponse:
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
        
        # Validate URL format and platform
        is_valid, platform, error_message = validate_url(request.url)
        if not is_valid:
            logger.warning("Invalid URL provided: %s - %s", request.url, error_message)
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid URL",
                    "message": error_message,
                    "supported_formats": [
                        "Instagram: https://www.instagram.com/p/... or https://www.instagram.com/reel/...",
                        "TikTok: https://www.tiktok.com/@user/video/... or https://vm.tiktok.com/..."
                    ]
                }
            )
        
        logger.info("URL validation successful. Platform: %s", platform)
        raw = str(request.url)
        lowered = raw.lower()
        
        # Determine platform and call appropriate service based on validation
        if platform == "instagram":
            logger.info("Processing Instagram URL with Instagram service")
            _, metadata = await ig_service.download_post(raw)
        elif platform == "tiktok":
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
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error("Download error: %s", e)
        message = str(e)
        
        # Map common authorization/private errors to a clear 403 response
        lowered_msg = message.lower()
        if any(key in lowered_msg for key in ["403", "authorization", "login", "private", "forbidden"]):
            raise HTTPException(status_code=403, detail="Видео недоступно: аккаунт приватный или требуется вход в Instagram")
        elif "timeout" in lowered_msg or "timed out" in lowered_msg:
            raise HTTPException(status_code=408, detail="Request timeout: попробуйте позже")
        elif "not found" in lowered_msg or "404" in lowered_msg:
            raise HTTPException(status_code=404, detail="Видео не найдено")
        else:
            raise HTTPException(status_code=500, detail="Failed to download content")


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
