from pydantic import BaseModel, HttpUrl, field_validator
import re

# Basic patterns to recognize supported platforms without over-restricting valid variations
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
    """

    url: HttpUrl

    @field_validator("url")
    @classmethod
    def validate_supported_url(cls, value: HttpUrl) -> HttpUrl:
        """
        Ensure the provided URL belongs to a supported platform (Instagram/TikTok)
        and points to a post-like or video resource.
        """
        raw = str(value)
        if INSTAGRAM_POST_REGEX.match(raw) or TIKTOK_POST_REGEX.match(raw):
            return value
        raise ValueError("URL must be a valid Instagram or TikTok video URL")
