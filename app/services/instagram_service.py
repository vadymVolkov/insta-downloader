import instaloader
from instaloader.exceptions import (
    InstaloaderException,
    LoginRequiredException,
    QueryReturnedForbiddenException,
)
import logging
import os
from datetime import datetime
from typing import Dict, Tuple, Any, Optional
from pathlib import Path
import json
import httpx
from .base_service import BaseService
from app.config import AppConfig
from app.utils.logger import get_service_logger
from app.utils.exceptions import ServiceError, VideoDownloadError

class InstagramService(BaseService):
    """
    Service for downloading Instagram posts and extracting metadata.
    """
    
    def __init__(self, media_dir: str = "app/media"):
        """
        Initialize the Instagram service with instaloader configuration.
        
        Args:
            media_dir: Directory to store downloaded media files
        """
        # Initialize base service
        super().__init__(media_dir, max_files=10)
        
        # Initialize service logger
        self.logger = get_service_logger("instagram")
        
        self.loader = instaloader.Instaloader(
            download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=True,
            compress_json=False
        )
        
        # Session-based authentication
        self._setup_session_auth()
        
        self.logger.log_service_status("initialized", media_dir=str(self.media_dir))
    
    def _setup_session_auth(self):
        """
        Setup Instagram authentication using session file.
        Attempts to load existing session from .instaloader-session file.
        """
        # Path to session file in project root
        project_root = Path(__file__).parent.parent.parent
        session_file = project_root / ".instaloader-session"
        
        self.logger.info("🔐 Starting Instagram authentication process...")
        self.logger.info("📁 Session file path", session_file=str(session_file))
        
        # Check if session file exists
        if not session_file.exists():
            self.logger.warning("⚠️  Session file not found", session_file=str(session_file))
            self.logger.info("❌ Authentication failed: No session file available")
            self.logger.info("💡 Working in unauthenticated mode - some content may be inaccessible")
            return
        
        # Check if session file is readable
        if not session_file.is_file():
            self.logger.error("❌ Authentication failed: Session file is not a regular file")
            return
        
        # Check file size
        try:
            file_size = session_file.stat().st_size
            self.logger.info("📊 Session file size", file_size_bytes=file_size)
            if file_size == 0:
                self.logger.warning("⚠️  Session file is empty")
                self.logger.info("❌ Authentication failed: Empty session file")
                return
        except Exception as e:
            self.logger.error("❌ Authentication failed: Cannot read session file", error=str(e))
            return
        
        # Try to load session
        try:
            self.logger.info("🔄 Attempting to load Instagram session...")
            
            # Get username from environment or use default
            username = os.getenv("INSTAGRAM_USERNAME", "default_user")
            self.logger.info("👤 Loading session for user", username=username)
            
            with open(session_file, "rb") as sf:
                self.loader.context.load_session_from_file(username, sessionfile=sf)
            
            self.logger.info("✅ Instagram authentication successful!")
            self.logger.info("🎉 Session loaded successfully for user", username=username)
            self.logger.info("🚀 Ready to download Instagram content")
            
        except Exception as e:
            self.logger.error("❌ Authentication failed: Cannot load session", error=str(e))
            self.logger.warning("⚠️  Session file may be corrupted or invalid")
            self.logger.info("💡 Working in unauthenticated mode - some content may be inaccessible")
    
    def extract_shortcode_from_url(self, url: str) -> str:
        """
        Extract the shortcode from an Instagram URL.
        
        Args:
            url: Instagram post URL
            
        Returns:
            Post shortcode
            
        Raises:
            ValueError: If shortcode cannot be extracted
        """
        # Remove trailing slash and split by '/'
        parts = url.strip("/").split("/")
        
        # Find 'p', 'reel', or 'tv' in the URL
        for i, part in enumerate(parts):
            if part in ["p", "reel", "tv"] and i + 1 < len(parts):
                return parts[i + 1]
        
        raise ValueError("Could not extract shortcode from URL")
        
    async def download_post(self, url: str) -> Tuple[str, Dict[str, Any]]:
        """
        Download a post and return the file path and metadata.
        
        Args:
            url: Instagram post URL
            
        Returns:
            Tuple of (filename, metadata_dict)
            
        Raises:
            Exception: If download fails
        """
        try:
            # Extract shortcode and load the post metadata first
            shortcode = self.extract_shortcode_from_url(url)
            post = instaloader.Post.from_shortcode(self.loader.context, shortcode)

            # Ensure it is a video
            if not post.is_video:
                raise ValueError("The provided URL does not contain a video")

            # Choose a stable unique identifier for filenames (mediaid is globally unique)
            unique_id = str(post.mediaid)

            # Target file paths based on unique_id
            target_mp4 = self.media_dir / f"{unique_id}.mp4"
            target_json = self.media_dir / f"{unique_id}.json"
            target_txt = self.media_dir / f"{unique_id}.txt"

            # Fast path: if already downloaded, return cached metadata
            if target_mp4.exists():
                metadata = self._build_metadata_from_files(
                    post=post,
                    unique_id=unique_id,
                    target_mp4=target_mp4,
                    target_txt=target_txt,
                )
                return target_mp4.name, metadata

            # Download video directly from the post's video_url to avoid filename heuristics
            video_url = getattr(post, "video_url", None)
            if not video_url:
                raise Exception("Could not resolve video URL from the post")

            # Stream download to a temp file, then atomically move to target
            temp_path = self.media_dir / f"{unique_id}.mp4.part"
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
                async with client.stream("GET", video_url) as resp:
                    resp.raise_for_status()
                    with open(temp_path, "wb") as fp:
                        async for chunk in resp.aiter_bytes(chunk_size=1024 * 64):
                            if not chunk:
                                continue
                            fp.write(chunk)
            # Ensure file is non-empty and move into place
            if not temp_path.exists() or temp_path.stat().st_size == 0:
                try:
                    temp_path.unlink()
                except Exception:
                    pass
                raise Exception("Downloaded video file is empty or missing")
            try:
                temp_path.replace(target_mp4)
            except Exception:
                # Fallback copy
                data = temp_path.read_bytes()
                target_mp4.write_bytes(data)
                try:
                    temp_path.unlink()
                except Exception:
                    pass

            # Persist caption and metadata for idempotent reads
            try:
                target_txt.write_text(post.caption or "")
            except Exception:
                pass

            metadata = {
                "author": post.owner_username,
                "description": post.caption or "",
                "created_at": post.date,
                "video_url": f"{AppConfig.BASE_URL}/static/{target_mp4.name}",
            }
            try:
                target_json.write_text(json.dumps({
                    "shortcode": post.shortcode,
                    "mediaid": unique_id,
                    "owner_username": post.owner_username,
                    "date": post.date.isoformat(),
                    "caption": post.caption or "",
                }, ensure_ascii=False))
            except Exception:
                pass

            # Extract audio from video after successful download
            audio_extracted, audio_url = self._extract_audio_from_video(target_mp4)
            
            # Add audio URL to metadata if extraction was successful
            if audio_extracted:
                metadata["audio_url"] = audio_url
            else:
                metadata["audio_url"] = None
            
            # Clean up old files after successful download
            self._cleanup_old_files()
            
            return target_mp4.name, metadata

        except (LoginRequiredException, QueryReturnedForbiddenException) as e:
            # Typical 403/authorization errors
            raise Exception("Instagram returned 403/authorization error. The content may be private or restricted.") from e
        except InstaloaderException as e:
            # Other instaloader-level errors
            raise Exception("Fetching Post metadata failed. The URL may be invalid/private or rate-limited.") from e
        except Exception as e:
            raise Exception(f"Error downloading Instagram post: {str(e)}")

    def _build_metadata_from_files(self, post: "instaloader.Post", unique_id: str, target_mp4: Path, target_txt: Path) -> Dict[str, Any]:
        """
        Build a consistent metadata dict from saved files and post fields.

        This is used both for the cached-return path and right after download.
        """
        description = ""
        try:
            if target_txt.exists():
                description = target_txt.read_text(errors="ignore").strip()
        except Exception:
            description = ""
        
        created_at = post.date if hasattr(post, "date") else datetime.fromtimestamp(target_mp4.stat().st_mtime)
        author = getattr(post, "owner_username", "unknown")
        
        return self._build_metadata_with_audio(author, description, target_mp4, created_at)
    
    # Comments extraction removed per requirements simplification
