import asyncio
import time


class TokenBucketRateLimiter:
    """Async-safe token bucket rate limiter.

    Tokens refill continuously at a fixed rate. Each acquire() call consumes
    one token. If no tokens remain, the call returns False immediately.
    """

    def __init__(self, max_tokens: int, refill_period: float):
        """
        Args:
            max_tokens: Maximum tokens (requests) allowed per period.
            refill_period: Period in seconds over which all tokens fully refill.
        """
        self._max_tokens = max_tokens
        self._refill_period = refill_period
        self._tokens = float(max_tokens)
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        refill_amount = (elapsed / self._refill_period) * self._max_tokens
        self._tokens = min(self._max_tokens, self._tokens + refill_amount)
        self._last_refill = now

    async def acquire(self) -> bool:
        """Consume one token. Returns True if acquired, False if rate-limited."""
        async with self._lock:
            self._refill()
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return True
            return False
