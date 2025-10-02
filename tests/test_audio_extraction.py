#!/usr/bin/env python3
"""
Test script for audio extraction functionality.
This script tests the FFmpeg audio extraction utility.
"""

import os
import sys
import tempfile
from app.services.ffmpeg_utils import verify_ffmpeg_installation, test_audio_extraction

def main():
    """Test audio extraction functionality."""
    print("🧪 Testing FFmpeg audio extraction functionality...")
    
    # Check if FFmpeg is available
    print("1. Checking FFmpeg availability...")
    if not verify_ffmpeg_installation():
        print("❌ FFmpeg is not available. Please install FFmpeg first.")
        return False
    print("✅ FFmpeg is available")
    
    # Check if we have any existing video files to test with
    print("2. Looking for test video files...")
    media_dir = "app/media"
    video_files = []
    
    if os.path.exists(media_dir):
        for file in os.listdir(media_dir):
            if file.endswith(('.mp4', '.avi', '.mov', '.mkv')):
                video_files.append(os.path.join(media_dir, file))
    
    if not video_files:
        print("⚠️ No video files found in app/media directory")
        print("   You can test audio extraction by placing a video file in app/media/")
        return True
    
    # Test audio extraction with the first video file found
    test_video = video_files[0]
    print(f"3. Testing audio extraction with: {test_video}")
    
    # Create temporary output file
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
        temp_audio_path = temp_file.name
    
    try:
        success = test_audio_extraction(test_video, temp_audio_path)
        if success:
            print("✅ Audio extraction test successful!")
            print(f"   Output file: {temp_audio_path}")
            print(f"   File size: {os.path.getsize(temp_audio_path)} bytes")
        else:
            print("❌ Audio extraction test failed")
            return False
    finally:
        # Clean up temporary file
        if os.path.exists(temp_audio_path):
            os.unlink(temp_audio_path)
    
    print("🎉 All tests passed!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
