"""
FFmpeg utilities for audio extraction functionality.
Provides functions to verify FFmpeg installation and extract audio from videos.
"""

import subprocess
import logging
import os
import time
from typing import Optional, Tuple, Dict, Any
import ffmpeg
from app.config import AppConfig

logger = logging.getLogger(__name__)


def verify_ffmpeg_installation() -> bool:
    """
    Verify that FFmpeg is properly installed and available in the system PATH.
    
    Returns:
        bool: True if FFmpeg is available, False otherwise
    """
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            check=True,
            timeout=10
        )
        first_line = result.stdout.split('\n')[0]
        logger.info(f"FFmpeg installed: {first_line}")
        return True
    except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
        logger.error(f"FFmpeg not properly installed: {str(e)}")
        return False


def extract_audio_from_video(video_path: str, audio_path: str) -> Tuple[bool, Optional[str]]:
    """
    Extract audio track from a video file using FFmpeg with comprehensive error handling.
    
    Args:
        video_path (str): Path to the input video file
        audio_path (str): Path where the audio file should be saved
        
    Returns:
        Tuple[bool, Optional[str]]: (success, error_message)
    """
    start_time = time.time()
    
    try:
        # Check if input video exists
        if not os.path.exists(video_path):
            error_msg = f"Input video file not found: {video_path}"
            logger.error(error_msg)
            return False, error_msg
        
        # Check if input file is readable
        try:
            with open(video_path, 'rb') as f:
                f.read(1)  # Try to read first byte
        except PermissionError:
            error_msg = f"Permission denied: Cannot read video file {video_path}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Cannot access video file {video_path}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        
        # Get input file size for logging
        try:
            input_size = os.path.getsize(video_path)
            if input_size == 0:
                error_msg = f"Input video file is empty: {video_path}"
                logger.error(error_msg)
                return False, error_msg
        except OSError as e:
            error_msg = f"Cannot get file size for {video_path}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        
        logger.info(f"Starting audio extraction: {video_path} ({input_size} bytes)")
        
        # Create output directory if it doesn't exist
        try:
            os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        except PermissionError:
            error_msg = f"Permission denied: Cannot create output directory for {audio_path}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Cannot create output directory: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        
        # Extract audio using ffmpeg-python with comprehensive error handling
        try:
            (ffmpeg
                .input(video_path)
                .output(audio_path,
                       acodec='libmp3lame',  # High-quality MP3 encoder
                       ab=AppConfig.AUDIO.AUDIO_BITRATE,  # Configurable bitrate
                       ar=str(AppConfig.AUDIO.AUDIO_SAMPLE_RATE),  # Configurable sample rate
                       ac=AppConfig.AUDIO.AUDIO_CHANNELS,  # Configurable channels
                       map='a',             # Extract only audio
                       loglevel='error',    # Reduce log output
                       threads=0)          # Use all available CPU cores
                .overwrite_output()          # Overwrite if file exists
                .run(capture_stdout=True, capture_stderr=True))
            
            # Check if output file was created successfully
            if os.path.exists(audio_path):
                try:
                    output_size = os.path.getsize(audio_path)
                    if output_size == 0:
                        error_msg = "Audio extraction completed but output file is empty"
                        logger.error(error_msg)
                        # Clean up empty file
                        os.remove(audio_path)
                        return False, error_msg
                    
                    duration = time.time() - start_time
                    logger.info(f"Audio extraction successful: {audio_path} ({output_size} bytes) in {duration:.2f}s")
                    
                    # Clean up old audio files after successful extraction (if enabled)
                    if AppConfig.AUDIO.AUTO_CLEANUP_AFTER_EXTRACTION:
                        try:
                            deleted_files = cleanup_audio_files()
                            if deleted_files:
                                logger.info(f"Audio cleanup after extraction: removed {len(deleted_files)} old files")
                        except Exception as cleanup_error:
                            logger.warning(f"Audio cleanup failed after extraction: {str(cleanup_error)}")
                    else:
                        logger.info("Audio cleanup after extraction is disabled")
                    
                    return True, None
                except OSError as e:
                    error_msg = f"Cannot verify output file {audio_path}: {str(e)}"
                    logger.error(error_msg)
                    return False, error_msg
            else:
                error_msg = "Audio extraction completed but output file was not created"
                logger.error(error_msg)
                return False, error_msg
                
        except ffmpeg.Error as e:
            # Handle specific FFmpeg errors
            stderr_msg = e.stderr.decode() if hasattr(e, 'stderr') and e.stderr else str(e)
            
            # Check for common error patterns
            if "No audio stream" in stderr_msg or "no audio" in stderr_msg.lower():
                error_msg = f"Video file has no audio track: {video_path}"
                logger.warning(error_msg)
                return False, error_msg
            elif "Permission denied" in stderr_msg:
                error_msg = f"Permission denied during audio extraction: {stderr_msg}"
                logger.error(error_msg)
                return False, error_msg
            elif "Invalid data found" in stderr_msg or "corrupt" in stderr_msg.lower():
                error_msg = f"Corrupted or invalid video file: {video_path} - {stderr_msg}"
                logger.error(error_msg)
                return False, error_msg
            else:
                error_msg = f"FFmpeg error: {stderr_msg}"
                logger.error(error_msg)
                return False, error_msg
                
        except FileNotFoundError:
            error_msg = "FFmpeg not found in system PATH"
            logger.error(error_msg)
            return False, error_msg
            
    except PermissionError as e:
        error_msg = f"Permission error during audio extraction: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
        
    except OSError as e:
        error_msg = f"OS error during audio extraction: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
        
    except Exception as e:
        error_msg = f"Unexpected error during audio extraction: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


