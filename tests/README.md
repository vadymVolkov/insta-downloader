# Tests Directory

This directory contains all test scripts and benchmark files for the Instagram/TikTok downloader project.

## Test Files

### 1. `testcurl.py`
- **Purpose**: Simple curl-based API testing
- **Usage**: Tests the `/api/download/` endpoint with various URLs
- **Run**: `python testcurl.py`

### 2. `test_integration.py`
- **Purpose**: Comprehensive integration testing
- **Features**:
  - FFmpeg availability check
  - Basic audio extraction testing
  - API response structure validation
  - Static file serving verification
  - Error handling tests
  - Basic performance testing
- **Run**: `python test_integration.py`

### 3. `test_audio_extraction.py`
- **Purpose**: Audio extraction functionality testing
- **Features**:
  - Tests audio extraction from video files
  - Validates FFmpeg integration
  - Checks audio file generation
- **Run**: `python test_audio_extraction.py`

### 4. `benchmark_audio.py`
- **Purpose**: Performance benchmarking for audio extraction
- **Features**:
  - Synchronous vs asynchronous performance comparison
  - CPU and memory usage monitoring
  - Extraction time measurements
  - Results saved to JSON files
- **Run**: `python benchmark_audio.py`

## Results Files

### `integration_test_results.json`
- Contains results from integration tests
- Includes test status, timing, and error information

### `benchmark_results/`
- Directory containing benchmark result files
- Files are timestamped for easy identification
- Contains performance metrics and comparison data

## Running Tests

All tests should be run from the project root directory with the virtual environment activated:

```bash
cd /path/to/insta_downloader
source .venv/bin/activate
python tests/test_integration.py
```

## Notes

- Tests are designed to work with the running FastAPI server
- Some tests require FFmpeg to be installed
- Benchmark tests may take several minutes to complete
- All test results are preserved for analysis and comparison
