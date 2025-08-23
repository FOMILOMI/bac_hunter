import asyncio
import time
from collections import defaultdict
from typing import Dict


class TokenBucket:
    def __init__(self, rate: float, burst: float | None = None):
        self.rate = rate
        self.tokens = burst if burst is not None else max(1.0, rate)
        self.updated = time.perf_counter()
        self.lock = asyncio.Lock()

    async def take(self, amount: float = 1.0):
        async with self.lock:
            now = time.perf_counter()
            elapsed = now - self.updated
            self.updated = now
            self.tokens = min(self.tokens + elapsed * self.rate, max(self.rate, 10.0))
            while self.tokens < amount:
                need = amount - self.tokens
                wait = need / self.rate if self.rate > 0 else 0.5
                await asyncio.sleep(min(0.5, wait))
                now2 = time.perf_counter()
                gained = (now2 - self.updated) * self.rate
                self.tokens += gained
                self.updated = now2
            self.tokens -= amount


class RateLimiter:
    def __init__(self, global_rps: float, per_host_rps: float):
        self.global_bucket = TokenBucket(global_rps, burst=global_rps)
        self.host_buckets: Dict[str, TokenBucket] = defaultdict(lambda: TokenBucket(per_host_rps, burst=per_host_rps))

    async def acquire(self, host: str):
        await asyncio.gather(
            self.global_bucket.take(1.0),
            self.host_buckets[host].take(1.0),
        )

