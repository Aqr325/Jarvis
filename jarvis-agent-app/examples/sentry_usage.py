"""
Sentry Usage Examples for J.A.R.V.I.S. Agent
==============================================
"""

# Example 1: Basic Sentry Integration
# ---------------------------------------------------------------------------

# In server.py, add after imports:
"""
from core.sentry_integration import init_sentry

# Initialize Sentry
sentry_initialized = init_sentry()
"""

# Then set environment variable:
# export SENTRY_DSN="https://xxx@xxx.ingest.sentry.io/xxx"
# export SENTRY_ENVIRONMENT="production"


# Example 2: Manual Error Reporting
# ---------------------------------------------------------------------------

from core.sentry_integration import capture_exception, capture_message, set_user_context

try:
    # Some code that might fail
    result = risky_operation()
except Exception as e:
    # Capture exception with context
    event_id = capture_exception(
        "Database connection failed",
        user_id="user_123",
        operation="query",
        query="SELECT * FROM users"
    )
    print(f"Error reported to Sentry: {event_id}")


# Example 3: User Context
# ---------------------------------------------------------------------------

# Set user context before an operation
set_user_context(
    user_id="user_123",
    username="john_doe",
    email="john@example.com",
    account_type="premium"
)

# Now any errors will include user context
do_something()


# Example 4: Custom Error Reporting in Endpoints
# ---------------------------------------------------------------------------

from fastapi import Request
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from core.sentry_integration import capture_exception

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Report to Sentry
    capture_exception(
        str(exc),
        path=str(request.url.path),
        method=request.method,
        headers=dict(request.headers),
        query_params=dict(request.query_params),
    )
    
    # Return error response
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error"},
    )


# Example 5: Performance Monitoring
# ---------------------------------------------------------------------------

from core.sentry_integration import set_transaction_context

@app.get("/api/heavy-operation")
async def heavy_operation():
    # Set transaction name for performance tracking
    set_transaction_context("heavy_operation")
    
    # Your code here
    result = perform_complex_calculation()
    
    return {"result": result}


# Example 6: Before Send Hook (Custom Filtering)
# ---------------------------------------------------------------------------

# In sentry_integration.py, the _before_send function can be customized:

def _before_send(event, hint):
    # Skip health check errors
    if event.get("request", {}).get("url") in ["/health"]:
        return None
    
    # Skip specific exceptions
    if isinstance(hint.get("exc_info", (None, None))[1], 
                  ConnectionRefusedError):
        return None
    
    # Add custom context
    event["tags"]["server"] = os.getenv("HOSTNAME", "unknown")
    
    return event


# Example 7: Testing Sentry Integration
# ---------------------------------------------------------------------------

import pytest
from unittest.mock import patch

def test_sentry_integration():
    """Test that errors are reported to Sentry."""
    with patch('sentry_sdk.capture_exception') as mock_capture:
        # Trigger an error
        try:
            1 / 0
        except ZeroDivisionError:
            capture_exception("Division error", test="case")
        
        # Verify Sentry was called
        mock_capture.assert_called_once()
        assert "Division error" in str(mock_capture.call_args)


# Example 8: Breadcrumb Logging
# ---------------------------------------------------------------------------

import sentry_sdk

# Add a breadcrumb before an operation
sentry_sdk.add_breadcrumb(
    category="operation",
    message="Starting data processing",
    level="info",
    data={"batch_size": 100, "source": "api"},
)

# Do the operation
process_data()

# Add success breadcrumb
sentry_sdk.add_breadcrumb(
    category="operation",
    message="Data processing completed",
    level="info",
)


# Example 9: Monitoring Configuration
# ---------------------------------------------------------------------------

# .env file:
"""
# Sentry Configuration
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% of transactions sampled

# Optional: Release version
SENTRY_RELEASE=v0.2.0
"""


# Example 10: Dashboard Integration
# ---------------------------------------------------------------------------

# After setting up Sentry, you can:
# 1. View error trends at sentry.io
# 2. Set up alerts for error rate spikes
# 3. Create dashboards for key metrics
# 4. Integrate with issue trackers (Jira, GitHub)

# Recommended alerts:
# - Error rate > 5% in 5 minutes
# - > 100 errors in 1 hour
# - Any P0/P1 errors
