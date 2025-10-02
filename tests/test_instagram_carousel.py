#!/usr/bin/env python3
"""
Test script for Instagram carousel processing.
Tests the improved carousel detection and slideshow creation.
"""

import requests
import json
import time
from pathlib import Path

def test_carousel_processing():
    """
    Test Instagram carousel processing with a known carousel post.
    """
    # Test URL - replace with a real carousel post URL
    carousel_url = "https://www.instagram.com/p/DOOFdyJjLbG/?img_index=10&igsh=MXRzdHZ2cGVudGF5ZA=="
    
    print(f"🧪 Testing carousel processing with URL: {carousel_url}")
    print("=" * 80)
    
    try:
        # Make request to our API
        print("📤 Sending request to API...")
        start_time = time.time()
        
        response = requests.post(
            "http://localhost:8000/api/download/", 
            json={"url": carousel_url},
            timeout=120  # Increased timeout for carousel processing
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"⏱️  Processing time: {processing_time:.2f} seconds")
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success! Response data:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Check if we got a video URL
            if 'video_url' in data:
                video_url = data['video_url']
                print(f"\n🎥 Video URL: {video_url}")
                
                # Test if the video file is accessible
                try:
                    video_response = requests.get(video_url, timeout=30)
                    if video_response.status_code == 200:
                        print(f"✅ Video file is accessible (size: {len(video_response.content)} bytes)")
                    else:
                        print(f"❌ Video file not accessible (status: {video_response.status_code})")
                except Exception as e:
                    print(f"❌ Error accessing video file: {e}")
            
            # Check for audio URL
            if 'audio_url' in data and data['audio_url']:
                print(f"🎵 Audio URL: {data['audio_url']}")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out - carousel processing might take longer")
    except Exception as e:
        print(f"❌ Error during test: {e}")

def test_health_check():
    """
    Test the health check endpoint to ensure services are running.
    """
    print("\n🏥 Testing health check...")
    try:
        response = requests.get("http://localhost:8000/api/health/", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Health check passed")
            print(f"📊 Services status: {health_data.get('services', {})}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")

if __name__ == "__main__":
    print("🚀 Instagram Carousel Processing Test")
    print("=" * 80)
    
    # Test health check first
    test_health_check()
    
    # Test carousel processing
    test_carousel_processing()
    
    print("\n" + "=" * 80)
    print("🏁 Test completed!")
