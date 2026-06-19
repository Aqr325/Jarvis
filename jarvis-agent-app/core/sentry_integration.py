"""
Sentry Integration for J.A.R.V.I.S. Agent
==========================================
Real-time error tracking and performance monitoring.

Setup:
    1. Set SENTRY_DSN environment variable
    2. Optional: Set SENTRY_ENVIRONMENT (development/staging/production)
    3. Optional: Set SENTRY_TRACES_SAMPLE_RATE (0.0-1.0)

Example:
    export SENTRY_DSN="https://xxx@xxx.ingest.sentry.io/xxx"
    export SENTRY_ENVIRONMENT="production"
    export SENTRY_TRACES_SAMPLE_RATE="0.1"
"""

import os
import logging
from typing import Optional, Dict, Any


def init_sentry(app_name: str = "jarvis-agent") -> bool:
    """
    Initialize Sentry SDK.
    
    Returns:
        bool: True if Sentry was initialized, False if not configured.
    """
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        logging.getLogger("jarvis.sentry").debug("Sentry DSN not configured, skipping initialization")
        return False
    
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration
        from sentry_sdk.integrations.aiohttp import AioHttpIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
        
        # Configure Sentry
        sentry_sdk.init(
            dsn=dsn,
            app_name=app_name,
            environment=os.getenv("SENTRY_ENVIRONMENT", "development"),
            
            # Performance monitoring
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            
            # Integrations
            integrations=[
                FastApiIntegration(
                    transaction_style="url",
                    middleware_error=False,
                ),
                AioHttpIntegration(),
                LoggingIntegration(
                    level=logging.INFO,
                    event_level=logging.ERROR,
                ),
            ],
            
            # Error filtering
            ignore_errors=[
                # Ignore common expected errors
                "fastapi.exceptions.RequestValidationError",
            ],
            
            # Before send callback for custom filtering
            before_send=_before_send,
            before_breadcrumb=_before_breadcrumb,
        )
        
        logging.getLogger("jarvis.sentry").info("Sentry initialized successfully")
        return True
        
    except ImportError:
        logging.getLogger("jarvis.sentry").warning(
            "Sentry SDK not installed. Install with: pip install sentry-sdk[fastapi]"
        )
        return False
    except Exception as e:
        logging.getLogger("jarvis.sentry").error(f"Failed to initialize Sentry: {e}")
        return False


def _before_send(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Callback to filter events before sending to Sentry.
    
    Args:
        event: The error event
        hint: Additional context
        
    Returns:
        Modified event or None to discard
    """
    # Filter out health check errors
    if event.get("request", {}).get("url") in ["/health", "/api/status"]:
        return None
    
    # Add context for better debugging
    if "tags" not in event:
        event["tags"] = {}
    event["tags"]["application"] = "jarvis-agent"
    
    # Redact sensitive data
    if "request" in event:
        request = event["request"]
        if "headers" in request:
            headers = request["headers"]
            # Redact sensitive headers
            for key in ["authorization", "cookie", "set-cookie", "x-api-key"]:
                if key in headers:
                    headers[key] = "[REDACTED]"
    
    return event


def _before_breadcrumb(crumb: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Callback to filter breadcrumbs.
    
    Args:
        crumb: The breadcrumb
        hint: Additional context
        
    Returns:
        Modified breadcrumb or None to discard
    """
    # Skip too verbose breadcrumbs
    if crumb.get("category") == "http.client" and crumb.get("data", {}).get("status_code") == 200:
        return None
    
    return crumb


def capture_exception(message: str, **context) -> Optional[str]:
    """
    Capture an exception and send to Sentry.
    
    Args:
        message: Error message
        **context: Additional context to attach
        
    Returns:
        Event ID if sent, None otherwise
    """
    try:
        import sentry_sdk
        event_id = sentry_sdk.capture_exception(Exception(message))
        
        if context:
            sentry_sdk.set_context("additional_context", context)
        
        return event_id
    except Exception:
        return None


def capture_message(message: str, level: str = "error", **context) -> Optional[str]:
    """
    Capture a message and send to Sentry.
    
    Args:
        message: Message to send
        level: Severity level (info, warning, error, fatal)
        **context: Additional context
        
    Returns:
        Event ID if sent, None otherwise
    """
    try:
        import sentry_sdk
        event_id = sentry_sdk.capture_message(message, level=level)
        
        if context:
            sentry_sdk.set_context("additional_context", context)
        
        return event_id
    except Exception:
        return None


def set_user_context(user_id: str, **user_data):
    """
    Set user context for error tracking.
    
    Args:
        user_id: User identifier
        **user_data: Additional user data
    """
    try:
        import sentry_sdk
        sentry_sdk.set_user({"id": user_id, **user_data})
    except Exception:
        pass


def set_transaction_context(transaction_name: str, op: str = "http.server"):
    """
    Set transaction context for performance monitoring.
    
    Args:
        transaction_name: Name of the transaction
        op: Operation type
    """
    try:
        import sentry_sdk
        sentry_sdk.set_transaction_name(transaction_name)
    except Exception:
        pass
