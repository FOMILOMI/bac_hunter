from __future__ import annotations
import asyncio
import logging
from typing import Optional
import httpx

from .config import Settings
from .rate_limiter import RateLimiter
from .utils import host_of, jitter

log = logging.getLogger("http")


class HttpClient:
    def __init__(self, settings: Settings):
        self.s = settings
        limits = httpx.Limits(max_connections=settings.max_concurrency, max_keepalive_connections=settings.max_concurrency)
        self._client = httpx.AsyncClient(timeout=self.s.timeout_seconds, trust_env=True, limits=limits, proxies=self.s.proxy)
        self._rl = RateLimiter(self.s.max_rps, self.s.per_host_rps)
        self._sem = asyncio.Semaphore(self.s.max_concurrency)

    async def close(self):
        await self._client.aclose()

    async def get(self, url: str, headers: Optional[dict] = None) -> httpx.Response:
        host = host_of(url)
        async with self._sem:
            await self._rl.acquire(host)
            await jitter(self.s.random_jitter_ms)
            for attempt in range(self.s.retry_times + 1):
                try:
                    r = await self._client.get(url, headers=headers)
                    log.debug("GET %s -> %s", url, r.status_code)
                    return r
                except Exception as e:
                    if attempt >= self.s.retry_times:
                        raise
                    await asyncio.sleep(0.5 * (attempt + 1))

