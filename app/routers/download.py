from fastapi import APIRouter, HTTPException, Depends
from app.schemas import DownloadRequest, DownloadResponse
from app.services import InstagramService, TikTokService
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
    """
    try:
        logger.info("Processing download request for URL: %s", request.url)
        raw = str(request.url)
        lowered = raw.lower()
        if "instagram.com" in lowered:
            _, metadata = await ig_service.download_post(raw)
        elif "tiktok.com" in lowered:
            _, metadata = await tt_service.download_post(raw)
        else:
            raise ValueError("Unsupported platform. Provide Instagram or TikTok URL")
        # Ensure only the required fields are returned
        filtered = {
            "author": metadata.get("author"),
            "description": metadata.get("description"),
            "created_at": metadata.get("created_at"),
            "video_url": metadata.get("video_url"),
        }
        return DownloadResponse(**filtered)
    except ValueError as e:
        logger.warning("Validation error: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Download error: %s", e)
        message = str(e)
        # Map common authorization/private errors to a clear 403 response
        lowered_msg = message.lower()
        if any(key in lowered_msg for key in ["403", "authorization", "login", "private"]):
            raise HTTPException(status_code=403, detail="Видео недоступно: аккаунт приватный или требуется вход в Instagram")
        raise HTTPException(status_code=500, detail="Failed to download content")
