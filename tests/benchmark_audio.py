#!/usr/bin/env python3
"""
Performance benchmarking framework for audio extraction functionality.
Measures and tracks performance metrics for audio extraction operations.
"""

import time
import os
import sys
import json
import psutil
from pathlib import Path
from typing import Dict, List, Any
import asyncio

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.ffmpeg_utils import extract_audio_from_video, extract_audio_with_timeout, get_audio_path


class AudioExtractionBenchmark:
    """Benchmarking framework for audio extraction performance."""
    
    def __init__(self, output_dir: str = "benchmark_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results = []
        
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information for benchmarking context."""
        return {
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "disk_usage": psutil.disk_usage('/').percent,
            "python_version": sys.version,
            "platform": sys.platform
        }
    
    def measure_extraction_time(self, video_path: str, audio_path: str, iterations: int = 3) -> Dict[str, Any]:
        """Measure audio extraction time and performance metrics."""
        print(f"🎬 Benchmarking audio extraction for {os.path.basename(video_path)}")
        
        times = []
        memory_usage = []
        cpu_usage = []
        
        for i in range(iterations):
            print(f"  Iteration {i+1}/{iterations}...")
            
            # Clean up previous test file
            if os.path.exists(audio_path):
                os.remove(audio_path)
            
            # Measure system resources before extraction
            process = psutil.Process()
            memory_before = process.memory_info().rss
            cpu_before = process.cpu_percent()
            
            # Measure extraction time
            start_time = time.time()
            success, error = extract_audio_from_video(video_path, audio_path)
            end_time = time.time()
            
            # Measure system resources after extraction
            memory_after = process.memory_info().rss
            cpu_after = process.cpu_percent()
            
            if success:
                extraction_time = end_time - start_time
                times.append(extraction_time)
                memory_usage.append(memory_after - memory_before)
                cpu_usage.append(cpu_after - cpu_before)
                
                print(f"    ✅ Success: {extraction_time:.2f}s")
            else:
                print(f"    ❌ Failed: {error}")
                times.append(None)
                memory_usage.append(None)
                cpu_usage.append(None)
            
            # Clean up test file
            if os.path.exists(audio_path):
                os.remove(audio_path)
        
        # Calculate statistics
        valid_times = [t for t in times if t is not None]
        valid_memory = [m for m in memory_usage if m is not None]
        valid_cpu = [c for c in cpu_usage if c is not None]
        
        if valid_times:
            avg_time = sum(valid_times) / len(valid_times)
            min_time = min(valid_times)
            max_time = max(valid_times)
        else:
            avg_time = min_time = max_time = None
        
        if valid_memory:
            avg_memory = sum(valid_memory) / len(valid_memory)
            max_memory = max(valid_memory)
        else:
            avg_memory = max_memory = None
        
        if valid_cpu:
            avg_cpu = sum(valid_cpu) / len(valid_cpu)
            max_cpu = max(valid_cpu)
        else:
            avg_cpu = max_cpu = None
        
        return {
            "video_file": os.path.basename(video_path),
            "video_size": os.path.getsize(video_path),
            "iterations": iterations,
            "successful_extractions": len(valid_times),
            "failed_extractions": iterations - len(valid_times),
            "avg_time": avg_time,
            "min_time": min_time,
            "max_time": max_time,
            "avg_memory_usage": avg_memory,
            "max_memory_usage": max_memory,
            "avg_cpu_usage": avg_cpu,
            "max_cpu_usage": max_cpu,
            "raw_times": times,
            "raw_memory": memory_usage,
            "raw_cpu": cpu_usage
        }
    
    async def measure_async_extraction_time(self, video_path: str, audio_path: str, timeout: int = 30, iterations: int = 3) -> Dict[str, Any]:
        """Measure async audio extraction time and performance metrics."""
        print(f"🚀 Benchmarking async audio extraction for {os.path.basename(video_path)}")
        
        times = []
        memory_usage = []
        cpu_usage = []
        
        for i in range(iterations):
            print(f"  Async iteration {i+1}/{iterations}...")
            
            # Clean up previous test file
            if os.path.exists(audio_path):
                os.remove(audio_path)
            
            # Measure system resources before extraction
            process = psutil.Process()
            memory_before = process.memory_info().rss
            cpu_before = process.cpu_percent()
            
            # Measure async extraction time
            start_time = time.time()
            success, error = await extract_audio_with_timeout(video_path, audio_path, timeout)
            end_time = time.time()
            
            # Measure system resources after extraction
            memory_after = process.memory_info().rss
            cpu_after = process.cpu_percent()
            
            if success:
                extraction_time = end_time - start_time
                times.append(extraction_time)
                memory_usage.append(memory_after - memory_before)
                cpu_usage.append(cpu_after - cpu_before)
                
                print(f"    ✅ Success: {extraction_time:.2f}s")
            else:
                print(f"    ❌ Failed: {error}")
                times.append(None)
                memory_usage.append(None)
                cpu_usage.append(None)
            
            # Clean up test file
            if os.path.exists(audio_path):
                os.remove(audio_path)
        
        # Calculate statistics (same as sync version)
        valid_times = [t for t in times if t is not None]
        valid_memory = [m for m in memory_usage if m is not None]
        valid_cpu = [c for c in cpu_usage if c is not None]
        
        if valid_times:
            avg_time = sum(valid_times) / len(valid_times)
            min_time = min(valid_times)
            max_time = max(valid_times)
        else:
            avg_time = min_time = max_time = None
        
        if valid_memory:
            avg_memory = sum(valid_memory) / len(valid_memory)
            max_memory = max(valid_memory)
        else:
            avg_memory = max_memory = None
        
        if valid_cpu:
            avg_cpu = sum(valid_cpu) / len(valid_cpu)
            max_cpu = max(valid_cpu)
        else:
            avg_cpu = max_cpu = None
        
        return {
            "video_file": os.path.basename(video_path),
            "video_size": os.path.getsize(video_path),
            "timeout": timeout,
            "iterations": iterations,
            "successful_extractions": len(valid_times),
            "failed_extractions": iterations - len(valid_times),
            "avg_time": avg_time,
            "min_time": min_time,
            "max_time": max_time,
            "avg_memory_usage": avg_memory,
            "max_memory_usage": max_memory,
            "avg_cpu_usage": avg_cpu,
            "max_cpu_usage": max_cpu,
            "raw_times": times,
            "raw_memory": memory_usage,
            "raw_cpu": cpu_usage
        }
    
    def run_comprehensive_benchmark(self, video_files: List[str], iterations: int = 3) -> Dict[str, Any]:
        """Run comprehensive benchmark on multiple video files."""
        print("🏁 Starting Comprehensive Audio Extraction Benchmark")
        print("=" * 60)
        
        benchmark_results = {
            "timestamp": time.time(),
            "system_info": self.get_system_info(),
            "sync_results": [],
            "async_results": [],
            "summary": {}
        }
        
        for video_file in video_files:
            if not os.path.exists(video_file):
                print(f"⚠️ Video file not found: {video_file}")
                continue
            
            # Generate test audio path
            video_filename = os.path.basename(video_file)
            audio_filename = os.path.splitext(video_filename)[0] + "_benchmark"
            audio_path = get_audio_path(audio_filename)
            
            # Sync benchmark
            sync_result = self.measure_extraction_time(video_file, audio_path, iterations)
            benchmark_results["sync_results"].append(sync_result)
            
            # Async benchmark
            async_result = asyncio.run(self.measure_async_extraction_time(video_file, audio_path, 30, iterations))
            benchmark_results["async_results"].append(async_result)
        
        # Calculate summary statistics
        self._calculate_summary(benchmark_results)
        
        # Save results
        self._save_results(benchmark_results)
        
        return benchmark_results
    
    def _calculate_summary(self, results: Dict[str, Any]):
        """Calculate summary statistics from benchmark results."""
        sync_times = []
        async_times = []
        
        for result in results["sync_results"]:
            if result["avg_time"] is not None:
                sync_times.append(result["avg_time"])
        
        for result in results["async_results"]:
            if result["avg_time"] is not None:
                async_times.append(result["avg_time"])
        
        results["summary"] = {
            "total_videos_tested": len(results["sync_results"]),
            "sync_avg_time": sum(sync_times) / len(sync_times) if sync_times else None,
            "async_avg_time": sum(async_times) / len(async_times) if async_times else None,
            "sync_success_rate": len(sync_times) / len(results["sync_results"]) if results["sync_results"] else 0,
            "async_success_rate": len(async_times) / len(results["async_results"]) if results["async_results"] else 0
        }
    
    def _save_results(self, results: Dict[str, Any]):
        """Save benchmark results to file."""
        timestamp = int(results["timestamp"])
        filename = f"audio_extraction_benchmark_{timestamp}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"📊 Benchmark results saved to: {filepath}")
    
    def print_summary(self, results: Dict[str, Any]):
        """Print a summary of benchmark results."""
        summary = results["summary"]
        
        print("\n📈 Benchmark Summary")
        print("=" * 40)
        print(f"Total videos tested: {summary['total_videos_tested']}")
        print(f"Sync average time: {summary['sync_avg_time']:.2f}s" if summary['sync_avg_time'] else "Sync: No successful extractions")
        print(f"Async average time: {summary['async_avg_time']:.2f}s" if summary['async_avg_time'] else "Async: No successful extractions")
        print(f"Sync success rate: {summary['sync_success_rate']:.1%}")
        print(f"Async success rate: {summary['async_success_rate']:.1%}")


def main():
    """Main function to run audio extraction benchmarks."""
    # Find video files for testing
    media_dir = Path("app/media")
    video_files = list(media_dir.glob("*.mp4"))
    
    if not video_files:
        print("❌ No video files found in app/media directory")
        return
    
    print(f"🎬 Found {len(video_files)} video files for benchmarking")
    
    # Run benchmark
    benchmark = AudioExtractionBenchmark()
    results = benchmark.run_comprehensive_benchmark([str(f) for f in video_files], iterations=2)
    
    # Print summary
    benchmark.print_summary(results)
    
    print("\n✅ Benchmark completed!")


if __name__ == "__main__":
    main()
