from __future__ import annotations
import logging
from typing import Dict, List, Tuple

from ..config import Settings, Identity
from ..http_client import HttpClient
from ..storage import Storage

log = logging.getLogger("audit.headers")

SEC_HEADERS = [
    "content-security-policy",
    "x-content-type-options",
    "x-frame-options",
    "referrer-policy",
    "strict-transport-security",
]

class HeaderInspector:
    """Reads response headers for known misconfigs. Low-noise: single GET per URL.
    Emits findings:
      - cors_misconfig
      - weak_headers
      - cache_sensitive
    """

    def __init__(self, settings: Settings, http: HttpClient, db: Storage):
        self.s = settings
        self.http = http
        self.db = db

    def _lower(self, h: Dict[str, str]) -> Dict[str, str]:
        return {k.lower(): v for k, v in h.items()}

    def _is_sensitive_path(self, url: str) -> bool:
        u = url.lower()
        return any(k in u for k in ["/admin", "/account", "/user", "/api/", "/internal", "/settings", "/billing"]) or u.endswith(('.json', '.csv'))

    def _check_cors(self, url: str, h: Dict[str, str]) -> List[Tuple[str,float]]:
        issues: List[Tuple[str,float]] = []
        acao = h.get("access-control-allow-origin")
        acac = (h.get("access-control-allow-credentials") or "").lower()
        if acao:
            if acao == "*" and acac == "true":
                issues.append((f"CORS: ACAO=* with credentials=true on {url}", 0.85))
            # Reflection pattern (very rough, header contains scheme://)
            if "://" in acao and "null" not in acao.lower():
                issues.append((f"CORS: Potentially reflected/overly‑broad ACAO={acao}", 0.6))
        return issues

    def _check_headers(self, url: str, h: Dict[str, str]) -> List[Tuple[str,float]]:
        issues: List[Tuple[str,float]] = []
        # Security headers
        if "x-content-type-options" not in h or h.get("x-content-type-options", "").lower() != "nosniff":
            issues.append(("Missing/weak X-Content-Type-Options (nosniff)", 0.35))
        xf = h.get("x-frame-options", "").lower()
        csp = h.get("content-security-policy", "")
        if not xf and not csp:
            issues.append(("Missing X-Frame-Options/CSP (clickjacking risk)", 0.35))
        if self._is_sensitive_path(url):
            cc = (h.get("cache-control") or "").lower()
            if not any(t in cc for t in ["no-store", "private", "no-cache"]):
                issues.append(("Sensitive path without no-store/private cache-control", 0.45))
        # HSTS for https
        if url.lower().startswith("https://"):
            if "strict-transport-security" not in h:
                issues.append(("Missing HSTS on HTTPS origin", 0.3))
        return issues

    async def _active_cors_probe(self, url: str, ident: Identity):
        if not self.s.enable_cors_probe:
            return
        origin = self.s.cors_probe_origin
        try:
            r = await self.http.get(url, headers={**ident.headers(), "Origin": origin})
        except Exception:
            return
        hd = self._lower(dict(r.headers))
        acao = hd.get("access-control-allow-origin")
        acac = (hd.get("access-control-allow-credentials") or "").lower()
        if acao and (acao == origin or acao == "*"):
            sev = 0.9 if acac == "true" else 0.6
            self.db.add_finding_for_url(url, type_="cors_misconfig", evidence=f"Active CORS: ACAO={acao} ACAC={acac}", score=sev)

    async def run(self, urls: List[str], ident: Identity):
        for u in urls:
            try:
                r = await self.http.get(u, headers=ident.headers())
            except Exception:
                continue
            hd = self._lower(dict(r.headers))
            for msg, score in self._check_cors(u, hd) + self._check_headers(u, hd):
                self.db.add_finding_for_url(u, type_="weak_headers" if "CORS" not in msg else "cors_misconfig", evidence=msg, score=score)
            # optional active probe
            await self._active_cors_probe(u, ident)