#!/usr/bin/env python3
"""
Test script for Instagram multi-format post support.
Tests video, carousel, and single image post processing.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.instagram_service import InstagramService
from app.config import AppConfig

async def test_post_type_detection():
    """Test post type detection functionality."""
    print("🧪 Testing Instagram post type detection...")
    
    service = InstagramService()
    
    # Test URLs (these are examples - replace with real URLs for testing)
    test_urls = [
        "https://www.instagram.com/p/DOOFdyJjLbG/",  # Carousel example
        "https://www.instagram.com/reel/example/",   # Video example
        "https://www.instagram.com/p/example/",       # Single image example
    ]
    
    for url in test_urls:
        try:
            post_type = service.determine_post_type(url)
            print(f"✅ URL: {url}")
            print(f"   Post type: {post_type}")
        except Exception as e:
            print(f"❌ URL: {url}")
            print(f"   Error: {str(e)}")
        print()

async def test_service_initialization():
    """Test service initialization."""
    print("🧪 Testing Instagram service initialization...")
    
    try:
        service = InstagramService()
        print("✅ Instagram service initialized successfully")
        print(f"   Media directory: {service.media_dir}")
        print(f"   Max files: {service.max_files}")
        return True
    except Exception as e:
        print(f"❌ Service initialization failed: {str(e)}")
        return False

async def test_configuration():
    """Test configuration settings."""
    print("🧪 Testing configuration...")
    
    try:
        config = AppConfig()
        print("✅ Configuration loaded successfully")
        print(f"   Base URL: {config.BASE_URL}")
        print(f"   Media directory: {config.MEDIA_DIR}")
        print(f"   Log directory: {config.LOG_DIR}")
        return True
    except Exception as e:
        print(f"❌ Configuration failed: {str(e)}")
        return False

async def main():
    """Run all tests."""
    print("🚀 Starting Instagram Multi-Format Post Support Tests")
    print("=" * 60)
    
    # Test configuration
    config_ok = await test_configuration()
    print()
    
    # Test service initialization
    service_ok = await test_service_initialization()
    print()
    
    # Test post type detection (requires real URLs)
    print("⚠️  Post type detection requires real Instagram URLs")
    print("   Replace test URLs with actual Instagram post URLs to test")
    print()
    
    if config_ok and service_ok:
        print("✅ All basic tests passed!")
        print("🎯 Ready for integration testing with real Instagram URLs")
    else:
        print("❌ Some tests failed. Check configuration and dependencies.")
    
    print("=" * 60)
    print("📝 Next steps:")
    print("   1. Test with real Instagram video URLs")
    print("   2. Test with real Instagram carousel URLs") 
    print("   3. Test with real Instagram single image URLs")
    print("   4. Verify audio extraction works for all types")
    print("   5. Check file cleanup and management")

if __name__ == "__main__":
    asyncio.run(main())
