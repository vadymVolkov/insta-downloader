from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class DownloadResponse(BaseModel):
    """
    Response payload for the download endpoint containing metadata, video URL, and audio URL.
    
    Attributes:
        author: Username of the post author
        description: Post caption or description text
        created_at: When the post was created
        video_url: Public URL to access the downloaded video
        audio_url: Public URL to access the extracted audio (if available)
    """

    author: str = Field(
        ...,
        description="Post author username",
        examples=["username", "creator123"]
    )
    description: Optional[str] = Field(
        None,
        description="Post caption/description",
        examples=["Check out this amazing video!", "Funny moment captured"]
    )
    created_at: datetime = Field(
        ...,
        description="Post creation timestamp in ISO format",
        examples=["2023-10-01T14:23:00"]
    )
    video_url: str = Field(
        ...,
        description="Public URL to the downloaded video file",
        examples=["http://localhost:8000/static/video123.mp4"]
    )
    audio_url: Optional[str] = Field(
        None,
        description="Public URL to the extracted audio file",
        examples=["http://localhost:8000/static/video123.mp3"]
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "author": "username",
                    "description": "Check out this amazing video!",
                    "created_at": "2023-10-01T14:23:00",
                    "video_url": "http://localhost:8000/static/video123.mp4",
                    "audio_url": "http://localhost:8000/static/video123.mp3"
                }
            ]
        }
    }
