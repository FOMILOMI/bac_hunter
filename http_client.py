from __future__ import annotations
import asyncio
import logging
from typing import Optional, Dict, Any, Callable, Awaitable, List
import httpx
import time

try:
    from .config import Settings
    from .rate_limiter import RateLimiter, AdaptiveRateLimiter
    from .utils import host_of, jitter, pick_ua
    from .monitoring.stats_collector import StatsCollector
    from .safety.throttle_calibrator import ThrottleCalibrator
    from .safety.waf_detector import WAFDetector
    from .logging_setup import set_log_context
except Exception:
    from config import Settings  # type: ignore
    from rate_limiter import RateLimiter, AdaptiveRateLimiter  # type: ignore
    from utils import host_of, jitter, pick_ua  # type: ignore
    from monitoring.stats_collector import StatsCollector  # type: ignore
    from safety.throttle_calibrator import ThrottleCalibrator  # type: ignore
    from safety.waf_detector import WAFDetector  # type: ignore
    from logging_setup import set_log_context  # type: ignore

log = logging.getLogger("http")


class HttpClient:
    def __init__(self, settings: Settings):
        self.s = settings
        limits = httpx.Limits(max_connections=settings.max_concurrency, max_keepalive_connections=settings.max_concurrency)
        self._client = httpx.AsyncClient(timeout=self.s.timeout_seconds, trust_env=True, proxy=self.s.proxy, limits=limits)
        # Use adaptive limiter when enabled
        if self.s.enable_adaptive_throttle:
            self._rl = AdaptiveRateLimiter(self.s.max_rps, self.s.per_host_rps, None)  # will set calibrator below
        else:
            self._rl = RateLimiter(self.s.max_rps, self.s.per_host_rps)
        self._sem = asyncio.Semaphore(self.s.max_concurrency)
        self._identity_semaphores: Dict[str, asyncio.Semaphore] = {}
        self._stats = StatsCollector()
        self._cal = ThrottleCalibrator(initial_rps=self.s.max_rps) if self.s.enable_adaptive_throttle else None
        if isinstance(self._rl, AdaptiveRateLimiter):
            self._rl.calibrator = self._cal
        self._waf = WAFDetector() if self.s.enable_waf_detection else None
        # simple in-memory GET cache
        self._cache: Dict[str, tuple[float, httpx.Response]] = {}
        # simple circuit breaker per route
        self._route_failures: Dict[str, int] = {}
        self._route_paused_until: Dict[str, float] = {}
        # request mutators middleware chain
        self._mutators: List[Callable[[str, str, Dict[str, str], Any, Any], Awaitable[tuple[str, str, Dict[str, str], Any, Any]]]] = []

    async def close(self):
        await self._client.aclose()

    @property
    def stats(self) -> StatsCollector:
        """Expose request statistics for orchestration safety controls and progress."""
        return self._stats

    def _prepare_headers(self, headers: Optional[Dict[str, str]]) -> Dict[str, str]:
        h: Dict[str, str] = {}
        if headers:
            h.update(headers)
        # UA rotation when requested or missing
        if self.s.enable_ua_rotation:
            if self.s.ua_rotate_per_request or "User-Agent" not in h:
                h["User-Agent"] = pick_ua()
        # tag identity if not present
        if "X-BH-Identity" not in h:
            h["X-BH-Identity"] = headers.get("X-BH-Identity") if headers else "unknown"
        return h

    def _cache_get(self, url: str) -> Optional[httpx.Response]:
        if not self.s.cache_enabled:
            return None
        item = self._cache.get(url)
        if not item:
            return None
        ts, resp = item
        if (time.time() - ts) > self.s.cache_ttl_seconds:
            try:
                del self._cache[url]
            except Exception:
                pass
            return None
        return resp

    def _cache_put(self, url: str, resp: httpx.Response):
        if not self.s.cache_enabled:
            return
        try:
            if len(self._cache) >= max(10, self.s.cache_max_entries):
                # naive eviction: pop an arbitrary item
                self._cache.pop(next(iter(self._cache)))
            self._cache[url] = (time.time(), resp)
        except Exception:
            pass

    async def _respect_limits(self, host: str, path: str):
        # token buckets
        await self._rl.acquire(host, path)
        # adaptive throttle delay
        if self._cal is not None:
            await asyncio.sleep(self._cal.get_delay())
        # random jitter
        await jitter(self.s.random_jitter_ms)

    def _record(self, url: str, method: str, status_code: int, elapsed_ms: float, size: int, identity: str):
        self._stats.record_request(url=url, method=method, status_code=status_code, response_time_ms=elapsed_ms, response_size=size, identity=identity)
        if self._cal is not None:
            self._cal.record_response(status_code, elapsed_ms / 1000.0)

    def add_mutator(self, fn: Callable[[str, str, Dict[str, str], Any, Any], Awaitable[tuple[str, str, Dict[str, str], Any, Any]]]) -> None:
        self._mutators.append(fn)

    async def _request(self, method: str, url: str, *, headers: Optional[dict] = None, data: Any = None, json: Any = None) -> httpx.Response:
        host = host_of(url)
        path = httpx.URL(url).raw_path.decode("utf-8", errors="ignore") if hasattr(httpx, "URL") else "/"
        async with self._sem:
            # GET cache check
            if method.upper() == "GET":
                cached = self._cache_get(url)
                if cached is not None:
                    return cached
            # circuit breaker pause check
            now = time.time()
            paused_until = self._route_paused_until.get(f"{host}{path}")
            if paused_until and now < paused_until:
                raise httpx.RemoteProtocolError("circuit-open")

            await self._respect_limits(host, path)
            h = self._prepare_headers(headers)
            last_exc: Optional[Exception] = None
            for attempt in range(self.s.retry_times + 1):
                start = time.perf_counter()
                try:
                    # per-identity concurrency cap
                    ident = h.get("X-BH-Identity", "unknown")
                    if ident not in self._identity_semaphores:
                        self._identity_semaphores[ident] = asyncio.Semaphore(self.s.identity_max_concurrency)
                    async with self._identity_semaphores[ident]:
                        # apply mutators
                        mth, u, hdrs, d, jsn = method, url, h, data, json
                        for mut in self._mutators:
                            mth, u, hdrs, d, jsn = await mut(mth, u, hdrs, d, jsn)
                        # dry-run
                        if self.s.dry_run:
                            log.info("dry-run", extra={"method": mth, "url": u, "headers": hdrs})
                            class _Dummy:
                                status_code = 204
                                headers = {"content-type": "application/json"}
                                content = b""
                                text = ""
                            r = _Dummy()  # type: ignore[assignment]
                        else:
                            r = await self._client.request(mth, u, headers=hdrs, data=d, json=jsn)
                    elapsed_ms = (time.perf_counter() - start) * 1000.0
                    log.debug("req", extra={"method": method.upper(), "url": url, "status": getattr(r, "status_code", -1)})
                    self._record(url, method.upper(), r.status_code, elapsed_ms, len(r.content), ident)
                    # WAF hinting for heavy throttling
                    if self._waf is not None:
                        try:
                            body_sample = r.text[:512] if r.headers.get("content-type","" ).lower().startswith("text/") else ""
                            self._waf.analyze_response(url, r.status_code, dict(r.headers), body_sample)
                        except Exception:
                            pass
                    if method.upper() == "GET" and r.status_code < 400:
                        self._cache_put(url, r)
                    # reset route failures on success-like responses
                    key = f"{host}{path}"
                    if r.status_code < 400:
                        self._route_failures[key] = 0
                    else:
                        self._route_failures[key] = self._route_failures.get(key, 0) + 1
                        if self._route_failures[key] >= 5:
                            # pause this route for a short while
                            self._route_paused_until[key] = time.time() + min(60, 5 * attempt + 10)
                            log.warning("circuit-open", extra={"route": key, "failures": self._route_failures[key]})
                    return r
                except Exception as e:
                    elapsed_ms = (time.perf_counter() - start) * 1000.0
                    self._record(url, method.upper(), 599, elapsed_ms, 0, h.get("X-BH-Identity", "unknown"))
                    last_exc = e
                    if attempt >= self.s.retry_times:
                        break
                    # exponential backoff + jitter
                    await asyncio.sleep(min(2.0, 0.5 * (2 ** attempt)))
            assert last_exc is not None
            raise last_exc

    async def get(self, url: str, headers: Optional[dict] = None) -> httpx.Response:
        return await self._request("GET", url, headers=headers)

    async def post(self, url: str, data: Optional[dict | str | bytes] = None, json: Optional[dict] = None, headers: Optional[dict] = None) -> httpx.Response:
        return await self._request("POST", url, headers=headers, data=data, json=json)

    async def put(self, url: str, data: Optional[dict | str | bytes] = None, json: Optional[dict] = None, headers: Optional[dict] = None) -> httpx.Response:
        return await self._request("PUT", url, headers=headers, data=data, json=json)

    async def patch(self, url: str, data: Optional[dict | str | bytes] = None, json: Optional[dict] = None, headers: Optional[dict] = None) -> httpx.Response:
        return await self._request("PATCH", url, headers=headers, data=data, json=json)

    async def delete(self, url: str, headers: Optional[dict] = None) -> httpx.Response:
        return await self._request("DELETE", url, headers=headers)


