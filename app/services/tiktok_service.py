import logging
from pathlib import Path
from typing import Dict, Tuple, Any
import os
import re
import json
from datetime import datetime
import yt_dlp
import glob


class TikTokService:
    """
    Service for downloading TikTok videos using yt-dlp (modern approach for 2024-2025).
    """

    def __init__(self, media_dir: str = "app/media"):
        """
        Initialize the TikTok service.

        Args:
            media_dir: Directory to store downloaded media files
        """
        self.media_dir = Path(media_dir)
        self.media_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.logger.info("TikTokService initialized | media_dir=%s", str(self.media_dir))
        
        # File rotation settings
        self.max_files = 10  # Keep only last 10 videos

    def _extract_video_id(self, url: str) -> str:
        """
        Extract a stable identifier from common TikTok URL formats.
        """
        m = re.search(r"/video/(\d+)", url)
        if m:
            return m.group(1)
        # fallback: strip non-filename chars for cache key
        return re.sub(r"[^A-Za-z0-9]+", "", url)[:32]
    
    def _cleanup_old_files(self):
        """
        Clean up old video files, keeping only the most recent max_files videos.
        Files are sorted by modification time (newest first).
        """
        try:
            # Get all video files in media directory
            video_files = list(self.media_dir.glob("*.mp4"))
            
            if len(video_files) <= self.max_files:
                return  # No cleanup needed
            
            # Sort by modification time (newest first)
            video_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Files to delete (oldest ones)
            files_to_delete = video_files[self.max_files:]
            
            deleted_count = 0
            for file_path in files_to_delete:
                try:
                    # Delete associated files (.json, .txt)
                    base_name = file_path.stem
                    json_file = self.media_dir / f"{base_name}.json"
                    txt_file = self.media_dir / f"{base_name}.txt"
                    
                    # Delete main video file
                    file_path.unlink()
                    deleted_count += 1
                    
                    # Delete associated metadata files
                    if json_file.exists():
                        json_file.unlink()
                    if txt_file.exists():
                        txt_file.unlink()
                        
                except Exception as e:
                    self.logger.warning("Failed to delete file %s: %s", file_path, str(e))
            
            if deleted_count > 0:
                self.logger.info("File cleanup completed: deleted %d old video files", deleted_count)
                
        except Exception as e:
            self.logger.error("Error during file cleanup: %s", str(e))

    async def download_post(self, url: str) -> Tuple[str, Dict[str, Any]]:
        """
        Download a TikTok video using yt-dlp and return the file name and metadata.

        Args:
            url: TikTok video URL

        Returns:
            Tuple of (filename, metadata_dict)
        """
        try:
            # Extract video ID for filename
            unique_id = self._extract_video_id(url)
            target_mp4 = self.media_dir / f"{unique_id}.mp4"
            target_json = self.media_dir / f"{unique_id}.json"
            target_txt = self.media_dir / f"{unique_id}.txt"

            # Check if already downloaded
            if target_mp4.exists():
                metadata = self._build_metadata(unique_id, "unknown", "", target_mp4)
                return target_mp4.name, metadata

            # Configure yt-dlp options for TikTok
            ydl_opts = {
                'outtmpl': str(target_mp4),
                'format': 'best[ext=mp4]/best',
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'writethumbnail': False,
                'writeinfojson': False,
                'writesubtitles': False,
                'writeautomaticsub': False,
                'ignoreerrors': False,
                'no_check_certificate': True,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'referer': 'https://www.tiktok.com/',
                'headers': {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-us,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            }

            # Use yt-dlp to download video and extract metadata
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    raise Exception("Could not extract video information from TikTok URL")
                
                # Get metadata
                author = info.get('uploader', 'unknown')
                # Try to get full description from multiple fields
                description = (info.get('description', '') or 
                              info.get('title', '') or 
                              info.get('fulltitle', '') or
                              info.get('alt_title', ''))
                upload_date = info.get('upload_date', '')
                
                # Log available fields for debugging
                self.logger.info("TikTok metadata fields: %s", list(info.keys()))
                self.logger.info("Description length: %d chars", len(description))
                self.logger.info("Description preview: %s", description[:100] + "..." if len(description) > 100 else description)
                
                # Convert upload_date to datetime if available
                created_at = datetime.now()
                if upload_date:
                    try:
                        created_at = datetime.strptime(upload_date, '%Y%m%d')
                    except ValueError:
                        pass
                
                # Download the video
                ydl.download([url])
                
                # Verify download
                if not target_mp4.exists() or target_mp4.stat().st_size == 0:
                    raise Exception("Downloaded video file is empty or missing")

                # Save metadata files
                try:
                    target_txt.write_text(description)
                except Exception:
                    pass

                metadata = {
                    "author": author,
                    "description": description,
                    "created_at": created_at,
                    "video_url": f"http://localhost:8000/static/{target_mp4.name}",
                }
                
                try:
                    target_json.write_text(json.dumps({
                        "video_id": unique_id,
                        "author": author,
                        "description": description,
                        "date": created_at.isoformat(),
                        "upload_date": upload_date,
                    }, ensure_ascii=False))
                except Exception:
                    pass

                # Clean up old files after successful download
                self._cleanup_old_files()

                return target_mp4.name, metadata

        except Exception as e:
            self.logger.error("TikTok download error: %s", str(e))
            raise Exception(f"Error downloading TikTok video: {str(e)}")

    def _build_metadata(self, unique_id: str, author: str, description: str, target_mp4: Path) -> Dict[str, Any]:
        """
        Build metadata dict from saved files and parameters.
        """
        return {
            "author": author,
            "description": description,
            "created_at": datetime.fromtimestamp(target_mp4.stat().st_mtime),
            "video_url": f"http://localhost:8000/static/{target_mp4.name}",
        }
