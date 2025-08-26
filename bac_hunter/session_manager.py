from __future__ import annotations
from typing import Dict, Optional
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
    """Lightweight identity registry for low-noise differential testing later."""

    def __init__(self):
        self._identities: Dict[str, Identity] = {}
        self.add_identity(Identity(name="anon", base_headers={"User-Agent": pick_ua()}))
        # Domain -> session dict {cookies: list, bearer: str}
        self._domain_sessions: Dict[str, Dict[str, object]] = {}
        self._sessions_dir: Optional[str] = None
        # Interactive login configuration
        self._browser_driver: str = "playwright"
        self._login_timeout_seconds: int = 180
        self._enable_semi_auto_login: bool = True
        # Common login path hints for redirect detection
        self._login_path_re = re.compile(r"/(login|signin|sign-in|account|user/login|users/sign_in|auth|session|sso)\b", re.IGNORECASE)

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
            self.add_identity(Identity(name=name, base_headers=base_headers, cookie=cookie, auth_bearer=bearer))

    # ---- Per-domain sessions (cookie/bearer) ----
    def load_domain_session(self, domain: str) -> Dict[str, object]:
        import json, os
        if domain in self._domain_sessions:
            return self._domain_sessions[domain]
        path = self._session_path(domain)
        if not path or not os.path.exists(path):
            self._domain_sessions[domain] = {"cookies": [], "bearer": None}
            return self._domain_sessions[domain]
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f) or {}
            cookies = data.get("cookies") or []
            bearer = data.get("bearer")
            self._domain_sessions[domain] = {"cookies": cookies, "bearer": bearer}
        except Exception:
            self._domain_sessions[domain] = {"cookies": [], "bearer": None}
        return self._domain_sessions[domain]

    def save_domain_session(self, domain: str, cookies: list, bearer: Optional[str] = None):
        import json
        self._domain_sessions[domain] = {"cookies": cookies or [], "bearer": bearer}
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
        cookie_header = self._cookie_header_from_cookies(sess.get("cookies") or [])
        if cookie_header:
            h["Cookie"] = cookie_header
        if sess.get("bearer"):
            h["Authorization"] = f"Bearer {sess['bearer']}"
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

    # ---- Modular API for auth-aware scanning ----
    def check_auth_required(self, response) -> bool:
        """Return True if response indicates authentication is required.

        Triggers on 401/403, or 302/307 redirect to common login paths. Never on 404.
        """
        try:
            status = int(getattr(response, "status_code", 0) or 0)
        except Exception:
            return False
        if status in (401, 403):
            return True
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
        # Explicitly avoid 404/broken links
        return False

    def open_browser_login(self, domain_or_url: str) -> bool:
        """Open an interactive browser for manual login and persist the session.

        Returns True if any cookies or bearer token were captured.
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
            cookies, bearer = drv.open_and_wait(target, timeout_seconds=self._login_timeout_seconds)
            # Persist if anything was captured
            if cookies or bearer:
                domain = self._hostname_from_url(target)
                if domain:
                    self.save_domain_session(domain, cookies, bearer)
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
    