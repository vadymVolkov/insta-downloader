"""
Base service class for common functionality between Instagram and TikTok services.
Provides shared methods for file management, audio extraction, and metadata handling.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Tuple, Any, Optional
from datetime import datetime
from .ffmpeg_utils import extract_audio_from_video, get_audio_path, get_audio_url, cleanup_audio_files
from app.config import AppConfig


class BaseService:
    """
    Base service class providing common functionality for social media download services.
    """
    
    def __init__(self, media_dir: str = "app/media", max_files: int = 10):
        """
        Initialize the base service with common configuration.
        
        Args:
            media_dir: Directory to store downloaded media files
            max_files: Maximum number of files to keep (for cleanup)
        """
        self.media_dir = Path(media_dir)
        self.media_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.max_files = max_files
        
        self.logger.info(f"{self.__class__.__name__} initialized | media_dir={self.media_dir}")
    
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
    
    def _extract_audio_from_video(self, video_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Extract audio from video file and return success status and audio URL.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Tuple of (success, audio_url)
        """
        try:
            # Generate audio filename (same as video filename without extension)
            audio_filename = video_path.stem
            audio_path = get_audio_path(audio_filename)
            
            self.logger.info(f"🎵 Starting audio extraction for {video_path.name}")
            
            # Extract audio from video
            success, error = extract_audio_from_video(str(video_path), audio_path)
            
            if success:
                audio_url = get_audio_url(audio_filename)
                self.logger.info(f"✅ Audio extraction successful: {audio_path}")
                return True, audio_url
            else:
                self.logger.warning(f"⚠️ Audio extraction failed: {error}")
                return False, None
                
        except Exception as e:
            self.logger.error(f"❌ Audio extraction error: {str(e)}")
            return False, None
    
    def _build_metadata_with_audio(self, author: str, description: str, target_mp4: Path, 
                                  created_at: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Build metadata dictionary with audio URL if available.
        
        Args:
            author: Author of the post
            description: Description of the post
            target_mp4: Path to the video file
            created_at: Creation date (defaults to file modification time)
            
        Returns:
            Metadata dictionary
        """
        # Check if audio file exists for this video
        audio_filename = target_mp4.stem
        audio_path = get_audio_path(audio_filename)
        audio_url = None
        
        if os.path.exists(audio_path):
            audio_url = get_audio_url(audio_filename)
            self.logger.info(f"🎵 Found existing audio file: {audio_path}")
        else:
            self.logger.info(f"ℹ️ No audio file found for {target_mp4.name}")
        
        # Use file modification time if created_at not provided
        if created_at is None:
            created_at = datetime.fromtimestamp(target_mp4.stat().st_mtime)
        
        return {
            "author": author,
            "description": description,
            "created_at": created_at,
            "video_url": f"{AppConfig.BASE_URL}/static/{target_mp4.name}",
            "audio_url": audio_url,
        }
    
    def _save_metadata_files(self, target_mp4: Path, metadata: Dict[str, Any], 
                           description: str) -> None:
        """
        Save metadata to JSON and text files.
        
        Args:
            target_mp4: Path to the video file
            metadata: Metadata dictionary to save
            description: Description text to save
        """
        try:
            # Save metadata to JSON file
            target_json = target_mp4.with_suffix('.json')
            target_json.write_text(json.dumps(metadata, indent=2, default=str))
            
            # Save description to text file
            target_txt = target_mp4.with_suffix('.txt')
            target_txt.write_text(description)
            
        except Exception as e:
            self.logger.warning(f"Failed to save metadata files: {str(e)}")
    
    def _get_unique_filename(self, base_name: str) -> Path:
        """
        Generate a unique filename for the video file.
        
        Args:
            base_name: Base name for the file
            
        Returns:
            Path to the unique filename
        """
        # Create a unique filename to avoid conflicts
        unique_id = f"{base_name}_{int(datetime.now().timestamp())}"
        return self.media_dir / f"{unique_id}.mp4"
