"""
Centralized logging utilities for the Instagram Downloader API.
Provides structured logging, request/response logging, and error handling.
"""

import logging
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from app.config import AppConfig


class StructuredLogger:
    """
    Structured logger for consistent logging across the application.
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.name = name
    
    def _log_structured(self, level: int, message: str, **kwargs):
        """
        Log a structured message with additional context.
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": logging.getLevelName(level),
            "logger": self.name,
            "message": message,
            **kwargs
        }
        
        if level >= logging.ERROR:
            self.logger.error(json.dumps(log_data, default=str))
        elif level >= logging.WARNING:
            self.logger.warning(json.dumps(log_data, default=str))
        elif level >= logging.INFO:
            self.logger.info(json.dumps(log_data, default=str))
        else:
            self.logger.debug(json.dumps(log_data, default=str))
    
    def info(self, message: str, **kwargs):
        """Log info message with context."""
        self._log_structured(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with context."""
        self._log_structured(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with context."""
        self._log_structured(logging.ERROR, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with context."""
        self._log_structured(logging.DEBUG, message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with context."""
        self._log_structured(logging.ERROR, message, **kwargs)


class RequestResponseLogger:
    """
    Logger for API request/response logging.
    """
    
    def __init__(self):
        self.logger = StructuredLogger("api.requests")
    
    def log_request(self, method: str, path: str, headers: Dict[str, str], 
                   body: Optional[str] = None, client_ip: str = None):
        """
        Log incoming API request.
        """
        self.logger.info(
            "API Request",
            method=method,
            path=path,
            client_ip=client_ip,
            headers=dict(headers) if headers else {},
            body_length=len(body) if body else 0
        )
    
    def log_response(self, method: str, path: str, status_code: int, 
                    response_time: float, response_size: int = None):
        """
        Log API response.
        """
        self.logger.info(
            "API Response",
            method=method,
            path=path,
            status_code=status_code,
            response_time_ms=round(response_time * 1000, 2),
            response_size=response_size
        )
    
    def log_error(self, method: str, path: str, error: Exception, 
                 client_ip: str = None):
        """
        Log API error.
        """
        self.logger.error(
            "API Error",
            method=method,
            path=path,
            error_type=type(error).__name__,
            error_message=str(error),
            client_ip=client_ip
        )


class ServiceLogger:
    """
    Logger for service operations.
    """
    
    def __init__(self, service_name: str):
        self.logger = StructuredLogger(f"service.{service_name}")
        self.service_name = service_name
    
    def log_operation_start(self, operation: str, **kwargs):
        """Log start of service operation."""
        self.logger.info(
            f"{self.service_name} operation started",
            operation=operation,
            **kwargs
        )
    
    def log_operation_success(self, operation: str, duration: float, **kwargs):
        """Log successful service operation."""
        self.logger.info(
            f"{self.service_name} operation completed",
            operation=operation,
            duration_ms=round(duration * 1000, 2),
            **kwargs
        )
    
    def log_operation_error(self, operation: str, error: Exception, **kwargs):
        """Log service operation error."""
        self.logger.error(
            f"{self.service_name} operation failed",
            operation=operation,
            error_type=type(error).__name__,
            error_message=str(error),
            **kwargs
        )
    
    def log_service_status(self, status: str, **kwargs):
        """Log service status change."""
        self.logger.info(
            f"{self.service_name} status changed",
            status=status,
            **kwargs
        )
    
    def info(self, message: str, **kwargs):
        """Log info message with context."""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with context."""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with context."""
        self.logger.error(message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with context."""
        self.logger.debug(message, **kwargs)


def get_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger instance.
    """
    return StructuredLogger(name)


def get_request_logger() -> RequestResponseLogger:
    """
    Get request/response logger instance.
    """
    return RequestResponseLogger()


def get_service_logger(service_name: str) -> ServiceLogger:
    """
    Get service logger instance.
    """
    return ServiceLogger(service_name)
