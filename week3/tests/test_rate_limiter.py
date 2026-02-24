import asyncio
import pytest
import time
from unittest.mock import patch

from week3.server.rate_limiter import TokenBucketRateLimiter


@pytest.mark.asyncio
async def test_acquire_within_limit(rate_limiter):
    """Tokens should be available when under the limit."""
    assert await rate_limiter.acquire() is True


@pytest.mark.asyncio
async def test_acquire_exhausts_tokens():
    """After consuming all tokens, acquire should return False."""
    limiter = TokenBucketRateLimiter(max_tokens=3, refill_period=60.0)
    assert await limiter.acquire() is True
    assert await limiter.acquire() is True
    assert await limiter.acquire() is True
    assert await limiter.acquire() is False


@pytest.mark.asyncio
async def test_tokens_refill_over_time():
    """Tokens should gradually refill based on elapsed time."""
    limiter = TokenBucketRateLimiter(max_tokens=2, refill_period=1.0)
    assert await limiter.acquire() is True
    assert await limiter.acquire() is True
    assert await limiter.acquire() is False

    await asyncio.sleep(0.6)
    assert await limiter.acquire() is True


@pytest.mark.asyncio
async def test_tokens_never_exceed_max():
    """Token count should never exceed max_tokens even after long idle."""
    limiter = TokenBucketRateLimiter(max_tokens=5, refill_period=1.0)
    await asyncio.sleep(0.1)
    results = [await limiter.acquire() for _ in range(6)]
    assert results[:5] == [True] * 5
    assert results[5] is False


@pytest.mark.asyncio
async def test_initial_tokens_are_full():
    """A freshly created limiter should have all tokens available."""
    limiter = TokenBucketRateLimiter(max_tokens=10, refill_period=60.0)
    results = [await limiter.acquire() for _ in range(10)]
    assert all(results)
