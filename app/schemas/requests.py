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

    url: HttpUrl = Field(
        ...,
        description="URL of the Instagram or TikTok video to download",
        examples=[
            "https://www.instagram.com/reel/DPFJiwpDiBL/",
            "https://vm.tiktok.com/ZMAac7Uhm/",
            "https://www.tiktok.com/@user/video/1234567890"
        ]
    )

    @field_validator("url")
    @classmethod
    def validate_supported_url(cls, value: HttpUrl) -> HttpUrl:
        """
        Ensure the provided URL belongs to a supported platform (Instagram/TikTok)
        and points to a post-like or video resource.
        
        Args:
            value: The URL to validate
            
        Returns:
            The validated URL
            
        Raises:
            ValueError: If the URL is not supported
        """
        raw = str(value)
        if INSTAGRAM_POST_REGEX.match(raw) or TIKTOK_POST_REGEX.match(raw):
            return value
        raise ValueError("URL must be a valid Instagram or TikTok video URL")
    
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
