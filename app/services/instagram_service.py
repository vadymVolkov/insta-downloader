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

class InstagramService:
    """
    Service for downloading Instagram posts and extracting metadata.
    """
    
    def __init__(self, media_dir: str = "app/media"):
        """
        Initialize the Instagram service with instaloader configuration.
        
        Args:
            media_dir: Directory to store downloaded media files
        """
        self.loader = instaloader.Instaloader(
            download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=True,
            compress_json=False
        )
        self.media_dir = Path(media_dir)
        self.media_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.logger.info("InstagramService initialized | media_dir=%s", str(self.media_dir))
        
        # Optional login if credentials are provided via environment variables.
        # Also support loading/saving a session file to reduce login frequency.
        username = os.getenv("INSTAGRAM_USERNAME")
        password = os.getenv("INSTAGRAM_PASSWORD")
        # Resolve session file to an absolute path in project root by default
        session_file_env = os.getenv("INSTALOADER_SESSION_FILE")
        default_root = Path(os.getenv("PROJECT_ROOT", Path.cwd()))
        session_path = Path(session_file_env) if session_file_env else (default_root / ".instaloader-session")
        session_path = session_path if session_path.is_absolute() else (default_root / session_path)
        if username:
            try:
                # Try to load session if it exists
                if session_path.exists():
                    self.logger.info("Loading Instagram session | user=%s, session_file=%s", username, str(session_path))
                    with open(session_path, "rb") as sf:
                        self.loader.context.load_session_from_file(username, sessionfile=sf)
                    self.logger.info("Session loaded successfully")
                elif password:
                    # Fallback to fresh login and save session for future runs
                    self.logger.info("Performing Instagram login | user=%s", username)
                    self.loader.login(username, password)
                    session_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(session_path, "wb") as sf:
                        self.loader.context.save_session_to_file(sessionfile=sf)
                    self.logger.info("Login successful, session saved | session_file=%s", str(session_path))
            except Exception as e:
                # Non-fatal: proceed unauthenticated; requests may fail for private/limited content
                self.logger.warning("Auth/session setup failed, proceeding unauthenticated | error=%s", str(e))
        else:
            if session_path.exists():
                self.logger.warning("INSTAGRAM_USERNAME is not set; cannot load session file at %s", str(session_path))
            else:
                self.logger.info("No INSTAGRAM_USERNAME provided, working unauthenticated")
        
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
                "video_url": f"http://localhost:8000/static/{target_mp4.name}",
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

            return target_mp4.name, metadata

        except (LoginRequiredException, QueryReturnedForbiddenException) as e:
            # Typical 403/authorization errors
            raise Exception("Instagram returned 403/authorization error. Provide credentials or a valid session.") from e
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
        return {
            "author": getattr(post, "owner_username", "unknown"),
            "description": description,
            "created_at": created_at,
            "video_url": f"http://localhost:8000/static/{target_mp4.name}",
        }
    
    # Comments extraction removed per requirements simplification
