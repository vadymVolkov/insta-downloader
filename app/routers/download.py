from fastapi import APIRouter, HTTPException, Depends
from app.schemas import DownloadRequest, DownloadResponse
from app.services import InstagramService
import logging

router = APIRouter(prefix="/api", tags=["download"])
logger = logging.getLogger(__name__)


def get_instagram_service() -> InstagramService:
    """
    Provide InstagramService instance as a dependency.
    """
    return InstagramService()


@router.post("/download/", response_model=DownloadResponse)
async def download_instagram_video(request: DownloadRequest, service: InstagramService = Depends(get_instagram_service)) -> DownloadResponse:
    """
    Download Instagram video by URL and return metadata with public video URL.
    """
    try:
        logger.info("Processing download request for URL: %s", request.url)
        _, metadata = await service.download_post(str(request.url))
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
        lowered = message.lower()
        if any(key in lowered for key in ["403", "authorization", "login", "private"]):
            raise HTTPException(status_code=403, detail="Видео недоступно: аккаунт приватный или требуется вход в Instagram")
        raise HTTPException(status_code=500, detail="Failed to download Instagram content")
