"""
API Request/Response logging middleware for development/testing.
Logs all API calls to a local file with timestamps, request details, and responses.
"""

import os
import json
import time
from datetime import datetime
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message

LOG_FILE = os.path.join(os.path.dirname(__file__), "api-logs.txt")


def init_log_file():
    """Initialize/clear the log file on startup."""
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"=== Backend API Logs ===\n")
        f.write(f"Started: {datetime.now().isoformat()}\n")
        f.write("=" * 50 + "\n\n")


def log_to_file(entry: str):
    """Append a log entry to the file."""
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}]\n{entry}\n{'─' * 50}\n\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)


class APILoggerMiddleware(BaseHTTPMiddleware):
    """Middleware to log all API requests and responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip logging for static files and non-API routes
        path = request.url.path
        api_paths = ["/users", "/tasks", "/energy", "/api"]
        
        if not any(path.startswith(p) for p in api_paths):
            return await call_next(request)
        
        # Capture request details
        method = request.method
        url = str(request.url)
        
        # Read request body
        request_body = ""
        try:
            body_bytes = await request.body()
            if body_bytes:
                try:
                    request_body = json.dumps(json.loads(body_bytes), indent=2)
                except json.JSONDecodeError:
                    request_body = body_bytes.decode("utf-8", errors="replace")
        except Exception:
            request_body = "[Could not read request body]"
        
        # Time the request
        start_time = time.time()
        
        # Call the actual endpoint
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Capture response body
        response_body = ""
        response_body_bytes = b""
        
        async for chunk in response.body_iterator:
            response_body_bytes += chunk
        
        try:
            response_body = response_body_bytes.decode("utf-8")
            try:
                response_body = json.dumps(json.loads(response_body), indent=2)
            except json.JSONDecodeError:
                pass  # Keep as plain text
        except Exception:
            response_body = "[Could not decode response body]"
        
        # Build log entry
        log_parts = [
            f"{method} {path}",
            f"Full URL: {url}",
            f"Status: {response.status_code}",
            f"Duration: {duration_ms:.2f}ms",
        ]
        
        if request_body:
            log_parts.append(f"Request Body:\n{request_body}")
        
        log_parts.append(f"Response:\n{response_body}")
        
        log_entry = "\n".join(log_parts)
        log_to_file(log_entry)
        
        print(f"📝 Logged: {method} {path} [{response.status_code}] ({duration_ms:.2f}ms)")
        
        # Return a new response with the captured body
        return Response(
            content=response_body_bytes,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type
        )