# Audio directory configuration - using media directory for static serving
AUDIO_DIR = os.path.join('app', 'media')


def get_audio_path(filename: str) -> str:
    """
    Generate filesystem path for audio file.
    
    Args:
        filename (str): Base filename without extension
        
    Returns:
        str: Full path to audio file
    """
    return os.path.join(AUDIO_DIR, f"{filename}.mp3")


def get_audio_url(filename: str) -> str:
    """
    Generate URL for accessing audio file.
    
    Args:
        filename (str): Base filename without extension
        
    Returns:
        str: URL to access audio file
    """
    from app.config import AppConfig
    return f"{AppConfig.BASE_URL}/static/{filename}.mp3"


def ensure_audio_directory() -> bool:
    """
    Ensure the audio directory exists with proper permissions.
    
    Returns:
        bool: True if directory exists or was created successfully
    """
    try:
        os.makedirs(AUDIO_DIR, exist_ok=True)
        # Set permissions to allow read/write for the application
        os.chmod(AUDIO_DIR, 0o755)
        logger.info(f"Audio directory ensured: {AUDIO_DIR}")
        return True
    except Exception as e:
        logger.error(f"Failed to create audio directory: {str(e)}")
        return False






def get_ffmpeg_performance_info() -> Dict[str, Any]:
    """
    Get FFmpeg performance information and system capabilities.
    
    Returns:
        Dict containing performance metrics and system info
    """
    try:
        # Get FFmpeg version and build info
        result = subprocess.run(
            ['ffmpeg', '-version'], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            check=True,
            timeout=10
        )
        
        version_info = result.stdout.split('\n')[0]
        
        # Get available encoders
        encoder_result = subprocess.run(
            ['ffmpeg', '-encoders'], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            check=True,
            timeout=10
        )
        
        # Check for libmp3lame availability
        has_libmp3lame = 'libmp3lame' in encoder_result.stdout
        
        return {
            "version": version_info,
            "has_libmp3lame": has_libmp3lame,
            "status": "available"
        }
        
    except Exception as e:
        logger.error(f"Error getting FFmpeg performance info: {str(e)}")
        return {
            "version": "unknown",
            "has_libmp3lame": False,
            "status": "error",
            "error": str(e)
        }


def cleanup_audio_files(max_files: Optional[int] = None) -> list:
    """
    Clean up old audio files, keeping only the most recent max_files audio files.
    Files are sorted by modification time (newest first).
    
    Args:
        max_files (Optional[int]): Maximum number of audio files to keep. 
                                 If None, uses value from AppConfig.AUDIO.MAX_AUDIO_FILES
        
    Returns:
        list: List of removed file paths
    """
    try:
        # Use configuration value if max_files not specified
        if max_files is None:
            max_files = AppConfig.AUDIO.MAX_AUDIO_FILES
        # Get all MP3 files in the media directory
        import glob
        audio_files = glob.glob(os.path.join(AUDIO_DIR, '*.mp3'))
        
        if len(audio_files) <= max_files:
            logger.info(f"Audio cleanup not needed: {len(audio_files)} files (limit: {max_files})")
            return []  # No cleanup needed
        
        # Sort files by modification time (newest first)
        audio_files.sort(key=os.path.getmtime, reverse=True)
        
        # Files to delete (oldest ones)
        files_to_delete = audio_files[max_files:]
        
        deleted_files = []
        for file_path in files_to_delete:
            try:
                # Get file info for logging
                file_size = os.path.getsize(file_path)
                file_mtime = os.path.getmtime(file_path)
                
                # Delete the audio file
                os.remove(file_path)
                deleted_files.append(file_path)
                
                logger.info(f"Removed old audio file: {os.path.basename(file_path)} "
                           f"({file_size} bytes, modified: {time.ctime(file_mtime)})")
                
            except OSError as e:
                logger.warning(f"Failed to delete audio file {file_path}: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error deleting audio file {file_path}: {str(e)}")
        
        if deleted_files:
            logger.info(f"Audio cleanup completed: deleted {len(deleted_files)} old audio files")
        else:
            logger.warning("Audio cleanup attempted but no files were actually deleted")
            
        return deleted_files
        
    except Exception as e:
        logger.error(f"Error during audio cleanup: {str(e)}")
        return []
