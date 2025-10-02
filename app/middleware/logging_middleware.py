"""
Request/response logging middleware for the Instagram Downloader API.
"""

import time
import json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.logger import get_request_logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.
    """
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.logger = get_request_logger()
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/openapi.json", "/favicon.ico"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and response with logging.
        """
        # Skip logging for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Log request
        self.logger.log_request(
            method=request.method,
            path=request.url.path,
            headers=dict(request.headers),
            client_ip=client_ip
        )
        
        # Process request and measure time
        start_time = time.time()
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response
            self.logger.log_response(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                response_time=process_time,
                response_size=response.headers.get("content-length")
            )
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            
            # Log error
            self.logger.log_error(
                method=request.method,
                path=request.url.path,
                error=e,
                client_ip=client_ip
            )
            
            raise
