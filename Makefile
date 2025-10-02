# Instagram Downloader API - Server Management
# Makefile for easy server control

.PHONY: help start stop restart status clean install test

# Default target
help:
	@echo "Instagram Downloader API - Server Management"
	@echo "=============================================="
	@echo ""
	@echo "Available commands:"
	@echo "  make start     - Start the server"
	@echo "  make stop      - Stop the server"
	@echo "  make restart   - Restart the server"
	@echo "  make status    - Check server status"
	@echo "  make clean     - Clean up server files"
	@echo "  make install   - Install dependencies"
	@echo "  make test      - Run tests"
	@echo ""

# Start the server
start:
	@echo "🚀 Starting Instagram Downloader API Server..."
	@python app/server_manager.py start

# Stop the server
stop:
	@echo "🛑 Stopping Instagram Downloader API Server..."
	@python app/server_manager.py stop

# Restart the server
restart:
	@echo "🔄 Restarting Instagram Downloader API Server..."
	@python app/server_manager.py restart

# Check server status
status:
	@echo "📊 Checking server status..."
	@python app/server_manager.py status

# Clean up server files
clean:
	@echo "🧹 Cleaning up server files..."
	@rm -f server.pid
	@rm -rf __pycache__
	@rm -rf app/__pycache__
	@rm -rf app/services/__pycache__
	@rm -rf app/routers/__pycache__
	@rm -rf app/utils/__pycache__
	@rm -rf app/middleware/__pycache__
	@echo "✅ Cleanup completed"

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	@pip install -r requirements.txt
	@echo "✅ Dependencies installed"

# Run tests
test:
	@echo "🧪 Running tests..."
	@python -m pytest tests/ -v
	@echo "✅ Tests completed"

# Development server (with auto-reload)
dev:
	@echo "🔧 Starting development server with auto-reload..."
	@python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Production server (without reload)
prod:
	@echo "🏭 Starting production server..."
	@python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Show logs
logs:
	@echo "📄 Showing server logs..."
	@if [ -f logs/app.log ]; then tail -f logs/app.log; else echo "No log file found"; fi

# Kill all server processes (emergency)
kill:
	@echo "💀 Force killing all server processes..."
	@pkill -f "uvicorn app.main:app" || true
	@pkill -f "app.main" || true
	@lsof -ti:8000 | xargs -r kill -9 || true
	@rm -f server.pid
	@echo "✅ All server processes killed"
