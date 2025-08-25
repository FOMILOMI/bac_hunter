from __future__ import annotations
import asyncio
from typing import List
from urllib.parse import urlparse, urlunparse, urlencode

from ..config import Settings, Identity
from ..core.http_client import HttpClient
from ..core.storage import Storage


class ParamScanner:
    """Fallback parameter scanner that tries safe, low-noise GET toggles."""

    COMMON_PARAMS = [
        {"admin": "1"},
        {"debug": "1"},
        {"role": "admin"},
        {"preview": "true"},
        {"private": "true"},
    ]

    def __init__(self, settings: Settings, http: HttpClient, db: Storage):
        self.s = settings
        self.http = http
        self.db = db

    async def run(self, base_url: str, identity: Identity) -> List[str]:
        urls = []
        tid = self.db.ensure_target(base_url)
        candidates = list(dict.fromkeys(self.db.iter_target_urls(tid)))[:30]
        candidates.insert(0, base_url.rstrip('/'))
        out: List[str] = []

        async def probe(u: str, param: dict):
            p = urlparse(u)
            q = urlencode(param, doseq=True)
            target = urlunparse((p.scheme, p.netloc, p.path, p.params, q, p.fragment))
            h = identity.headers()
            h["X-BH-Identity"] = identity.name
            try:
                resp = await self.http.get(target, headers=h)
                if resp.status_code in (200, 206, 401, 403) and len(resp.content) > 256:
                    self.db.add_finding_for_url(target, "param_toggle", f"status={resp.status_code}; len={len(resp.content)}", 0.2)
                    out.append(target)
            except Exception:
                pass

        tasks = []
        for u in candidates:
            for p in self.COMMON_PARAMS:
                tasks.append(probe(u, p))
        await asyncio.gather(*tasks[:100])
        return out

