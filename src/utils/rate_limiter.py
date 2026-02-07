"""速率限制模組

提供 API 請求的速率限制功能，防止過度請求。
"""

import asyncio
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone


@dataclass
class RateLimitConfig:
    """速率限制配置"""

    requests_per_minute: int = 60
    requests_per_second: int = 10
    burst_size: int = 5


@dataclass
class RateLimiter:
    """速率限制器

    使用 Token Bucket 演算法限制請求速率。

    Usage:
        limiter = RateLimiter()
        async with limiter.acquire("newsapi"):
            # 執行 API 請求
            ...
    """

    config: RateLimitConfig = field(default_factory=RateLimitConfig)
    _buckets: dict[str, list[datetime]] = field(
        default_factory=lambda: defaultdict(list)
    )
    _locks: dict[str, asyncio.Lock] = field(
        default_factory=lambda: defaultdict(asyncio.Lock)
    )

    async def acquire(self, key: str = "default") -> None:
        """獲取請求許可

        如果超過速率限制，會等待直到可以繼續。

        Args:
            key: 限制器 key (用於區分不同 API)
        """
        async with self._locks[key]:
            now = datetime.now(timezone.utc)
            window_start = now - timedelta(minutes=1)

            # 清除過期的請求記錄
            self._buckets[key] = [ts for ts in self._buckets[key] if ts > window_start]

            # 檢查是否超過限制
            if len(self._buckets[key]) >= self.config.requests_per_minute:
                # 計算需要等待的時間
                oldest = self._buckets[key][0]
                wait_time = (oldest + timedelta(minutes=1) - now).total_seconds()
                if wait_time > 0:
                    await asyncio.sleep(wait_time)

            # 記錄這次請求
            self._buckets[key].append(datetime.now(timezone.utc))

    async def __aenter__(self) -> "RateLimiter":
        return self

    async def __aexit__(self, *args: object) -> None:
        pass


class RateLimiterContext:
    """速率限制上下文管理器"""

    def __init__(self, limiter: RateLimiter, key: str = "default") -> None:
        self.limiter = limiter
        self.key = key

    async def __aenter__(self) -> None:
        await self.limiter.acquire(self.key)

    async def __aexit__(self, *args: object) -> None:
        pass


# 全域速率限制器實例
_global_limiter: RateLimiter | None = None
_limiter_lock = threading.Lock()


def get_rate_limiter() -> RateLimiter:
    """取得全域速率限制器"""
    global _global_limiter
    if _global_limiter is None:
        with _limiter_lock:
            if _global_limiter is None:
                _global_limiter = RateLimiter()
    return _global_limiter


async def rate_limit(key: str = "default") -> None:
    """簡便的速率限制函數

    Usage:
        await rate_limit("newsapi")
        # 執行 API 請求
    """
    limiter = get_rate_limiter()
    await limiter.acquire(key)
