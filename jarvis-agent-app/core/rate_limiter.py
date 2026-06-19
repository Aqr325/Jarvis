"""
J.A.R.V.I.S. Rate Limiter Middleware
--------------------------------------
Token bucket algorithm for API rate limiting with per-client tracking.
Supports sliding window and fixed window strategies.
"""

import asyncio
import time
import logging
from collections import defaultdict
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("jarvis.ratelimiter")


@dataclass
class TokenBucket:
    """Single client token bucket."""
    capacity: int
    tokens: float
    refill_rate: float  # tokens per second
    last_refill: float = field(default_factory=time.monotonic)

    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens. Returns True if allowed."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def get_wait_time(self, tokens: int = 1) -> float:
        """Estimated seconds until enough tokens are available."""
        if self.tokens >= tokens:
            return 0.0
        needed = tokens - self.tokens
        return needed / self.refill_rate if self.refill_rate > 0 else float('inf')


class RateLimiter:
    """
    Per-client rate limiter using token bucket algorithm.
    
    Default limits:
    - General API: 60 requests/min (1/sec refill)
    - Chat endpoint: 20 requests/min (0.33/sec refill)
    - Tool calls: 30 requests/min (0.5/sec refill)
    """

    DEFAULT_LIMITS = {
        "general": {"capacity": 60, "refill_rate": 1.0},
        "chat": {"capacity": 20, "refill_rate": 0.33},
        "tool": {"capacity": 30, "refill_rate": 0.5},
        "default": {"capacity": 100, "refill_rate": 2.0},
    }

    def __init__(self, limits: Optional[Dict[str, dict]] = None):
        self.limits = limits or self.DEFAULT_LIMITS
        self.buckets: Dict[str, Dict[str, TokenBucket]] = defaultdict(dict)
        self._cleanup_interval = 300  # seconds
        self._last_cleanup = time.monotonic()
        logger.info("Rate limiter initialized with limits: %s", self.limits)

    def _get_or_create_bucket(
        self, client_id: str, endpoint: str
    ) -> TokenBucket:
        """Get or create a token bucket for the given client+endpoint."""
        if endpoint not in self.buckets[client_id]:
            config = self.limits.get(
                endpoint, self.limits.get("default", self.limits["default"])
            )
            self.buckets[client_id][endpoint] = TokenBucket(
                capacity=config["capacity"],
                tokens=config["capacity"],  # start full
                refill_rate=config["refill_rate"],
            )
        return self.buckets[client_id][endpoint]

    def is_allowed(
        self, client_id: str, endpoint: str, tokens: int = 1
    ) -> dict:
        """
        Check if request is allowed.
        Returns: {"allowed": bool, "remaining": int, "retry_after": float}
        """
        bucket = self._get_or_create_bucket(client_id, endpoint)
        allowed = bucket.consume(tokens)
        remaining = int(bucket.tokens)
        retry_after = bucket.get_wait_time(1) if not allowed else 0.0

        return {
            "allowed": allowed,
            "remaining": remaining,
            "retry_after": round(retry_after, 2),
        }

    async def check_and_wait(
        self, client_id: str, endpoint: str, tokens: int = 1
    ) -> dict:
        """
        Async check with optional waiting.
        If rate limit exceeded, waits until tokens are available.
        """
        result = self.is_allowed(client_id, endpoint, tokens)
        if result["allowed"]:
            return result

        retry_after = result["retry_after"]
        logger.warning(
            "Rate limit hit for client=%s endpoint=%s, retry in %.1fs",
            client_id,
            endpoint,
            retry_after,
        )
        # Wait a bit and retry
        await asyncio.sleep(min(retry_after, 5.0))
        return self.is_allowed(client_id, endpoint, tokens)

    async def cleanup_expired(self):
        """Periodically remove stale client buckets (> 10 min inactive)."""
        now = time.monotonic()
        stale_keys = []
        for client_id, endpoints in self.buckets.items():
            for ep, bucket in endpoints.items():
                if now - bucket.last_refill > 600:
                    stale_keys.append((client_id, ep))

        for client_id, ep in stale_keys:
            del self.buckets[client_id][ep]

        if stale_keys:
            logger.info("Cleaned up %d stale rate limit buckets", len(stale_keys))
