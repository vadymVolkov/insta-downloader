"""
Configuration settings for the Instagram Downloader API.
Provides centralized configuration management with validation and environment variable support.
"""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class AudioConfig:
    """Configuration for audio file management."""
    
    # Maximum number of audio files to keep (default: 10)
    MAX_AUDIO_FILES: int = int(os.getenv("MAX_AUDIO_FILES", "10"))
    
    # Audio cleanup interval in seconds (default: 3600 = 1 hour)
    AUDIO_CLEANUP_INTERVAL: int = int(os.getenv("AUDIO_CLEANUP_INTERVAL", "3600"))
    
    # Enable/disable automatic audio cleanup after extraction
    AUTO_CLEANUP_AFTER_EXTRACTION: bool = os.getenv("AUTO_CLEANUP_AFTER_EXTRACTION", "true").lower() == "true"
    
    # Enable/disable scheduled audio cleanup
    ENABLE_SCHEDULED_CLEANUP: bool = os.getenv("ENABLE_SCHEDULED_CLEANUP", "true").lower() == "true"
    
    # Audio quality settings
    AUDIO_BITRATE: str = os.getenv("AUDIO_BITRATE", "192k")
    AUDIO_SAMPLE_RATE: int = int(os.getenv("AUDIO_SAMPLE_RATE", "44100"))
    AUDIO_CHANNELS: int = int(os.getenv("AUDIO_CHANNELS", "2"))


class VideoConfig:
    """Configuration for video file management."""
    
    # Maximum number of video files to keep (default: 10)
    MAX_VIDEO_FILES: int = int(os.getenv("MAX_VIDEO_FILES", "10"))
    
    # Video quality settings
    VIDEO_QUALITY: str = os.getenv("VIDEO_QUALITY", "best")
    VIDEO_FORMAT: str = os.getenv("VIDEO_FORMAT", "mp4")


class LoggingConfig:
    """Configuration for logging settings."""
    
    # Log level
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Log format
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # Enable/disable console logging
    ENABLE_CONSOLE_LOGGING: bool = os.getenv("ENABLE_CONSOLE_LOGGING", "false").lower() == "true"
    
    # Enable/disable file logging
    ENABLE_FILE_LOGGING: bool = os.getenv("ENABLE_FILE_LOGGING", "true").lower() == "true"


class AppConfig:
    """Main application configuration."""
    
    # Base URL for the application
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")
    
    # Log directory
    LOG_DIR: str = os.getenv("LOG_DIR", "logs")
    
    # Media directory
    MEDIA_DIR: str = os.getenv("MEDIA_DIR", "app/media")
    
    # Application settings
    APP_NAME: str = os.getenv("APP_NAME", "Instagram Downloader API")
    APP_VERSION: str = os.getenv("APP_VERSION", "0.1.0")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # API settings
    API_PREFIX: str = os.getenv("API_PREFIX", "/api")
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost,http://127.0.0.1")
    
    # Audio configuration
    AUDIO = AudioConfig()
    
    # Video configuration
    VIDEO = VideoConfig()
    
    # Logging configuration
    LOGGING = LoggingConfig()
    
    @classmethod
    def get_cors_origins(cls) -> list:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in cls.CORS_ORIGINS.split(",")]
    
    @classmethod
    def validate_config(cls) -> list:
        """
        Validate configuration values and return list of validation errors.
        
        Returns:
            list: List of validation error messages
        """
        errors = []
        
        # Validate audio config
        if cls.AUDIO.MAX_AUDIO_FILES < 1:
            errors.append("MAX_AUDIO_FILES must be at least 1")
        
        if cls.AUDIO.AUDIO_CLEANUP_INTERVAL < 60:
            errors.append("AUDIO_CLEANUP_INTERVAL must be at least 60 seconds")
        
        if cls.AUDIO.AUDIO_SAMPLE_RATE not in [22050, 44100, 48000]:
            errors.append("AUDIO_SAMPLE_RATE must be 22050, 44100, or 48000")
        
        if cls.AUDIO.AUDIO_CHANNELS not in [1, 2]:
            errors.append("AUDIO_CHANNELS must be 1 (mono) or 2 (stereo)")
        
        # Validate video config
        if cls.VIDEO.MAX_VIDEO_FILES < 1:
            errors.append("MAX_VIDEO_FILES must be at least 1")
        
        # Validate base URL
        if not cls.BASE_URL.startswith(("http://", "https://")):
            errors.append("BASE_URL must start with http:// or https://")
        
        # Validate directories
        try:
            Path(cls.LOG_DIR).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot create log directory {cls.LOG_DIR}: {str(e)}")
        
        try:
            Path(cls.MEDIA_DIR).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot create media directory {cls.MEDIA_DIR}: {str(e)}")
        
        return errors
    
    @classmethod
    def get_config_summary(cls) -> Dict[str, Any]:
        """
        Get a summary of current configuration for debugging.
        
        Returns:
            Dict containing configuration summary
        """
        return {
            "app": {
                "name": cls.APP_NAME,
                "version": cls.APP_VERSION,
                "debug": cls.DEBUG,
                "base_url": cls.BASE_URL
            },
            "audio": {
                "max_files": cls.AUDIO.MAX_AUDIO_FILES,
                "cleanup_interval": cls.AUDIO.AUDIO_CLEANUP_INTERVAL,
                "auto_cleanup": cls.AUDIO.AUTO_CLEANUP_AFTER_EXTRACTION,
                "scheduled_cleanup": cls.AUDIO.ENABLE_SCHEDULED_CLEANUP,
                "bitrate": cls.AUDIO.AUDIO_BITRATE,
                "sample_rate": cls.AUDIO.AUDIO_SAMPLE_RATE,
                "channels": cls.AUDIO.AUDIO_CHANNELS
            },
            "video": {
                "max_files": cls.VIDEO.MAX_VIDEO_FILES,
                "quality": cls.VIDEO.VIDEO_QUALITY,
                "format": cls.VIDEO.VIDEO_FORMAT
            },
            "logging": {
                "level": cls.LOGGING.LOG_LEVEL,
                "console": cls.LOGGING.ENABLE_CONSOLE_LOGGING,
                "file": cls.LOGGING.ENABLE_FILE_LOGGING
            }
        }
