from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class DownloadResponse(BaseModel):
    """
    Response payload for the download endpoint containing metadata and video URL.
    """

    author: str = Field(..., description="Post author username")
    description: Optional[str] = Field(None, description="Post caption/description")
    created_at: datetime = Field(..., description="Post creation timestamp in ISO format")
    video_url: str = Field(..., description="Public URL to the downloaded video file")
