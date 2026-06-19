"""
J.A.R.V.I.S. Timeout Middleware
---------------------------------
Response timeout control with configurable per-endpoint deadlines.
Uses asyncio.wait_for with fallback timeout exceptions.
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass

logger = logging.getLogger("jarvis.timeout")


@dataclass
class EndpointConfig:
    """Configuration for a single endpoint's timeout."""
    timeout_seconds: float
    max_retries: int = 0
    retry_delay: float = 0.5
    circuit_breaker_threshold: int = 5  # fail N times to open circuit


class TimeoutManager:
    """
    Manages per-endpoint timeouts and circuit breaker patterns.
    
    Default timeouts:
    - /api/chat: 10s
    - /api/tool: 15s
    - /api/data/*: 30s
    - /api/weather: 20s
    - default: 5s
    """

    DEFAULT_ENDPOINTS = {
        "chat": EndpointConfig(timeout_seconds=10, max_retries=1),
        "tool": EndpointConfig(timeout_seconds=15, max_retries=1),
        "data": EndpointConfig(timeout_seconds=30, max_retries=0),
        "weather": EndpointConfig(timeout_seconds=20, max_retries=0),
        "default": EndpointConfig(timeout_seconds=5),
    }

    def __init__(self, configs: Optional[Dict[str, EndpointConfig]] = None):
        self.configs = configs or self.DEFAULT_ENDPOINTS
        self._circuit_states: Dict[str, int] = {}  # endpoint -> consecutive failures
        self._circuit_thresholds: Dict[str, int] = {}
        for name, cfg in self.configs.items():
            if hasattr(cfg, "circuit_breaker_threshold"):
                self._circuit_thresholds[name] = cfg.circuit_breaker_threshold

    def _get_config(self, endpoint: str) -> EndpointConfig:
        """Get config for endpoint, falling back to default."""
        for pattern, cfg in self.configs.items():
            if endpoint.startswith(pattern) or pattern == "default":
                return cfg
        return self.configs["default"]

    async def execute_with_timeout(
        self, coro, endpoint: str, client_id: str = "unknown"
    ) -> Any:
        """
        Execute coroutine with timeout. Raises asyncio.TimeoutError if exceeded.
        Implements circuit breaker pattern for recurring failures.
        """
        config = self._get_config(endpoint)
        
        # Check circuit breaker
        cb_threshold = self._circuit_thresholds.get(endpoint, 0)
        if cb_threshold > 0 and self._circuit_states.get(endpoint, 0) >= cb_threshold:
            logger.error(
                "Circuit OPEN for endpoint=%s (%d consecutive failures)",
                endpoint,
                self._circuit_states[endpoint],
            )
            raise asyncio.TimeoutError(
                f"Circuit breaker open for {endpoint}. Try again later."
            )

        start_time = time.monotonic()
        try:
            result = await asyncio.wait_for(coro, timeout=config.timeout_seconds)
            
            # Reset circuit breaker on success
            if endpoint in self._circuit_states:
                self._circuit_states[endpoint] = 0
            
            elapsed = time.monotonic() - start_time
            logger.debug(
                "Endpoint %s completed in %.2fs (timeout=%ds)",
                endpoint, elapsed, config.timeout_seconds,
            )
            return result

        except asyncio.TimeoutError:
            elapsed = time.monotonic() - start_time
            logger.warning(
                "Endpoint %s TIMED OUT after %.2fs (client=%s)",
                endpoint, elapsed, client_id,
            )
            # Increment circuit breaker
            self._circuit_states[endpoint] = (
                self._circuit_states.get(endpoint, 0) + 1
            )
            raise

    async def execute_with_retry(
        self, coro_func: Callable, endpoint: str, *args, **kwargs
    ) -> Any:
        """Execute with retry logic (for endpoints that support it)."""
        config = self._get_config(endpoint)
        if config.max_retries == 0:
            return await coro_func(*args, **kwargs)

        last_exception = None
        for attempt in range(config.max_retries + 1):
            try:
                return await self.execute_with_timeout(
                    coro_func(*args, **kwargs), endpoint, kwargs.get("client_id", "unknown")
                )
            except (asyncio.TimeoutError, Exception) as e:
                last_exception = e
                if attempt < config.max_retries:
                    logger.info(
                        "Retry %d/%d for endpoint=%s: %s",
                        attempt + 1, config.max_retries, endpoint, str(e)[:50],
                    )
                    await asyncio.sleep(config.retry_delay * (attempt + 1))
        
        raise last_exception

    def get_circuit_status(self, endpoint: str) -> Dict[str, Any]:
        """Get current circuit breaker status for an endpoint."""
        threshold = self._circuit_thresholds.get(endpoint, 0)
        failures = self._circuit_states.get(endpoint, 0)
        return {
            "endpoint": endpoint,
            "failures": failures,
            "threshold": threshold,
            "state": "OPEN" if failures >= threshold else "CLOSED",
        }


class TimeoutMiddleware:
    """
    Wraps FastAPI requests with timeout enforcement.
    Usage: await middleware.enforce(request_handler, endpoint, client_id)
    """

    def __init__(self, timeout_manager: Optional[TimeoutManager] = None):
        self.manager = timeout_manager or TimeoutManager()

    async def enforce(
        self, handler: Callable, endpoint: str, client_id: str = "unknown"
    ) -> Any:
        """Wrap any async handler with timeout enforcement."""
        try:
            result = await self.manager.execute_with_timeout(
                handler(), endpoint, client_id
            )
            return result
        except asyncio.TimeoutError:
            logger.error("Request to %s timed out for client %s", endpoint, client_id)
            return {
                "error": "Request timeout",
                "message": f"Service unavailable. Please try again later.",
                "endpoint": endpoint,
            }
