import asyncio
import time

from redis.asyncio import Redis

from app.core.config import get_settings


class RateLimiter:
    def __init__(self) -> None:
        self._redis: Redis | None = None
        self._memory: dict[str, tuple[int, int]] = {}
        self._lock = asyncio.Lock()

    async def _redis_client(self) -> Redis:
        if self._redis is None:
            self._redis = Redis.from_url(get_settings().redis_url, encoding="utf-8", decode_responses=True)
        return self._redis

    async def allow(self, key: str, limit: int) -> tuple[bool, int]:
        bucket = int(time.time() // 60)
        redis_key = f"smartdispo:rate:{bucket}:{key}"
        try:
            client = await self._redis_client()
            count = await client.incr(redis_key)
            if count == 1:
                await client.expire(redis_key, 65)
            return count <= limit, max(0, limit - count)
        except Exception:
            async with self._lock:
                count, stored_bucket = self._memory.get(key, (0, bucket))
                if stored_bucket != bucket:
                    count = 0
                count += 1
                self._memory[key] = (count, bucket)
                if len(self._memory) > 10000:
                    self._memory = {
                        item_key: value for item_key, value in self._memory.items() if value[1] == bucket
                    }
                return count <= limit, max(0, limit - count)


rate_limiter = RateLimiter()
