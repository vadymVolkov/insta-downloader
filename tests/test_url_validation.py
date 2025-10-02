#!/usr/bin/env python3
"""
Test script for URL validation functionality.
Tests Instagram and TikTok URL validation.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.utils.url_validator import validate_url, is_instagram_url, is_tiktok_url

def test_url_validation():
    """Test URL validation with various inputs."""
    print("🧪 Testing URL validation...")
    print("=" * 60)
    
    # Test cases
    test_cases = [
        # Valid Instagram URLs
        ("https://www.instagram.com/p/ABC123/", True, "instagram"),
        ("https://instagram.com/reel/XYZ789/", True, "instagram"),
        ("https://www.instagram.com/tv/DEF456/", True, "instagram"),
        ("https://www.instagram.com/p/ABC123", True, "instagram"),  # No trailing slash
        
        # Valid TikTok URLs
        ("https://www.tiktok.com/@user/video/1234567890/", True, "tiktok"),
        ("https://vm.tiktok.com/ABC123/", True, "tiktok"),
        ("https://vt.tiktok.com/XYZ789/", True, "tiktok"),
        ("https://m.tiktok.com/v/1234567890/", True, "tiktok"),
        
        # Invalid URLs
        ("https://www.youtube.com/watch?v=123", False, None),
        ("https://www.facebook.com/post/123", False, None),
        ("https://www.instagram.com/user/", False, None),  # Profile, not post
        ("https://www.tiktok.com/@user/", False, None),  # Profile, not video
        ("not-a-url", False, None),
        ("", False, None),
        ("https://", False, None),
        ("ftp://example.com", False, None),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for url, expected_valid, expected_platform in test_cases:
        is_valid, platform, error = validate_url(url)
        
        if is_valid == expected_valid and platform == expected_platform:
            status = "✅"
            passed += 1
        else:
            status = "❌"
        
        print(f"{status} URL: {url}")
        print(f"   Expected: valid={expected_valid}, platform={expected_platform}")
        print(f"   Got: valid={is_valid}, platform={platform}")
        if error:
            print(f"   Error: {error}")
        print()
    
    print("=" * 60)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All URL validation tests passed!")
    else:
        print("❌ Some tests failed. Check the validation logic.")
    
    return passed == total

def test_platform_detection():
    """Test platform detection functions."""
    print("\n🧪 Testing platform detection...")
    print("=" * 60)
    
    # Instagram tests
    instagram_urls = [
        "https://www.instagram.com/p/ABC123/",
        "https://instagram.com/reel/XYZ789/",
        "https://www.instagram.com/tv/DEF456/",
    ]
    
    for url in instagram_urls:
        is_ig = is_instagram_url(url)
        is_tt = is_tiktok_url(url)
        print(f"Instagram URL: {url}")
        print(f"   is_instagram_url: {is_ig} ✅" if is_ig else f"   is_instagram_url: {is_ig} ❌")
        print(f"   is_tiktok_url: {is_tt} ✅" if not is_tt else f"   is_tiktok_url: {is_tt} ❌")
        print()
    
    # TikTok tests
    tiktok_urls = [
        "https://www.tiktok.com/@user/video/1234567890/",
        "https://vm.tiktok.com/ABC123/",
        "https://vt.tiktok.com/XYZ789/",
    ]
    
    for url in tiktok_urls:
        is_ig = is_instagram_url(url)
        is_tt = is_tiktok_url(url)
        print(f"TikTok URL: {url}")
        print(f"   is_instagram_url: {is_ig} ✅" if not is_ig else f"   is_instagram_url: {is_ig} ❌")
        print(f"   is_tiktok_url: {is_tt} ✅" if is_tt else f"   is_tiktok_url: {is_tt} ❌")
        print()

def main():
    """Run all URL validation tests."""
    print("🚀 Starting URL Validation Tests")
    print("=" * 60)
    
    # Test URL validation
    validation_ok = test_url_validation()
    
    # Test platform detection
    test_platform_detection()
    
    print("=" * 60)
    if validation_ok:
        print("✅ All tests completed successfully!")
        print("🎯 URL validation is ready for production use")
    else:
        print("❌ Some tests failed. Please review the validation logic.")
    
    print("\n📝 Supported URL formats:")
    print("   Instagram: https://www.instagram.com/p/... or /reel/...")
    print("   TikTok: https://www.tiktok.com/@user/video/... or https://vm.tiktok.com/...")

if __name__ == "__main__":
    main()
