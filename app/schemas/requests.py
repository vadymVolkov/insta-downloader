from pydantic import BaseModel, HttpUrl, field_validator
import re

INSTAGRAM_POST_REGEX = re.compile(
    r"^https?://(www\.)?instagram\.com/(p|reel|tv)/[\w\-]+/?(\?.*)?$",
    re.IGNORECASE,
)

class DownloadRequest(BaseModel):
    """
    Request schema for the download endpoint, validating the Instagram post URL.
    """

    url: HttpUrl

    @field_validator("url")
    @classmethod
    def validate_instagram_url(cls, value: HttpUrl) -> HttpUrl:
        """
        Ensure the provided URL belongs to Instagram and points to a post-like resource.
        Accepts /p/, /reel/, or /tv/ paths; rejects others.
        """
        if not INSTAGRAM_POST_REGEX.match(str(value)):
            raise ValueError("URL must be a valid Instagram post/reel/tv URL")
        return value
