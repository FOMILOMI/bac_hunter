from __future__ import annotations
from typing import Dict, Optional, List, Tuple, Callable
try:
    from .config import Identity
    from .utils import pick_ua
except Exception:
    from config import Identity
    from utils import pick_ua

import logging
import re
import json
import os
from urllib.parse import urlparse

log = logging.getLogger("session")


class SessionManager:
    """Lightweight identity registry for low-noise differential testing later.

    Extended to support:
    - Per-domain session persistence (cookies, bearer)
    - Response processing to capture Set-Cookie, bearer tokens, and CSRF tokens
    - Identity metadata (role/user_id/tenant_id) and pairing helpers
    - Semi-automatic login via browser driver
    """

    def __init__(self):
        self._identities: Dict[str, Identity] = {}
        self.add_identity(Identity(name="anon", base_headers={"User-Agent": pick_ua()}))
        # Domain -> session dict {cookies: list, bearer: str, csrf: str, storage: dict}
        self._domain_sessions: Dict[str, Dict[str, object]] = {}
        # Aggregate index path for convenience (optional)
        self._aggregate_path: Optional[str] = None
        self._sessions_dir: Optional[str] = None
        # Interactive login configuration
        self._browser_driver: str = "playwright"
        self._login_timeout_seconds: int = 180
        self._enable_semi_auto_login: bool = True
        # Retry and overall timeout guards to prevent infinite loops
        self._max_login_retries: int = 3
        self._overall_login_timeout_seconds: int = 240
        # Common login path hints for redirect detection
        self._login_path_re = re.compile(r"/(login|signin|sign-in|account|user/login|users/sign_in|auth|session|sso)\b", re.IGNORECASE)
        # Optional extractors for custom apps to provide tokens
        self._token_extractors: List[Callable[[object], Dict[str, str]]] = []
        # Internal clock helper
        import time as _t  # lazy to avoid global import noise
        self._now = _t.time
        # Global auth store path (auth_data.json via env in module)
        try:
            from .auth_store import DEFAULT_AUTH_PATH as _ap
            self._auth_store_path = _ap
        except Exception:
            self._auth_store_path = "auth_data.json"

    def configure(self, *, sessions_dir: str, browser_driver: Optional[str] = None, login_timeout_seconds: Optional[int] = None, enable_semi_auto_login: Optional[bool] = None, max_login_retries: Optional[int] = None, overall_login_timeout_seconds: Optional[int] = None):
        import os
        self._sessions_dir = sessions_dir
        try:
            os.makedirs(self._sessions_dir, exist_ok=True)
        except Exception:
            pass
        # Aggregate index path
        try:
            self._aggregate_path = f"{self._sessions_dir}/session.json"
        except Exception:
            self._aggregate_path = None
        if browser_driver:
            self._browser_driver = browser_driver
        if login_timeout_seconds is not None:
            self._login_timeout_seconds = int(login_timeout_seconds)
        if enable_semi_auto_login is not None:
            self._enable_semi_auto_login = bool(enable_semi_auto_login)
        if max_login_retries is not None:
            try:
                self._max_login_retries = max(0, int(max_login_retries))
            except Exception:
                pass
        if overall_login_timeout_seconds is not None:
            try:
                self._overall_login_timeout_seconds = max(1, int(overall_login_timeout_seconds))
            except Exception:
                pass
        # CI/offline guard: disable interactive login when BH_OFFLINE=1
        try:
            if (os.getenv("BH_OFFLINE", "0") == "1"):
                self._enable_semi_auto_login = False
            # Optional env overrides for retries and overall timeout
            val = os.getenv("BH_LOGIN_MAX_RETRIES")
            if val is not None:
                try:
                    self._max_login_retries = max(0, int(val))
                except Exception:
                    pass
            val = os.getenv("BH_LOGIN_OVERALL_TIMEOUT")
            if val is not None:
                try:
                    self._overall_login_timeout_seconds = max(1, int(val))
                except Exception:
                    pass
            # Allow user to skip any interactive login entirely
            if os.getenv("BH_SKIP_LOGIN", "0") == "1":
                self._enable_semi_auto_login = False
        except Exception:
            pass

    def _session_path(self, domain: str) -> Optional[str]:
        if not self._sessions_dir:
            return None
        # Sanitize domain name for safe file naming
        safe = re.sub(r'[^\w\-\.]', '_', domain.lower())
        return f"{self._sessions_dir}/{safe}.json"

    def _is_cookie_for_domain(self, cookie: dict, target_domain: str) -> bool:
        """Check if a cookie belongs to the target domain."""
        try:
            cookie_domain = cookie.get("domain", "").lower()
            if not cookie_domain:
                return True  # No domain specified, assume it's for current domain
            
            # Remove leading dot if present
            if cookie_domain.startswith('.'):
                cookie_domain = cookie_domain[1:]
            
            # Check if cookie domain matches target domain
            if cookie_domain == target_domain.lower():
                return True
            
            # Check if cookie domain is a parent domain (e.g., .example.com for sub.example.com)
            if target_domain.lower().endswith('.' + cookie_domain):
                return True
            
            return False
        except Exception:
            return False

    def _filter_cookies_by_domain(self, cookies: list, target_domain: str) -> list:
        """Filter cookies to only include those for the target domain."""
        if not cookies:
            return []
        
        filtered = []
        for cookie in cookies:
            if isinstance(cookie, dict) and self._is_cookie_for_domain(cookie, target_domain):
                filtered.append(cookie)
        
        return filtered

    def add_identity(self, ident: Identity):
        self._identities[ident.name] = ident

    def get(self, name: str) -> Optional[Identity]:
        return self._identities.get(name)

    def all(self):
        return list(self._identities.values())

    def set_identity_metadata(self, name: str, *, role: Optional[str] = None, user_id: Optional[str] = None, tenant_id: Optional[str] = None):
        ident = self._identities.get(name)
        if not ident:
            return
        if role is not None:
            ident.role = role
        if user_id is not None:
            ident.user_id = user_id
        if tenant_id is not None:
            ident.tenant_id = tenant_id

    def choose_pairs(self, strategy: str = "horizontal") -> List[Tuple[Identity, Identity]]:
        pairs: List[Tuple[Identity, Identity]] = []
        ids = [i for i in self.all() if i.name != "anon"]
        if strategy == "horizontal":
            # same role, different user_id
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    a, b = ids[i], ids[j]
                    if a.role and b.role and a.role == b.role and a.user_id and b.user_id and a.user_id != b.user_id:
                        pairs.append((a, b))
        else:
            # vertical: different roles when known
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    a, b = ids[i], ids[j]
                    if a.role and b.role and a.role != b.role:
                        pairs.append((a, b))
        return pairs

    def register_token_extractors(self, extractors: List[Callable[[object], Dict[str, str]]]):
        self._token_extractors = extractors or []

    def load_yaml(self, path: str):
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        for item in data.get("identities", []):
            name = item.get("name")
            if not name:
                continue
            base_headers = item.get("headers", {}) or {}
            cookie = item.get("cookie")
            bearer = item.get("auth_bearer") or item.get("bearer")
            role = item.get("role")
            user_id = item.get("user_id")
            tenant_id = item.get("tenant_id")
            self.add_identity(Identity(name=name, base_headers=base_headers, cookie=cookie, auth_bearer=bearer, role=role, user_id=user_id, tenant_id=tenant_id))

    # ---- Per-domain sessions (cookie/bearer) ----
    def validate_and_refresh_session(self, domain_or_url: str) -> bool:
        """Validate existing session and refresh if needed.
        
        Returns True if a valid session exists after this call.
        """
        # First check if we have any session data
        if self.has_valid_session(domain_or_url):
            try:
                print(f"✅ Session validated for {domain_or_url}")
            except Exception:
                pass
            return True
        
        # Try to load from global auth store and hydrate
        try:
            from .auth_store import read_auth, is_auth_still_valid
        except Exception:
            from auth_store import read_auth, is_auth_still_valid
        
        try:
            data = read_auth(self._auth_store_path)
            if data and is_auth_still_valid(data):
                # Hydrate per-domain cache
                dom = domain_or_url
                try:
                    if "://" in domain_or_url:
                        dom = self._hostname_from_url(domain_or_url) or ""
                except Exception:
                    pass
                if dom:
                    try:
                        cookies = data.get("cookies") or []
                        bearer = data.get("bearer") or data.get("token")
                        csrf = data.get("csrf")
                        storage = data.get("storage")
                        self.save_domain_session(dom, cookies, bearer, csrf, storage)
                        try:
                            print(f"✅ Session loaded from global store for {dom}")
                        except Exception:
                            pass
                        return True
                    except Exception:
                        pass
        except Exception:
            pass
        
        # If no valid session found, trigger login
        return self.ensure_logged_in(domain_or_url)

    def load_domain_session(self, domain: str) -> Dict[str, object]:
        """Load session data for a domain, with improved fallback logic."""
        if not domain:
            return {}
        
        # Try to load from sessions directory first using consistent file naming
        try:
            if self._sessions_dir:
                session_file = self._session_path(domain)
                if session_file and os.path.exists(session_file):
                    with open(session_file, "r", encoding="utf-8") as f:
                        data = json.load(f) or {}
                        # Ensure we have the expected structure
                        if not isinstance(data.get("cookies"), list):
                            data["cookies"] = []
                        return data
        except Exception:
            pass
        
        # Fallback to global auth store only if no domain-specific file exists
        try:
            from .auth_store import read_auth
        except Exception:
            from auth_store import read_auth
        
        try:
            data = read_auth(self._auth_store_path)
            if data:
                # Return a copy to avoid modifying the global store
                return {
                    "cookies": data.get("cookies") or [],
                    "bearer": data.get("bearer") or data.get("token"),
                    "csrf": data.get("csrf"),
                    "storage": data.get("storage")
                }
        except Exception:
            pass
        
        return {}

    def save_domain_session(self, domain: str, cookies: list, bearer: Optional[str] = None, csrf: Optional[str] = None, storage: Optional[dict] = None):
        """Save session data for a domain with improved persistence."""
        if not domain:
            return
        
        # Filter cookies to only include those for the target domain
        filtered_cookies = self._filter_cookies_by_domain(cookies or [], domain)
        
        # Update in-memory cache
        self._domain_sessions[domain] = {
            "cookies": filtered_cookies,
            "bearer": bearer,
            "csrf": csrf,
            "storage": storage
        }
        
        # Save to sessions directory using consistent file naming
        try:
            if self._sessions_dir:
                session_file = self._session_path(domain)
                if session_file:
                    os.makedirs(os.path.dirname(session_file), exist_ok=True)
                    with open(session_file, "w", encoding="utf-8") as f:
                        json.dump(self._domain_sessions[domain], f, indent=2)
        except Exception:
            pass
        
        # Update aggregate sessions/session.json (for debugging and reuse)
        try:
            if self._aggregate_path and self._sessions_dir:
                aggregate: Dict[str, object] = {}
                for fname in os.listdir(self._sessions_dir):
                    if not fname.endswith(".json"):
                        continue
                    if fname == self._aggregate_path.split("/")[-1]:
                        continue
                    dom = fname[:-5]
                    try:
                        with open(f"{self._sessions_dir}/{fname}", "r", encoding="utf-8") as sf:
                            aggregate[dom] = json.load(sf)
                    except Exception:
                        continue
                with open(self._aggregate_path, "w", encoding="utf-8") as af:
                    json.dump(aggregate, af, indent=2)
        except Exception:
            pass

    def build_domain_headers(self, domain: str, base_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        sess = self.load_domain_session(domain)
        h: Dict[str, str] = {}
        if base_headers:
            h.update(base_headers)
        # Filter out expired cookies to avoid sending stale values
        cookies_all = sess.get("cookies") or []
        cookies_valid = [c for c in cookies_all if self._cookie_is_valid(c)]
        cookie_header = self._cookie_header_from_cookies(cookies_valid)
        if cookie_header:
            h["Cookie"] = cookie_header
        if sess.get("bearer"):
            h["Authorization"] = f"Bearer {sess['bearer']}"
        # CSRF: only attach if caller already set a known header to avoid breakage; expose getter for clients
        return h

    def _cookie_header_from_cookies(self, cookies: list) -> str:
        # cookies: list of {name, value, domain, path, expires, httpOnly, secure}
        pairs = []
        for c in cookies:
            name = c.get("name")
            val = c.get("value")
            if not name or val is None:
                continue
            pairs.append(f"{name}={val}")
        return "; ".join(pairs)

    def _cookie_is_valid(self, cookie: dict) -> bool:
        """Return True if cookie is not expired.
        Supports both Playwright ('expires') and Selenium ('expiry') fields.
        Session cookies (no expiry or 0) are treated as valid.
        """
        try:
            exp = cookie.get("expires")
            if exp is None:
                exp = cookie.get("expiry")
            if exp in (None, 0, "0", ""):
                return True
            try:
                expf = float(exp)
            except Exception:
                return True
            return expf > self._now()
        except Exception:
            return True

    # ---- Modular API for auth-aware scanning ----
    def check_auth_required(self, response) -> bool:
        """Return True if response indicates authentication is required.

        Triggers on 401/403, or 302/307 redirect to common login paths. Never on 404.
        Also heuristically detects 200 OK login pages by path and content.
        """
        try:
            status = int(getattr(response, "status_code", 0) or 0)
        except Exception:
            return False
        if status in (401, 403):
            return True
        # Challenge header indicates auth even on 200
        try:
            if (response.headers.get("WWW-Authenticate") or response.headers.get("www-authenticate")):
                return True
        except Exception:
            pass
        if status in (302, 307):
            try:
                loc = (response.headers.get("Location") or response.headers.get("location") or "").strip()
            except Exception:
                loc = ""
            if not loc:
                return False
            try:
                path = urlparse(loc).path or loc
            except Exception:
                path = loc
            if self._login_path_re.search(path or "") is not None:
                return True
        # Heuristic 200 OK login pages
        if status == 200:
            req_path = ""
            try:
                req_url = getattr(getattr(response, "request", None), "url", None)
                if req_url:
                    req_path = urlparse(str(req_url)).path or ""
            except Exception:
                req_path = ""
            try:
                ct = (response.headers.get("content-type") or "").lower()
            except Exception:
                ct = ""
            body = ""
            if "html" in ct and hasattr(response, "text"):
                try:
                    body = response.text or ""
                except Exception:
                    body = ""
            # If path looks like login and body contains login indicators
            if req_path and self._login_path_re.search(req_path or "") is not None:
                if body and (re.search(r"type=\"password\"", body, flags=re.I) or re.search(r"\blogin\b|\bsign[ -]?in\b|\bauthenticate\b", body, flags=re.I)):
                    return True
            # Generic heuristic: both a password field and login keywords strongly suggest a login page
            if body:
                has_pwd = re.search(r"type=\s*[\"']password[\"']", body, flags=re.I) is not None
                has_login_kw = re.search(r"\blogin\b|\bsign[ -]?in\b|\bauthenticat(e|ion)\b|\bmfa\b|two[- ]factor", body, flags=re.I) is not None
                id_class_login = re.search(r"(id|class)=\s*[\"'][^\"']*(login|signin|auth)[^\"']*[\"']", body, flags=re.I) is not None
                if has_pwd and (has_login_kw or id_class_login):
                    return True
        # Explicitly avoid 404/broken links
        return False

    def process_response(self, url: str, response) -> None:
        """Capture Set-Cookie, bearer tokens (if present), and CSRF tokens from responses.
        This is best-effort and safe; errors are swallowed.
        """
        domain = self._hostname_from_url(url) or ""
        if not domain:
            return
        sess = self.load_domain_session(domain)
        # Capture Set-Cookie
        try:
            set_cookie = response.headers.get("set-cookie") or response.headers.get("Set-Cookie")
            if set_cookie:
                # Simple cookie parser (split on ';', handle first key=value)
                parts = [p.strip() for p in set_cookie.split(',') if p.strip()]
                # Some servers send multiple cookies separated by comma; process conservatively
                for part in parts:
                    kv = part.split(';', 1)[0]
                    if '=' in kv:
                        name, val = kv.split('=', 1)
                        if name and val:
                            # Create cookie object with domain info
                            cookie_obj = {
                                "name": name,
                                "value": val,
                                "domain": domain  # Set the domain for filtering
                            }
                            # Upsert cookie by name, filtering by domain
                            cookies = sess.get("cookies") or []
                            found = False
                            for c in cookies:
                                if c.get("name") == name and self._is_cookie_for_domain(c, domain):
                                    c["value"] = val
                                    found = True
                                    break
                            if not found and self._is_cookie_for_domain(cookie_obj, domain):
                                cookies.append(cookie_obj)
                            sess["cookies"] = cookies
        except Exception:
            pass
        # Capture bearer tokens using custom extractors and common JSON shapes
        try:
            token: Optional[str] = None
            for ex in self._token_extractors:
                try:
                    out = ex(response) or {}
                    token = out.get("bearer") or token
                except Exception:
                    continue
            if not token:
                ct = (response.headers.get("content-type") or "").lower()
                if "json" in ct and hasattr(response, "json"):
                    try:
                        data = response.json()
                        token = data.get("access_token") or data.get("token") or None
                    except Exception:
                        token = None
            if token:
                sess["bearer"] = token
        except Exception:
            pass
        # CSRF token capture from HTML
        try:
            text = response.text if hasattr(response, "text") else ""
            if text:
                m = re.search(r"<meta[^>]+name=\"csrf[^\"]*\"[^>]+content=\"([^\"]+)\"", text, flags=re.I)
                if m:
                    sess["csrf"] = m.group(1)
                else:
                    m = re.search(r"<input[^>]+type=\"hidden\"[^>]+name=\"(csrf|_csrf|csrf_token)\"[^>]+value=\"([^\"]+)\"", text, flags=re.I)
                    if m:
                        sess["csrf"] = m.group(2)
        except Exception:
            pass
        # Persist updated session
        try:
            self.save_domain_session(domain, sess.get("cookies") or [], sess.get("bearer"), sess.get("csrf"), sess.get("storage"))
        except Exception:
            pass

    def get_csrf(self, domain_or_url: str) -> Optional[str]:
        dom = domain_or_url
        try:
            if "://" in domain_or_url:
                dom = self._hostname_from_url(domain_or_url) or ""
        except Exception:
            pass
        if not dom:
            return None
        sess = self.load_domain_session(dom)
        return sess.get("csrf") if isinstance(sess.get("csrf"), str) else None

    # ---- Interactive pre-login helpers ----
    def has_valid_session(self, domain_or_url: str) -> bool:
        """Check if we have any non-expired cookie or a bearer token for the domain."""
        # Prefer global auth store if present and valid; hydrate per-domain cache lazily
        try:
            from .auth_store import read_auth, is_auth_still_valid
        except Exception:
            from auth_store import read_auth, is_auth_still_valid
        try:
            data = read_auth(self._auth_store_path)
            if data and is_auth_still_valid(data):
                # Hydrate per-domain cache so subsequent attach uses it seamlessly
                dom = domain_or_url
                try:
                    if "://" in domain_or_url:
                        dom = self._hostname_from_url(domain_or_url) or ""
                except Exception:
                    pass
                if dom:
                    try:
                        cookies = data.get("cookies") or []
                        bearer = data.get("bearer") or data.get("token")
                        csrf = data.get("csrf")
                        storage = data.get("storage")
                        self.save_domain_session(dom, cookies, bearer, csrf, storage)
                    except Exception:
                        pass
                return True
        except Exception:
            pass
        
        # Check per-domain session
        dom = domain_or_url
        try:
            if "://" in domain_or_url:
                dom = self._hostname_from_url(domain_or_url) or ""
        except Exception:
            pass
        if not dom:
            return False
        sess = self.load_domain_session(dom)
        
        # Check for any valid cookies (not just auth-specific ones)
        try:
            cookies = sess.get("cookies") or []
            if cookies:
                # Check if any cookie is valid (not expired)
                for c in cookies:
                    if self._cookie_is_valid(c):
                        # If we have any valid cookie, consider session valid
                        return True
        except Exception:
            pass
        
        # Check for bearer token
        try:
            if isinstance(sess.get("bearer"), str) and sess.get("bearer"):
                return True
        except Exception:
            pass
        
        return False

    def ensure_logged_in(self, domain_or_url: str) -> bool:
        """Ensure user has logged in for the given domain. Triggers browser if needed.
        Returns True if a valid session exists after this call.
        """
        # Short-circuit in offline/CI mode
        if not self._enable_semi_auto_login:
            return False
        
        # Check if we already have a valid session
        if self.has_valid_session(domain_or_url):
            try:
                print(f"✅ Reusing existing session for {domain_or_url}")
            except Exception:
                pass
            return True
        
        # Bounded retries with overall timeout to avoid infinite loops
        attempts = 0
        deadline = self._now() + max(self._login_timeout_seconds, self._overall_login_timeout_seconds)
        while (attempts < self._max_login_retries) and (self._now() < deadline) and not self.has_valid_session(domain_or_url):
            attempts += 1
            try:
                print(f"🔐 Attempt {attempts}/{self._max_login_retries}: Opening browser for login...")
            except Exception:
                pass
            ok = self.open_browser_login(domain_or_url)
            if self.has_valid_session(domain_or_url):
                try:
                    print(f"✅ Login successful! Session saved for {domain_or_url}")
                except Exception:
                    pass
                return True
            # Feedback after failed attempt
            if not ok:
                try:
                    remaining = max(0, int(deadline - self._now()))
                    print(f"⚠️  Login not detected yet. {remaining}s left; will retry if attempts remain...")
                except Exception:
                    pass
        
        # Final check
        if self.has_valid_session(domain_or_url):
            try:
                print(f"✅ Session validated for {domain_or_url}")
            except Exception:
                pass
            return True
        else:
            try:
                print(f"❌ Failed to establish valid session for {domain_or_url}")
            except Exception:
                pass
            return False

    def prelogin_targets(self, targets: List[str]):
        """Open a browser for each unique domain to let the user log in once per run.
        Safe no-op if sessions already exist and are valid.
        """
        # Respect offline/CI guard
        if not self._enable_semi_auto_login:
            return
        # Deduplicate by hostname
        seen: set[str] = set()
        for t in targets or []:
            try:
                dom = self._hostname_from_url(t) or t
            except Exception:
                dom = t
            if not dom or dom in seen:
                continue
            seen.add(dom)
            try:
                # Only open browser when session missing/expired
                if not self.has_valid_session(dom):
                    try:
                        print(f"🔐 [{dom}] Login required. Starting browser...")
                    except Exception:
                        pass
                    attempts = 0
                    deadline = self._now() + max(self._login_timeout_seconds, self._overall_login_timeout_seconds)
                    while (attempts < self._max_login_retries) and (self._now() < deadline) and not self.has_valid_session(dom):
                        attempts += 1
                        try:
                            print(f"[{dom}] Login attempt {attempts}/{self._max_login_retries}...")
                        except Exception:
                            pass
                        ok = self.open_browser_login(dom)
                        if self.has_valid_session(dom):
                            try:
                                print(f"✅ [{dom}] Login successful! Session saved.")
                            except Exception:
                                pass
                            break
                        if not ok:
                            try:
                                remaining = max(0, int(deadline - self._now()))
                                print(f"⚠️  [{dom}] Still waiting for login... {remaining}s remaining")
                            except Exception:
                                pass
                        if not self._enable_semi_auto_login:
                            break
                else:
                    try:
                        print(f"✅ [{dom}] Reusing existing session")
                    except Exception:
                        pass
            except Exception:
                continue

    def open_browser_login(self, domain_or_url: str) -> bool:
        """Open an interactive browser for manual login and persist the session.

        Returns True if any cookies, bearer token, or CSRF token were captured.
        """
        if not self._enable_semi_auto_login:
            return False
        try:
            # Log exact message requested
            try:
                print("🔐 Authentication required → Opening browser for manual login...")
            except Exception:
                pass
            target = domain_or_url
            # If only a bare domain is provided, try https scheme
            try:
                parsed = urlparse(domain_or_url)
                if not parsed.scheme:
                    target = f"https://{domain_or_url}"
            except Exception:
                target = domain_or_url
            try:
                from .integrations.browser_automation import InteractiveLogin  # type: ignore
            except Exception:
                from integrations.browser_automation import InteractiveLogin  # type: ignore
        except Exception:
            return False
        try:
            drv = InteractiveLogin(driver=self._browser_driver)

            import asyncio
            # Run async method in sync context with proper loop handling
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context. Offload to a separate thread to run its own loop.
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, drv.open_and_wait(target, self._login_timeout_seconds))
                    cookies, bearer, csrf, storage = future.result()
            except RuntimeError:
                # No running loop, safe to use asyncio.run directly
                cookies, bearer, csrf, storage = asyncio.run(drv.open_and_wait(target, self._login_timeout_seconds))

            # Persist if anything was captured
            if cookies or bearer or csrf:
                domain = self._hostname_from_url(target)
                if domain:
                    # Filter cookies to only include those for the target domain
                    filtered_cookies = self._filter_cookies_by_domain(cookies or [], domain)
                    self.save_domain_session(domain, filtered_cookies, bearer, csrf, storage)
                    try:
                        print(f"💾 Session data saved for {domain}")
                    except Exception:
                        pass
                # Also persist to global auth_data.json so next runs can skip browser
                try:
                    from .auth_store import write_auth
                except Exception:
                    from auth_store import write_auth
                try:
                    # Build a headers snapshot with filtered cookies
                    filtered_cookies = self._filter_cookies_by_domain(cookies or [], domain or "")
                    cookie_header = self._cookie_header_from_cookies(filtered_cookies)
                    hdrs = {}
                    if cookie_header:
                        hdrs["Cookie"] = cookie_header
                    if bearer:
                        hdrs["Authorization"] = f"Bearer {bearer}"
                    data = {
                        "cookies": filtered_cookies,
                        "bearer": bearer,
                        "csrf": csrf,
                        "headers": hdrs,
                        "storage": storage or None,
                        "captured_at": self._now(),
                        # optional token exp could be set by custom extractors in the future
                    }
                    write_auth(data, self._auth_store_path)
                    try:
                        print(f"💾 Global session data saved to {self._auth_store_path}")
                    except Exception:
                        pass
                except Exception as e:
                    try:
                        print(f"⚠️  Failed to save global session: {e}")
                    except Exception:
                        pass
                return True
            else:
                try:
                    print("⚠️  No session data captured from browser")
                except Exception:
                    pass
        except Exception as e:
            try:
                print(f"❌ Browser login failed: {e}")
            except Exception:
                pass
        return False

    def load_session(self, domain: str) -> Dict[str, object]:
        return self.load_domain_session(domain)

    def attach_session(self, url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Attach saved session (cookies/bearer) for the URL's domain to headers."""
        headers = headers or {}
        domain = self._hostname_from_url(url)
        if not domain:
            return headers
        return self.build_domain_headers(domain, headers)

    def refresh_session(self, domain_or_url: str) -> bool:
        """Re-trigger interactive login to refresh an expired session."""
        return self.open_browser_login(domain_or_url)

    def clear_expired_sessions(self) -> None:
        """Clear expired sessions from both memory and disk."""
        try:
            # Clear expired sessions from memory
            expired_domains = []
            for domain, session in self._domain_sessions.items():
                if not self.has_valid_session(domain):
                    expired_domains.append(domain)
            
            for domain in expired_domains:
                del self._domain_sessions[domain]
                try:
                    print(f"🗑️  Cleared expired session for {domain}")
                except Exception:
                    pass
            
            # Clear expired sessions from disk
            if self._sessions_dir:
                for fname in os.listdir(self._sessions_dir):
                    if not fname.endswith(".json"):
                        continue
                    domain = fname[:-5]  # Remove .json extension
                    session_file = f"{self._sessions_dir}/{fname}"
                    try:
                        with open(session_file, "r", encoding="utf-8") as f:
                            data = json.load(f) or {}
                        # Check if session is expired
                        cookies = data.get("cookies") or []
                        bearer = data.get("bearer")
                        if not cookies and not bearer:
                            # No session data, remove file
                            os.remove(session_file)
                            try:
                                print(f"🗑️  Removed empty session file for {domain}")
                            except Exception:
                                pass
                        else:
                            # Check if cookies are expired
                            valid_cookies = [c for c in cookies if self._cookie_is_valid(c)]
                            if not valid_cookies and not bearer:
                                os.remove(session_file)
                                try:
                                    print(f"🗑️  Removed expired session file for {domain}")
                                except Exception:
                                    pass
                    except Exception:
                        pass
        except Exception:
            pass

    def get_session_info(self, domain_or_url: str) -> Dict[str, object]:
        """Get detailed session information for debugging."""
        dom = domain_or_url
        try:
            if "://" in domain_or_url:
                dom = self._hostname_from_url(domain_or_url) or ""
        except Exception:
            pass
        
        if not dom:
            return {}
        
        session = self.load_domain_session(dom)
        info = {
            "domain": dom,
            "has_session": bool(session),
            "cookie_count": len(session.get("cookies") or []),
            "has_bearer": bool(session.get("bearer")),
            "has_csrf": bool(session.get("csrf")),
            "is_valid": self.has_valid_session(domain_or_url)
        }
        
        # Add cookie details
        cookies = session.get("cookies") or []
        valid_cookies = [c for c in cookies if self._cookie_is_valid(c)]
        info["valid_cookies"] = len(valid_cookies)
        info["expired_cookies"] = len(cookies) - len(valid_cookies)
        
        return info

    def _hostname_from_url(self, url: str) -> Optional[str]:
        try:
            return urlparse(url).netloc.split("@").pop().split(":")[0]
        except Exception:
            return None
    