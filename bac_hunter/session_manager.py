from __future__ import annotations
from typing import Dict, Optional
try:
    from .config import Identity
    from .utils import pick_ua
except Exception:
    from config import Identity
    from utils import pick_ua


class SessionManager:
    """Lightweight identity registry for low-noise differential testing later."""

    def __init__(self):
        self._identities: Dict[str, Identity] = {}
        self.add_identity(Identity(name="anon", base_headers={"User-Agent": pick_ua()}))
        # Domain -> session dict {cookies: list, bearer: str}
        self._domain_sessions: Dict[str, Dict[str, object]] = {}
        self._sessions_dir: Optional[str] = None

    def configure(self, *, sessions_dir: str):
        import os
        self._sessions_dir = sessions_dir
        try:
            os.makedirs(self._sessions_dir, exist_ok=True)
        except Exception:
            pass

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
    