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
    from .access.oracle import AccessOracle
except Exception:  # fallback when imported as top-level module
    from config import Settings
    from rate_limiter import RateLimiter, AdaptiveRateLimiter
    from utils import host_of, jitter, pick_ua, normalize_url, dedup_key_for_url, path_for_log
    from monitoring.stats_collector import StatsCollector
    from safety.throttle_calibrator import ThrottleCalibrator
    from safety.waf_detector import WAFDetector
    from safety.evasion import randomize_header_casing, soft_encode_url
    from access.oracle import AccessOracle

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
        # Store per-identity to avoid cross-identity reuse
        self._dedup_cache: Dict[str, Dict[str, httpx.Response]] = {}
        # context-aware tested combinations to suppress redundant requests
        # Track per-identity fingerprints to avoid skipping legitimate tests
        self._tested_fingerprints: set[str] = set()
        # session manager will be provided by orchestrator
        self._session_mgr = None
        # Access oracle for FP control
        self._oracle = AccessOracle() if getattr(self.s, 'enable_denial_fingerprinting', True) else None
        # Track which domains we've hydrated from global auth store
        self._auth_store_hydrated: set[str] = set()

    def attach_session_manager(self, session_manager):
        """Attach session manager after construction to avoid circular imports."""
        self._session_mgr = session_manager
        try:
            # Ensure sessions directory exists and pass browser settings
            self._session_mgr.configure(
                sessions_dir=self.s.sessions_dir,
                browser_driver=self.s.browser_driver,
                login_timeout_seconds=self.s.login_timeout_seconds,
                enable_semi_auto_login=self.s.enable_semi_auto_login,
            )
        except Exception:
            pass

    def _ensure_session_manager(self):
        if self._session_mgr is None:
            try:
                from .session_manager import SessionManager  # lazy import to avoid cycles
            except Exception:
                from session_manager import SessionManager
            try:
                self._session_mgr = SessionManager()
                self._session_mgr.configure(
                    sessions_dir=self.s.sessions_dir,
                    browser_driver=self.s.browser_driver,
                    login_timeout_seconds=self.s.login_timeout_seconds,
                    enable_semi_auto_login=self.s.enable_semi_auto_login,
                )
            except Exception:
                self._session_mgr = None

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

    def _inject_domain_session(self, url: str, headers: Dict[str, str]) -> Dict[str, str]:
        if not self._session_mgr:
            self._ensure_session_manager()
        if not self._session_mgr:
            return headers
        try:
            # ALWAYS check global auth store for latest auth data
            host = host_of(url)
            if host:
                try:
                    from .auth_store import read_auth, is_auth_still_valid, has_auth_data
                except Exception:
                    from auth_store import read_auth, is_auth_still_valid, has_auth_data
                try:
                    data = read_auth()
                    if data and has_auth_data(data) and is_auth_still_valid(data):
                        # Filter cookies to this host only to prevent cross-site bleed
                        try:
                            from .session_manager import SessionManager  # type: ignore
                        except Exception:
                            from session_manager import SessionManager  # type: ignore
                        _tmp_sm = SessionManager()
                        cookies = _tmp_sm._filter_cookies_for_domain(host, data.get("cookies") or [])
                        bearer = data.get("bearer") or data.get("token")
                        csrf = data.get("csrf")
                        storage = data.get("storage")
                        try:
                            # Always update domain session with latest global data
                            self._session_mgr.save_domain_session(host, cookies, bearer, csrf, storage)
                        except Exception:
                            pass
                except Exception:
                    pass
                try:
                    self._auth_store_hydrated.add(host)
                except Exception:
                    pass
            # Attach per-domain cookies/bearer to the request headers
            return self._session_mgr.attach_session(url, headers)
        except Exception:
            return headers

    async def _maybe_prompt_for_login(self, url: str) -> bool:
        if not self.s.enable_semi_auto_login:
            return False
        if not self._session_mgr:
            self._ensure_session_manager()
        if not self._session_mgr:
            return False
        try:
            # Check if we already have valid auth data before prompting
            try:
                from .auth_store import read_auth, is_auth_still_valid, has_auth_data, probe_auth_valid
            except Exception:
                from auth_store import read_auth, is_auth_still_valid, has_auth_data, probe_auth_valid
            
            data = read_auth()
            if data and has_auth_data(data):
                if is_auth_still_valid(data):
                    # Double-check with probe to ensure auth is really invalid
                    ok, probe_status = await probe_auth_valid(self, url, data, retry_on_failure=True)
                    if ok:
                        try:
                            host = host_of(url)
                            cookies = data.get("cookies") or []
                            bearer = data.get("bearer") or data.get("token")
                            csrf = data.get("csrf")
                            storage = data.get("storage")
                            self._session_mgr.save_domain_session(host, cookies, bearer, csrf, storage)
                            self._auth_store_hydrated.add(host)
                            if self.s.verbosity != "results":
                                log.info("✅ Auth probe succeeded (%s), reusing existing session for %s", probe_status, url)
                        except Exception:
                            pass
                        return True
                    else:
                        try:
                            if self.s.verbosity != "results":
                                log.info("❌ Auth probe failed (%s), proceeding with fresh login for %s", probe_status, url)
                        except Exception:
                            pass
                else:
                    try:
                        if self.s.verbosity != "results":
                            log.info("⏰ Stored auth data appears expired, proceeding with fresh login for %s", url)
                    except Exception:
                        pass
            else:
                try:
                    if self.s.verbosity != "results":
                        log.info("🔐 No stored auth data found, proceeding with fresh login for %s", url)
                except Exception:
                    pass
            
            # Only proceed with interactive login if validation confirms it's needed
            return bool(self._session_mgr.ensure_logged_in(url))
        except Exception:
            return False

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
        # Include identity and method to prevent cross-identity/method skipping
        return f"{key}:{method.upper()}:{ctx}:{auth_state}:{ident}"

    async def _silent_refresh(self, url: str) -> bool:
        """Attempt a silent session refresh using SessionManager hook.
        Falls back to interactive login if enabled.
        """
        if not self._session_mgr:
            self._ensure_session_manager()
        if not self._session_mgr:
            return False
        try:
            # For now reuse interactive path; future: POST to /refresh when configured
            return bool(self._session_mgr.refresh_session(url))
        except Exception:
            return False

    async def _maybe_confirm_stable(self, method: str, url: str, headers: Dict[str, str], data: Any, json_body: Any, context: Optional[str]) -> Optional[httpx.Response]:
        """Optional median-of-3 sampling for unstable endpoints to reduce noise."""
        if not self._oracle:
            return None
        if method.upper() != "GET":
            return None
        # perform two additional quick samples if oracle flagged flips previously
        if not self._oracle.is_unstable(url):
            return None
        try:
            r1 = await self._client.request(method, url, headers=headers, data=data, json=json_body)
            r2 = await self._client.request(method, url, headers=headers, data=data, json=json_body)
            # No fancy median here; pick the response that matches the majority classification
            cl0 = "unknown"
            # Note: caller will observe original response separately
            c1 = self._oracle.classify(url, r1)
            c2 = self._oracle.classify(url, r2)
            if c1 == c2:
                return r1
        except Exception:
            return None
        return None

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
            # Inject domain session cookies/tokens if available
            h = self._inject_domain_session(url, h)
            fingerprint = None
            ident = h.get("X-BH-Identity", "unknown")
            if method.upper() == "GET":
                # Smart dedup: reuse only for same identity+context and same host+path
                if getattr(self.s, "smart_dedup_enabled", False):
                    try:
                        if self.s.context_aware_dedup:
                            fingerprint = self._build_context_fingerprint(url, method, h, context)
                            if fingerprint in self._tested_fingerprints:
                                if self.s.verbosity == "debug" or self.s.verbosity == "smart":
                                    try:
                                        log.info("[SKIP] Context-dedup %s (%s | id=%s)", path_for_log(url), context or "", ident)
                                    except Exception:
                                        pass
                                # Attempt to reuse last response for this identity by host+path if available
                                key = dedup_key_for_url(url)
                                cache_for_key = self._dedup_cache.get(key) or {}
                                cached_resp = cache_for_key.get(ident)
                                if cached_resp is not None:
                                    return cached_resp
                                # Otherwise fall through to avoid breaking semantics
                        else:
                            key = dedup_key_for_url(url)
                            cache_for_key = self._dedup_cache.get(key) or {}
                            cached_resp = cache_for_key.get(ident)
                            if cached_resp is not None:
                                if self.s.verbosity == "debug" or self.s.verbosity == "smart":
                                    try:
                                        msg_tag = "[SKIP]" if cached_resp.status_code >= 400 else "[CACHE]"
                                        if msg_tag == "[SKIP]":
                                            log.info("%s Already tested %s (%s | id=%s)", msg_tag, path_for_log(url), cached_resp.status_code, ident)
                                        else:
                                            log.info("%s Reusing result for %s (%s | id=%s)", msg_tag, path_for_log(url), cached_resp.status_code, ident)
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
                    # Feed oracle and session manager with observations
                    try:
                        if self._oracle:
                            self._oracle.observe_response(url, r)
                    except Exception:
                        pass
                    try:
                        if self._session_mgr and hasattr(self._session_mgr, 'process_response'):
                            self._session_mgr.process_response(url, r)
                    except Exception:
                        pass
                    # Smart auth error handling: distinguish between actual auth failure and WAF/permission issues
                    try:
                        requires_auth = False
                        if self._session_mgr and hasattr(self._session_mgr, "check_auth_required"):
                            requires_auth = bool(self._session_mgr.check_auth_required(r))
                        else:
                            requires_auth = r.status_code in (401, 403)
                    except Exception:
                        requires_auth = r.status_code in (401, 403)
                    
                    if requires_auth and attempt == 0:
                        # Before attempting login, validate if stored auth data is actually invalid
                        should_attempt_refresh = False
                        try:
                            from .auth_store import read_auth, is_auth_still_valid, has_auth_data, probe_auth_valid
                        except Exception:
                            from auth_store import read_auth, is_auth_still_valid, has_auth_data, probe_auth_valid
                        
                        try:
                            data = read_auth()
                            if data and has_auth_data(data):
                                if is_auth_still_valid(data):
                                    # Auth data appears valid, probe to confirm it's actually invalid
                                    is_valid, probe_status = await probe_auth_valid(self, url, data, retry_on_failure=True)
                                    if not is_valid:
                                        # Confirmed: auth data is invalid, attempt refresh
                                        should_attempt_refresh = True
                                        try:
                                            if self.s.verbosity != "results":
                                                log.info("🔄 Auth probe confirmed invalid session (%s), attempting refresh for %s", probe_status, url)
                                        except Exception:
                                            pass
                                    else:
                                        # Auth data is valid, this is likely a WAF/permission issue, not auth failure
                                        try:
                                            if self.s.verbosity != "results":
                                                log.info("⚠️ Got %s but auth probe succeeded (%s) - likely WAF/permission issue, continuing with same session for %s", r.status_code, probe_status, url)
                                        except Exception:
                                            pass
                                else:
                                    # Auth data appears expired, attempt refresh
                                    should_attempt_refresh = True
                                    try:
                                        if self.s.verbosity != "results":
                                            log.info("🔄 Auth data appears expired, attempting refresh for %s", url)
                                    except Exception:
                                        pass
                            else:
                                # No auth data available, attempt fresh login
                                should_attempt_refresh = True
                                try:
                                    if self.s.verbosity != "results":
                                        log.info("🔄 No auth data available, attempting fresh login for %s", url)
                                except Exception:
                                    pass
                        except Exception:
                            # On error, fall back to attempting refresh
                            should_attempt_refresh = True
                        
                        if should_attempt_refresh:
                            did_refresh = await self._silent_refresh(url)
                            if not did_refresh and self.s.enable_semi_auto_login:
                                did_refresh = await self._maybe_prompt_for_login(url)
                            if did_refresh:
                                # Inject updated session and retry immediately
                                h = self._inject_domain_session(url, h)
                                r = await self._client.request(method, url, headers=h, data=data, json=json)
                                elapsed_ms = (time.perf_counter() - start) * 1000.0
                                self._record(url, method.upper(), r.status_code, elapsed_ms, len(r.content), ident)
                                try:
                                    if self._oracle:
                                        self._oracle.observe_response(url, r)
                                except Exception:
                                    pass
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
                                # Ensure per-identity cache bucket exists
                                if key not in self._dedup_cache:
                                    self._dedup_cache[key] = {}
                                # Only cache first-seen result for identity at host+path
                                if ident not in self._dedup_cache[key]:
                                    self._dedup_cache[key][ident] = r
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
                        # Optional stability confirmation for flappy endpoints
                        try:
                            if self._oracle and self._oracle.is_unstable(url):
                                alt = await self._maybe_confirm_stable(method, url, h, data, json, context)
                                if alt is not None:
                                    r = alt
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