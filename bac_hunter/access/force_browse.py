from __future__ import annotations
import logging
from typing import Iterable

try:
	from ..config import Identity, Settings
	from ..http_client import HttpClient
	from ..storage import Storage
	from ..utils import normalize_url, is_recursive_duplicate_path
except ImportError:
	from config import Identity, Settings
	from http_client import HttpClient
	from storage import Storage
	from utils import normalize_url, is_recursive_duplicate_path

log = logging.getLogger("access.fb")

SUSPECT_CODES = {200, 206, 302, 401, 403}

class ForceBrowser:
    def __init__(self, settings: Settings, http: HttpClient, db: Storage):
        self.s = settings
        self.http = http
        self.db = db

    async def try_paths(self, paths: Iterable[str], unauth: Identity, auth: Identity):
        seen = set()
        for u in paths:
            un = normalize_url(u)
            if is_recursive_duplicate_path(un.split('://',1)[-1].split('/',1)[-1] if '://' in un else un):
                if getattr(self.s, 'smart_dedup_enabled', False):
                    log.info("[!] Skipping duplicate endpoint: %s", un)
                continue
            if un in seen:
                if getattr(self.s, 'smart_dedup_enabled', False):
                    log.info("[!] Skipping duplicate endpoint: %s", un)
                continue
            seen.add(un)
            r0 = await self.http.get(un, headers=unauth.headers())
            self.db.save_probe(url=un, identity=unauth.name, status=r0.status_code, length=len(r0.content), content_type=r0.headers.get("content-type"), body=b"")
            if getattr(self.s, 'smart_backoff_enabled', False) and r0.status_code == 429:
                log.warning("[!] Rate limited (429) on %s, backing off", un)
                import asyncio as _aio
                await _aio.sleep(2.0)
            r1 = await self.http.get(un, headers=auth.headers())
            self.db.save_probe(url=un, identity=auth.name, status=r1.status_code, length=len(r1.content), content_type=r1.headers.get("content-type"), body=b"")
            if getattr(self.s, 'smart_backoff_enabled', False) and r1.status_code == 429:
                log.warning("[!] Rate limited (429) on %s (auth), backing off", un)
                import asyncio as _aio
                await _aio.sleep(2.0)
            if (r0.status_code in SUSPECT_CODES or r1.status_code in SUSPECT_CODES) and r1.status_code != 404:
                evidence = f"unauth={r0.status_code} auth={r1.status_code}"
                score = 0.5 if r0.status_code == 200 else 0.35
                self.db.add_finding_for_url(un, type_="force_browse", evidence=evidence, score=score)