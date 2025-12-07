import instaloader
from instaloader.exceptions import (
    InstaloaderException,
    LoginRequiredException,
    QueryReturnedForbiddenException,
)
import logging
import os
from datetime import datetime
from typing import Dict, Tuple, Any, Optional, List
from pathlib import Path
import json
import httpx
import uuid
import ffmpeg
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
        self.logger.info(f"📁 Session file path: {session_file}")
        
        # Check if session file exists
        if not session_file.exists():
            self.logger.warning(f"⚠️  Session file not found: {session_file}")
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
            self.logger.info(f"📊 Session file size: {file_size} bytes")
            if file_size == 0:
                self.logger.warning("⚠️  Session file is empty")
                self.logger.info("❌ Authentication failed: Empty session file")
                return
        except Exception as e:
            self.logger.error(f"❌ Authentication failed: Cannot read session file: {str(e)}")
            return
        
        # Try to load session
        try:
            self.logger.info("🔄 Attempting to load Instagram session...")
            
            # Get username from environment or use default
            username = os.getenv("INSTAGRAM_USERNAME", "default_user")
            self.logger.info(f"👤 Loading session for user: {username}")
            
            with open(session_file, "rb") as sf:
                self.loader.context.load_session_from_file(username, sessionfile=sf)
            
            self.logger.info("✅ Instagram authentication successful!")
            self.logger.info(f"🎉 Session loaded successfully for user: {username}")
            self.logger.info("🚀 Ready to download Instagram content")
            
        except Exception as e:
            self.logger.error(f"❌ Authentication failed: Cannot load session: {str(e)}")
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
    
    def determine_post_type(self, url: str) -> str:
        """
        Determine the type of Instagram post (video, carousel, or image).
        
        Args:
            url: Instagram post URL
            
        Returns:
            Post type: 'video', 'carousel', or 'image'
            
        Raises:
            Exception: If post type cannot be determined
        """
        try:
            # Extract shortcode and load the post metadata
            shortcode = self.extract_shortcode_from_url(url)
            post = instaloader.Post.from_shortcode(self.loader.context, shortcode)

            typename = getattr(post, "typename", None)
            self.logger.info(f"Post metadata: is_video={post.is_video}, typename={typename}")
            
            # Check if it's a video
            if post.is_video:
                return "video"
            
            # Check if it's a carousel (multiple media items)
            # Prefer generator API when available
            try:
                get_nodes = getattr(post, "get_sidecar_nodes", None)
                if callable(get_nodes):
                    nodes_list = list(get_nodes())
                    if nodes_list:
                        self.logger.info(f"Detected carousel via get_sidecar_nodes with {len(nodes_list)} items")
                        return "carousel"
            except Exception as _:
                pass

            # Fallbacks: attribute presence or typename
            sidecar_nodes = getattr(post, 'sidecar_nodes', None)
            if sidecar_nodes:
                try:
                    length = len(sidecar_nodes)
                except Exception:
                    length = 1
                if length >= 1:
                    self.logger.info(f"Detected carousel via sidecar_nodes (len={length})")
                    return "carousel"
            if typename and str(typename).lower() == "graphsidecar":
                self.logger.info("Detected carousel via typename GraphSidecar")
                return "carousel"
            
            # If it's not a video and not a carousel, it's a single image
            return "image"
            
        except Exception as e:
            self.logger.error(f"Failed to determine post type: {str(e)}")
            raise Exception(f"Could not determine Instagram post type: {str(e)}")
    
    async def download_carousel_images(self, url: str) -> List[Path]:
        """
        Download all images from an Instagram carousel post.
        
        Args:
            url: Instagram post URL
            
        Returns:
            List of downloaded image file paths
            
        Raises:
            Exception: If download fails
        """
        try:
            shortcode = self.extract_shortcode_from_url(url)
            post = instaloader.Post.from_shortcode(self.loader.context, shortcode)

            nodes_list: List[Any] = []
            get_nodes = getattr(post, "get_sidecar_nodes", None)
            if callable(get_nodes):
                try:
                    nodes_list = list(get_nodes())
                except Exception as e:
                    self.logger.warning(f"Failed to enumerate get_sidecar_nodes: {str(e)}")

            if not nodes_list:
                fallback_nodes = getattr(post, 'sidecar_nodes', None)
                if fallback_nodes:
                    try:
                        nodes_list = list(fallback_nodes)
                    except Exception:
                        nodes_list = [fallback_nodes]

            if not nodes_list:
                raise Exception("Post is not a carousel (no sidecar nodes found)")

            self.logger.info(f"Processing carousel with {len(nodes_list)} items")
            
            image_paths = []
            unique_id = str(post.mediaid)
            
            for i, node in enumerate(nodes_list):
                is_video = getattr(node, "is_video", False)
                self.logger.info(f"Processing carousel item {i+1}/{len(nodes_list)}: is_video={is_video}")
                
                if not is_video:  # Only process images, skip videos in carousel
                    try:
                        # Download image
                        image_filename = f"{unique_id}_carousel_{i}.jpg"
                        image_path = self.media_dir / image_filename
                        
                        # Get the image URL - try different possible attributes
                        image_url = getattr(node, 'display_url', None) or getattr(node, 'url', None)
                        if not image_url:
                            self.logger.warning(f"No image URL found for carousel item {i+1}")
                            continue
                        
                        self.logger.info(f"Downloading image from URL: {image_url}")
                        
                        # Download image using httpx
                        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
                            async with client.stream("GET", image_url) as resp:
                                resp.raise_for_status()
                                with open(image_path, "wb") as fp:
                                    async for chunk in resp.aiter_bytes(chunk_size=1024 * 64):
                                        if not chunk:
                                            continue
                                        fp.write(chunk)
                        
                        if image_path.exists() and image_path.stat().st_size > 0:
                            image_paths.append(image_path)
                            size_bytes = image_path.stat().st_size
                            self.logger.info(f"Downloaded carousel image {i+1}/{len(nodes_list)}: {image_path}, size: {size_bytes} bytes")
                        else:
                            self.logger.warning(f"Failed to download carousel image {i+1} - file is empty or missing")
                            
                    except Exception as e:
                        self.logger.warning(f"Failed to download carousel image {i+1}: {str(e)}")
                        continue
                else:
                    self.logger.info(f"Skipping video item {i+1} in carousel")
            
            if not image_paths:
                raise Exception("No images could be downloaded from carousel")
            
            self.logger.info(f"Successfully downloaded {len(image_paths)} carousel images")
            return image_paths
            
        except Exception as e:
            self.logger.error(f"Failed to download carousel images: {str(e)}")
            raise Exception(f"Could not download carousel images: {str(e)}")
    
    async def download_single_image(self, url: str) -> Path:
        """
        Download a single image from an Instagram post.
        
        Args:
            url: Instagram post URL
            
        Returns:
            Downloaded image file path
            
        Raises:
            Exception: If download fails
        """
        try:
            shortcode = self.extract_shortcode_from_url(url)
            post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
            
            unique_id = str(post.mediaid)
            image_filename = f"{unique_id}_single.jpg"
            image_path = self.media_dir / image_filename
            
            # Download image using httpx
            async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
                async with client.stream("GET", post.url) as resp:
                    resp.raise_for_status()
                    with open(image_path, "wb") as fp:
                        async for chunk in resp.aiter_bytes(chunk_size=1024 * 64):
                            if not chunk:
                                continue
                            fp.write(chunk)
            
            if not image_path.exists() or image_path.stat().st_size == 0:
                raise Exception("Downloaded image file is empty or missing")
            
            self.logger.info(f"Successfully downloaded single image: {image_path}")
            return image_path
            
        except Exception as e:
            self.logger.error(f"Failed to download single image: {str(e)}")
            raise Exception(f"Could not download single image: {str(e)}")
    
    async def create_slideshow_video(self, image_paths: List[Path], duration_per_slide: int = 3) -> Path:
        """
        Create a slideshow video from multiple images.
        
        Args:
            image_paths: List of image file paths
            duration_per_slide: Duration in seconds for each slide
            
        Returns:
            Path to the created video file
            
        Raises:
            Exception: If video creation fails
        """
        try:
            unique_id = str(uuid.uuid4())
            output_path = self.media_dir / f"slideshow_{unique_id}.mp4"
            
            self.logger.info(f"Creating slideshow video from {len(image_paths)} images", 
                           duration_per_slide=duration_per_slide)
            
            # Create ffmpeg inputs for each image with scaling and padding
            inputs = []
            for i, img_path in enumerate(image_paths):
                self.logger.info(f"Processing image {i+1}/{len(image_paths)}: {img_path.name}")
                
                # Scale and pad image to 1080x1080 (Instagram square format)
                input_stream = (
                    ffmpeg
                    .input(str(img_path), loop=1, t=duration_per_slide)
                    .filter('scale', 1080, 1080, force_original_aspect_ratio='decrease')
                    .filter('pad', 1080, 1080, '(ow-iw)/2', '(oh-ih)/2', color='black')
                )
                inputs.append(input_stream)
            
            # Concatenate all inputs
            joined = ffmpeg.concat(*inputs, v=1, a=0)
            
            # Output video with high quality settings optimized for Instagram
            (
                ffmpeg
                .output(joined, str(output_path), 
                       vcodec='libx264', 
                       pix_fmt='yuv420p',
                       r=30,  # 30 fps
                       crf=18,  # Very high quality
                       preset='medium',  # Balance between speed and compression
                       movflags='faststart')  # Optimize for web streaming
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            
            if not output_path.exists() or output_path.stat().st_size == 0:
                raise Exception("Created slideshow video is empty or missing")
            
            self.logger.info(f"Successfully created slideshow video", 
                           output_path=str(output_path), 
                           size_bytes=output_path.stat().st_size)
            return output_path
            
        except Exception as e:
            self.logger.error(f"Failed to create slideshow video: {str(e)}")
            raise Exception(f"Could not create slideshow video: {str(e)}")
    
    async def create_static_image_video(self, image_path: Path, duration: int = 1) -> Path:
        """
        Create a video from a single static image.
        
        Args:
            image_path: Path to the image file
            duration: Duration in seconds for the video
            
        Returns:
            Path to the created video file
            
        Raises:
            Exception: If video creation fails
        """
        try:
            unique_id = str(uuid.uuid4())
            output_path = self.media_dir / f"static_{unique_id}.mp4"
            
            self.logger.info(f"Creating static image video: {image_path}, duration: {duration}s")
            
            # Create video from static image
            (
                ffmpeg
                .input(str(image_path), loop=1, t=duration)
                .output(str(output_path), 
                       vcodec='libx264', 
                       pix_fmt='yuv420p',
                       r=30,  # 30 fps
                       crf=23)  # High quality
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            
            if not output_path.exists() or output_path.stat().st_size == 0:
                raise Exception("Created static image video is empty or missing")
            
            self.logger.info(f"Successfully created static image video: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Failed to create static image video: {str(e)}")
            raise Exception(f"Could not create static image video: {str(e)}")
    
    async def cleanup_image_files(self, image_paths: List[Path]) -> None:
        """
        Remove temporary image files after processing.
        
        Args:
            image_paths: List of image file paths to remove
        """
        deleted_count = 0
        for path in image_paths:
            try:
                if path.exists():
                    path.unlink()
                    deleted_count += 1
                    self.logger.info(f"Cleaned up temporary image: {path}")
            except Exception as e:
                self.logger.warning(f"Failed to remove temporary image {path}: {str(e)}")
        
        if deleted_count > 0:
            self.logger.info(f"Cleaned up {deleted_count} temporary image files")
    
    async def create_empty_audio_file(self, video_path: Path) -> Path:
        """
        Create an empty audio file to maintain consistent response structure.
        
        Args:
            video_path: Path to the video file (for naming)
            
        Returns:
            Path to the created empty audio file
        """
        try:
            audio_filename = video_path.stem
            audio_path = self.media_dir / f"{audio_filename}.mp3"
            
            # Create a silent audio file using ffmpeg
            (
                ffmpeg
                .input('anullsrc', f='lavfi', t=1)  # 1 second of silence
                .output(str(audio_path), format='mp3')
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            
            if audio_path.exists():
                self.logger.info(f"Created empty audio file: {audio_path}")
                return audio_path
            else:
                raise Exception("Empty audio file was not created")
                
        except Exception as e:
            self.logger.error(f"Failed to create empty audio file: {str(e)}")
            raise Exception(f"Could not create empty audio file: {str(e)}")
        
    async def download_post(self, url: str) -> Tuple[str, Dict[str, Any]]:
        """
        Download a post and return the file path and metadata.
        Supports video, carousel, and single image posts.
        
        Args:
            url: Instagram post URL
            
        Returns:
            Tuple of (filename, metadata_dict)
            
        Raises:
            Exception: If download fails
        """
        try:
            # Determine post type first
            post_type = self.determine_post_type(url)
            self.logger.info(f"Detected Instagram post type: {post_type}")
            
            # Extract shortcode and load the post metadata
            shortcode = self.extract_shortcode_from_url(url)
            post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
            
            # Choose a stable unique identifier for filenames (mediaid is globally unique)
            unique_id = str(post.mediaid)
            target_mp4 = self.media_dir / f"{unique_id}.mp4"
            
            # Fast path: if already downloaded, return cached metadata
            if target_mp4.exists():
                metadata = self._build_metadata_from_files(
                    post=post,
                    unique_id=unique_id,
                    target_mp4=target_mp4,
                    target_txt=self.media_dir / f"{unique_id}.txt",
                )
                return target_mp4.name, metadata
            
            # Process based on post type
            if post_type == "video":
                # Use existing video download logic
                target_mp4 = await self._download_video_post(post, unique_id)
                
            elif post_type == "carousel":
                # Download carousel images and create slideshow video
                image_paths = await self.download_carousel_images(url)
                target_mp4 = await self.create_slideshow_video(image_paths, duration_per_slide=3)
                # Clean up temporary images
                await self.cleanup_image_files(image_paths)
                
            elif post_type == "image":
                # Download single image and create static video
                image_path = await self.download_single_image(url)
                target_mp4 = await self.create_static_image_video(image_path, duration=1)
                # Clean up temporary image
                await self.cleanup_image_files([image_path])
                
            else:
                raise Exception(f"Unsupported Instagram post type: {post_type}")
            
            # Persist caption and metadata for idempotent reads
            target_txt = self.media_dir / f"{unique_id}.txt"
            target_json = self.media_dir / f"{unique_id}.json"
            
            try:
                target_txt.write_text(post.caption or "")
            except Exception:
                pass

            # Build metadata
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
                    "post_type": post_type,
                }, ensure_ascii=False))
            except Exception:
                pass

            # Extract audio from video after successful download
            audio_extracted, audio_url = self._extract_audio_from_video(target_mp4)
            
            # If audio extraction failed (e.g., for static images), create empty audio
            if not audio_extracted:
                try:
                    empty_audio_path = await self.create_empty_audio_file(target_mp4)
                    audio_url = f"{AppConfig.BASE_URL}/static/{empty_audio_path.name}"
                    self.logger.info("Created empty audio file for post without audio")
                except Exception as e:
                    self.logger.warning(f"Failed to create empty audio file: {str(e)}")
                    audio_url = None
            
            # Add audio URL to metadata
            metadata["audio_url"] = audio_url
            
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
    
    async def _download_video_post(self, post: "instaloader.Post", unique_id: str) -> Path:
        """
        Download a video post using the existing logic.
        
        Args:
            post: Instagram post object
            unique_id: Unique identifier for the post
            
        Returns:
            Path to the downloaded video file
        """
        target_mp4 = self.media_dir / f"{unique_id}.mp4"
        
        # Download video directly from the post's video_url
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
        
        return target_mp4

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
