"""
URL validation utilities for Instagram and TikTok links.
Validates that URLs are legitimate social media post/reel links.
"""

import re
from typing import Tuple, Optional
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

# Instagram URL patterns
INSTAGRAM_PATTERNS = [
    r'https?://(?:www\.)?instagram\.com/p/[A-Za-z0-9_-]+/?',
    r'https?://(?:www\.)?instagram\.com/reel/[A-Za-z0-9_-]+/?',
    r'https?://(?:www\.)?instagram\.com/tv/[A-Za-z0-9_-]+/?',
]

# TikTok URL patterns
TIKTOK_PATTERNS = [
    r'https?://(?:www\.)?tiktok\.com/@[A-Za-z0-9_.-]+/video/\d+/?',
    r'https?://(?:www\.)?vm\.tiktok\.com/[A-Za-z0-9]+/?',
    r'https?://(?:www\.)?vt\.tiktok\.com/[A-Za-z0-9]+/?',
    r'https?://(?:www\.)?m\.tiktok\.com/v/\d+/?',
]

def validate_url(url: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate if URL is a legitimate Instagram or TikTok post/reel link.
    
    Args:
        url: URL to validate
        
    Returns:
        Tuple of (is_valid, platform, error_message)
        - is_valid: True if URL is valid
        - platform: 'instagram' or 'tiktok' if valid, None otherwise
        - error_message: Error description if invalid, None if valid
    """
    if not url or not isinstance(url, str):
        return False, None, "URL is required and must be a string"
    
    # Clean and normalize URL
    url = url.strip()
    if not url:
        return False, None, "URL cannot be empty"
    
    # Check if URL starts with http/https
    if not url.startswith(('http://', 'https://')):
        return False, None, "URL must start with http:// or https://"
    
    # Parse URL to check basic structure
    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return False, None, "Invalid URL format"
    except Exception as e:
        return False, None, f"Invalid URL format: {str(e)}"
    
    # Check Instagram patterns
    for pattern in INSTAGRAM_PATTERNS:
        if re.match(pattern, url, re.IGNORECASE):
            logger.info("Valid Instagram URL detected: %s", url)
            return True, 'instagram', None
    
    # Check TikTok patterns
    for pattern in TIKTOK_PATTERNS:
        if re.match(pattern, url, re.IGNORECASE):
            logger.info("Valid TikTok URL detected: %s", url)
            return True, 'tiktok', None
    
    # If no patterns matched, it's not a supported URL
    logger.warning("Unsupported URL format: %s", url)
    return False, None, "URL must be a valid Instagram post/reel or TikTok video link"

def get_platform_from_url(url: str) -> Optional[str]:
    """
    Get platform name from URL without full validation.
    
    Args:
        url: URL to analyze
        
    Returns:
        Platform name ('instagram' or 'tiktok') or None if not supported
    """
    is_valid, platform, _ = validate_url(url)
    return platform if is_valid else None

def is_instagram_url(url: str) -> bool:
    """
    Check if URL is an Instagram link.
    
    Args:
        url: URL to check
        
    Returns:
        True if URL is Instagram, False otherwise
    """
    is_valid, platform, _ = validate_url(url)
    return is_valid and platform == 'instagram'

def is_tiktok_url(url: str) -> bool:
    """
    Check if URL is a TikTok link.
    
    Args:
        url: URL to check
        
    Returns:
        True if URL is TikTok, False otherwise
    """
    is_valid, platform, _ = validate_url(url)
    return is_valid and platform == 'tiktok'

def validate_and_get_platform(url: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate URL and return platform information.
    This is an alias for validate_url for backward compatibility.
    
    Args:
        url: URL to validate
        
    Returns:
        Tuple of (is_valid, platform, error_message)
    """
    return validate_url(url)
