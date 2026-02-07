"""RateLimiter 測試"""

from src.utils.rate_limiter import RateLimiter, RateLimitConfig, rate_limit


class TestRateLimiter:
    async def test_acquire_basic(self):
        limiter = RateLimiter()
        await limiter.acquire("test")
        assert len(limiter._buckets["test"]) == 1

    async def test_acquire_multiple(self):
        limiter = RateLimiter()
        for _ in range(5):
            await limiter.acquire("test")
        assert len(limiter._buckets["test"]) == 5

    async def test_different_keys_independent(self):
        limiter = RateLimiter()
        await limiter.acquire("api1")
        await limiter.acquire("api2")
        assert len(limiter._buckets["api1"]) == 1
        assert len(limiter._buckets["api2"]) == 1

    async def test_context_manager(self):
        limiter = RateLimiter()
        async with limiter:
            pass  # Should not raise

    async def test_custom_config(self):
        config = RateLimitConfig(requests_per_minute=5)
        limiter = RateLimiter(config=config)
        assert limiter.config.requests_per_minute == 5


class TestRateLimitFunction:
    async def test_rate_limit_function(self):
        await rate_limit("test_func")
        # Should not raise
