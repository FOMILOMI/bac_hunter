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
        # Domain -> session dict {cookies: list, bearer: str, csrf: str}
        self._domain_sessions: Dict[str, Dict[str, object]] = {}
        self._sessions_dir: Optional[str] = None
        # Interactive login configuration
        self._browser_driver: str = "playwright"
        self._login_timeout_seconds: int = 180
        self._enable_semi_auto_login: bool = True
        # Common login path hints for redirect detection
        self._login_path_re = re.compile(r"/(login|signin|sign-in|account|user/login|users/sign_in|auth|session|sso)\b", re.IGNORECASE)
        # Optional extractors for custom apps to provide tokens
        self._token_extractors: List[Callable[[object], Dict[str, str]]] = []
        # Internal clock helper
        import time as _t  # lazy to avoid global import noise
        self._now = _t.time

    def configure(self, *, sessions_dir: str, browser_driver: Optional[str] = None, login_timeout_seconds: Optional[int] = None, enable_semi_auto_login: Optional[bool] = None):
        import os
        self._sessions_dir = sessions_dir
        try:
            os.makedirs(self._sessions_dir, exist_ok=True)
        except Exception:
            pass
        if browser_driver:
            self._browser_driver = browser_driver
        if login_timeout_seconds is not None:
            self._login_timeout_seconds = int(login_timeout_seconds)
        if enable_semi_auto_login is not None:
            self._enable_semi_auto_login = bool(enable_semi_auto_login)

    def _session_path(self, domain: str) -> Optional[str]:
        if not self._sessions_dir:
            return None
        safe = domain.replace(":", "_")
        return f"{self._sessions_dir}/{safe}.json"

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
    def load_domain_session(self, domain: str) -> Dict[str, object]:
        import json, os
        if domain in self._domain_sessions:
            return self._domain_sessions[domain]
        path = self._session_path(domain)
        if not path or not os.path.exists(path):
            self._domain_sessions[domain] = {"cookies": [], "bearer": None, "csrf": None}
            return self._domain_sessions[domain]
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f) or {}
            cookies = data.get("cookies") or []
            bearer = data.get("bearer")
            csrf = data.get("csrf")
            self._domain_sessions[domain] = {"cookies": cookies, "bearer": bearer, "csrf": csrf}
        except Exception:
            self._domain_sessions[domain] = {"cookies": [], "bearer": None, "csrf": None}
        return self._domain_sessions[domain]

    def save_domain_session(self, domain: str, cookies: list, bearer: Optional[str] = None, csrf: Optional[str] = None):
        import json
        self._domain_sessions[domain] = {"cookies": cookies or [], "bearer": bearer, "csrf": csrf}
        path = self._session_path(domain)
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._domain_sessions[domain], f, indent=2)
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
                            # Upsert cookie by name
                            cookies = sess.get("cookies") or []
                            found = False
                            for c in cookies:
                                if c.get("name") == name:
                                    c["value"] = val
                                    found = True
                                    break
                            if not found:
                                cookies.append({"name": name, "value": val})
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
            self.save_domain_session(domain, sess.get("cookies") or [], sess.get("bearer"), sess.get("csrf"))
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
        dom = domain_or_url
        try:
            if "://" in domain_or_url:
                dom = self._hostname_from_url(domain_or_url) or ""
        except Exception:
            pass
        if not dom:
            return False
        sess = self.load_domain_session(dom)
        try:
            cookies = sess.get("cookies") or []
            for c in cookies:
                if self._cookie_is_valid(c):
                    return True
        except Exception:
            pass
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
        if not self._enable_semi_auto_login:
            return False
        if self.has_valid_session(domain_or_url):
            return True
        ok = self.open_browser_login(domain_or_url)
        if not ok:
            return False
        return self.has_valid_session(domain_or_url)

    def prelogin_targets(self, targets: List[str]):
        """Open a browser for each unique domain to let the user log in once per run.
        Safe no-op if sessions already exist and are valid.
        """
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
                    self.open_browser_login(dom)
                else:
                    try:
                        print(f"Reusing existing session for {dom}")
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
                print("Authentication required → Opening browser for manual login...")
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
            from .integrations.browser_automation import InteractiveLogin  # type: ignore
        except Exception:
            try:
                from integrations.browser_automation import InteractiveLogin  # type: ignore
            except Exception:
                return False
        try:
            drv = InteractiveLogin(driver=self._browser_driver)
            cookies, bearer, csrf = drv.open_and_wait(target, timeout_seconds=self._login_timeout_seconds)
            # Persist if anything was captured
            if cookies or bearer or csrf:
                domain = self._hostname_from_url(target)
                if domain:
                    self.save_domain_session(domain, cookies, bearer, csrf)
                    try:
                        print(f"Session saved for {domain}")
                    except Exception:
                        pass
                return True
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

    def _hostname_from_url(self, url: str) -> Optional[str]:
        try:
            return urlparse(url).netloc.split("@").pop().split(":")[0]
        except Exception:
            return None
    