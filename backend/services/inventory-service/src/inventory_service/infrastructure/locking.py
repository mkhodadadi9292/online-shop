"""Redis distributed lock and a no-op lock for tests/local dev.

The lock uses SET NX PX (atomic acquire with TTL) and a Lua script for
compare-and-delete release, so a holder only ever releases its own lock and a
crashed holder cannot deadlock the key forever (TTL expiry).
"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

import redis.asyncio as aioredis

_RELEASE_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""


class RedisDistributedLock:
    def __init__(self, redis_url: str, ttl_ms: int = 5000) -> None:
        self._redis = aioredis.from_url(redis_url, decode_responses=True)
        self._ttl_ms = ttl_ms

    @asynccontextmanager
    async def acquire(self, key: str):
        token = str(uuid.uuid4())
        acquired = await self._redis.set(key, token, nx=True, px=self._ttl_ms)
        try:
            yield bool(acquired)
        finally:
            if acquired:
                await self._redis.eval(_RELEASE_SCRIPT, 1, key, token)

    async def close(self) -> None:
        await self._redis.aclose()


class NoopLock:
    @asynccontextmanager
    async def acquire(self, key: str):
        yield True
