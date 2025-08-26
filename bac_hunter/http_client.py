from __future__ import annotations
import asyncio
import logging
from typing import Optional, Dict, Any
import httpx
import time

try:
    from .config import Settings
    from .rate_limiter import RateLimiter, AdaptiveRateLimiter
    from .utils import host_of, jitter, pick_ua, normalize_url, dedup_key_for_url, path_for_log
    from .monitoring.stats_collector import StatsCollector
    from .safety.throttle_calibrator import ThrottleCalibrator
    from .safety.waf_detector import WAFDetector
    from .safety.evasion import randomize_header_casing, soft_encode_url
except Exception:  # fallback when imported as top-level module
    from config import Settings
    from rate_limiter import RateLimiter, AdaptiveRateLimiter
    from utils import host_of, jitter, pick_ua, normalize_url, dedup_key_for_url, path_for_log
    from monitoring.stats_collector import StatsCollector
    from safety.throttle_calibrator import ThrottleCalibrator
    from safety.waf_detector import WAFDetector
    from safety.evasion import randomize_header_casing, soft_encode_url

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
        self._stats = StatsCollector()
        self._cal = ThrottleCalibrator(initial_rps=self.s.max_rps) if self.s.enable_adaptive_throttle else None
        if isinstance(self._rl, AdaptiveRateLimiter):
            self._rl.calibrator = self._cal
        self._waf = WAFDetector() if self.s.enable_waf_detection else None
        # simple in-memory GET cache for <400 responses (legacy)
        self._cache: Dict[str, tuple[float, httpx.Response]] = {}
        # smart dedup cache (normalized host+path -> last response)
        self._dedup_cache: Dict[str, httpx.Response] = {}
        # context-aware tested combinations to suppress redundant requests
        self._tested_fingerprints: set[str] = set()

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
        # tag identity if not present; avoid None values
        if "X-BH-Identity" not in h or h.get("X-BH-Identity") is None:
            identity_val = (headers or {}).get("X-BH-Identity")
            h["X-BH-Identity"] = identity_val or "unknown"
        # Optional header casing randomization
        try:
            if self.s.enable_request_randomization:
                h = randomize_header_casing(h)
        except Exception:
            pass
        return h

    def _auth_state_from_headers(self, headers: Dict[str, str]) -> str:
        auth = (headers.get("Authorization") or "").lower()
        if auth.startswith("bearer "):
            return "bearer"
        if headers.get("Cookie"):
            return "cookie"
        return "none"

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

    async def _respect_limits(self, host: str):
        # token buckets
        await self._rl.acquire(host)
        # adaptive throttle delay
        if self._cal is not None:
            await asyncio.sleep(self._cal.get_delay())
        # random jitter
        await jitter(self.s.random_jitter_ms)

    def _record(self, url: str, method: str, status_code: int, elapsed_ms: float, size: int, identity: str):
        self._stats.record_request(url=url, method=method, status_code=status_code, response_time_ms=elapsed_ms, response_size=size, identity=identity)
        if self._cal is not None:
            self._cal.record_response(status_code, elapsed_ms / 1000.0)

    def _build_context_fingerprint(self, url: str, method: str, headers: Dict[str, str], context: Optional[str]) -> str:
        # host+canonical path
        try:
            key = dedup_key_for_url(url)
        except Exception:
            key = url
        auth_state = self._auth_state_from_headers(headers)
        ident = headers.get("X-BH-Identity", "unknown")
        ctx = (context or "").strip().lower() if self.s.context_aware_dedup else ""
        return f"{key}:{method.upper()}:{ctx}:{auth_state}:{ident}"

    async def _request(self, method: str, url: str, *, headers: Optional[dict] = None, data: Any = None, json: Any = None, context: Optional[str] = None) -> httpx.Response:
        # Normalize URL path to reduce duplicates
        try:
            url = normalize_url(url)
        except Exception:
            pass
        # Optional soft-encoding to bypass naive filters
        try:
            if self.s.enable_encoding_bypass:
                url = soft_encode_url(url)
        except Exception:
            pass
        host = host_of(url)
        async with self._sem:
            # Prepare headers early for fingerprint
            h = self._prepare_headers(headers)
            fingerprint = None
            if method.upper() == "GET":
                # Smart dedup: reuse any prior result for same host+path (all status codes)
                if getattr(self.s, "smart_dedup_enabled", False):
                    try:
                        if self.s.context_aware_dedup:
                            fingerprint = self._build_context_fingerprint(url, method, h, context)
                            if fingerprint in self._tested_fingerprints:
                                if self.s.verbosity == "debug" or self.s.verbosity == "smart":
                                    try:
                                        log.info("[SKIP] Context-dedup %s (%s)", path_for_log(url), context or "")
                                    except Exception:
                                        pass
                                # Attempt to reuse last response by host+path if available
                                key = dedup_key_for_url(url)
                                cached_resp = self._dedup_cache.get(key)
                                if cached_resp is not None:
                                    return cached_resp
                                # Otherwise fall through to avoid breaking semantics
                        else:
                            key = dedup_key_for_url(url)
                            cached_resp = self._dedup_cache.get(key)
                            if cached_resp is not None:
                                if self.s.verbosity == "debug" or self.s.verbosity == "smart":
                                    try:
                                        msg_tag = "[SKIP]" if cached_resp.status_code >= 400 else "[CACHE]"
                                        if msg_tag == "[SKIP]":
                                            log.info("%s Already tested %s (%s)", msg_tag, path_for_log(url), cached_resp.status_code)
                                        else:
                                            log.info("%s Reusing result for %s (%s)", msg_tag, path_for_log(url), cached_resp.status_code)
                                    except Exception:
                                        pass
                                return cached_resp
                    except Exception:
                        pass
                cached = self._cache_get(url)
                if cached is not None:
                    return cached
            await self._respect_limits(host)
            last_exc: Optional[Exception] = None
            for attempt in range(self.s.retry_times + 1):
                start = time.perf_counter()
                try:
                    r = await self._client.request(method, url, headers=h, data=data, json=json)
                    elapsed_ms = (time.perf_counter() - start) * 1000.0
                    if self.s.verbosity == "debug":
                        log.debug("%s %s -> %s", method.upper(), url, r.status_code)
                    ident = h.get("X-BH-Identity", "unknown")
                    self._record(url, method.upper(), r.status_code, elapsed_ms, len(r.content), ident)
                    # WAF hinting for heavy throttling
                    if self._waf is not None:
                        try:
                            body_sample = r.text[:512] if r.headers.get("content-type","" ).lower().startswith("text/") else ""
                            self._waf.analyze_response(url, r.status_code, dict(r.headers), body_sample)
                        except Exception:
                            pass
                    if method.upper() == "GET":
                        # Populate legacy cache for 2xx/3xx and dedup cache for all
                        if r.status_code < 400:
                            self._cache_put(url, r)
                        if getattr(self.s, "smart_dedup_enabled", False):
                            try:
                                key = dedup_key_for_url(url)
                                # Only cache first-seen result for host+path
                                if key not in self._dedup_cache:
                                    self._dedup_cache[key] = r
                                # Record tested context fingerprint to suppress exact duplicates later
                                if self.s.context_aware_dedup and fingerprint is None:
                                    fingerprint = self._build_context_fingerprint(url, method, h, context)
                                if self.s.context_aware_dedup and fingerprint is not None:
                                    self._tested_fingerprints.add(fingerprint)
                            except Exception:
                                pass
                        # 429 backoff (rate limiting awareness)
                        if getattr(self.s, "smart_backoff_enabled", False) and r.status_code == 429:
                            try:
                                import random as _rnd, asyncio as _aio
                                delay = _rnd.uniform(10.0, 30.0)
                                if self.s.verbosity != "results":
                                    log.warning("[!] 429 Too Many Requests on %s – backing off for %.1fs", path_for_log(url), delay)
                                await _aio.sleep(delay)
                            except Exception:
                                pass
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

    async def get(self, url: str, headers: Optional[dict] = None, context: Optional[str] = None) -> httpx.Response:
        return await self._request("GET", url, headers=headers, context=context)

    async def post(self, url: str, data: Optional[dict | str | bytes] = None, json: Optional[dict] = None, headers: Optional[dict] = None, context: Optional[str] = None) -> httpx.Response:
        return await self._request("POST", url, headers=headers, data=data, json=json, context=context)

    async def put(self, url: str, data: Optional[dict | str | bytes] = None, json: Optional[dict] = None, headers: Optional[dict] = None, context: Optional[str] = None) -> httpx.Response:
        return await self._request("PUT", url, headers=headers, data=data, json=json, context=context)

    async def patch(self, url: str, data: Optional[dict | str | bytes] = None, json: Optional[dict] = None, headers: Optional[dict] = None, context: Optional[str] = None) -> httpx.Response:
        return await self._request("PATCH", url, headers=headers, data=data, json=json, context=context)

    async def delete(self, url: str, headers: Optional[dict] = None, context: Optional[str] = None) -> httpx.Response:
        return await self._request("DELETE", url, headers=headers, context=context)