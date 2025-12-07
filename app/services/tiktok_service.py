import logging
from pathlib import Path
from typing import Dict, Tuple, Any
import os
import re
import json
from datetime import datetime
import yt_dlp
import glob
from .base_service import BaseService
from app.config import AppConfig


class TikTokService(BaseService):
    """
    Service for downloading TikTok videos using yt-dlp (modern approach for 2024-2025).
    """

    def __init__(self, media_dir: str = "app/media"):
        """
        Initialize the TikTok service.

        Args:
            media_dir: Directory to store downloaded media files
        """
        # Initialize base service
        super().__init__(media_dir, max_files=10)

    def _extract_video_id(self, url: str) -> str:
        """
        Extract a stable identifier from common TikTok URL formats.
        """
        m = re.search(r"/video/(\d+)", url)
        if m:
            return m.group(1)
        # fallback: strip non-filename chars for cache key
        return re.sub(r"[^A-Za-z0-9]+", "", url)[:32]
    

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
                self.logger.info(f"TikTok metadata fields: {list(info.keys())}")
                self.logger.info(f"Description length: {len(description)} chars")
                preview = description[:100] + "..." if len(description) > 100 else description
                self.logger.info(f"Description preview: {preview}")
                
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
                    "video_url": f"{AppConfig.BASE_URL}/static/{target_mp4.name}",
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

        except Exception as e:
            self.logger.error(f"TikTok download error: {str(e)}")
            raise Exception(f"Error downloading TikTok video: {str(e)}")

    def _build_metadata(self, unique_id: str, author: str, description: str, target_mp4: Path) -> Dict[str, Any]:
        """
        Build metadata dict from saved files and parameters.
        """
        created_at = datetime.fromtimestamp(target_mp4.stat().st_mtime)
        return self._build_metadata_with_audio(author, description, target_mp4, created_at)
