from pydantic import BaseModel, HttpUrl, field_validator, Field
import re
from typing import Optional

# Enhanced patterns to recognize supported platforms with better validation
INSTAGRAM_POST_REGEX = re.compile(
    r"^https?://(www\.)?instagram\.com/(p|reel|tv)/[\w\-]+/?(\?.*)?$",
    re.IGNORECASE,
)

TIKTOK_POST_REGEX = re.compile(
    r"^https?://(www\.)?tiktok\.com/@[\w\.-]+/video/\d+/?(\?.*)?$|^https?://(vm|vt)\.tiktok\.com/[\w\-]+/?(\?.*)?$",
    re.IGNORECASE,
)


class DownloadRequest(BaseModel):
    """
    Request schema for the download endpoint, validating a supported media URL.
    Supports Instagram posts (p/reel/tv) and TikTok video links.
    
    Attributes:
        url: The URL of the video to download
    """

    url: str = Field(
        ...,
        description="URL of the Instagram or TikTok video to download",
        examples=[
            "https://www.instagram.com/reel/DPFJiwpDiBL/",
            "https://vm.tiktok.com/ZMAac7Uhm/",
            "https://www.tiktok.com/@user/video/1234567890"
        ]
    )

    # URL validation moved to router to return 200 with error JSON instead of 422
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "url": "https://www.instagram.com/reel/DPFJiwpDiBL/"
                },
                {
                    "url": "https://vm.tiktok.com/ZMAac7Uhm/"
                }
            ]
        }
    }
