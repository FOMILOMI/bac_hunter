from __future__ import annotations
import logging
import re
from typing import List, Set
from urllib.parse import urljoin, urlparse

try:
	from ...storage import Storage
	from ...http_client import HttpClient
	from ...config import Settings
	from ..base import Plugin
except Exception:
	from storage import Storage
	from http_client import HttpClient
	from config import Settings
	from plugins.base import Plugin

log = logging.getLogger("recon.js")

JS_PATH_RE = re.compile(r"['\"](/?[A-Za-z0-9_\-/\.]+?(?:\.php|\.aspx|\.jsp|/api/[^'\"\s]+|/v1/[^'\"\s]+|/v2/[^'\"\s]+|/admin[^'\"\s]*))['\"]")
API_HINT_RE = re.compile(r"['\"](/api/[^'\"]+)['\"]")
# SPA router patterns (React Router paths, Angular route path:, Next.js chunks)
ROUTER_PATH_RE = re.compile(r"path\s*:\s*['\"](/[^'\"]+)['\"]|to\s*:\s*['\"](/[^'\"]+)['\"]|href\s*:\s*['\"](/[^'\"]+)['\"]")
NEXT_CHUNK_PATH_RE = re.compile(r"/app/[^'\"]+/page\.(?:js|tsx)")
ADMIN_HINT_RE = re.compile(r"/(admin|internal|manage|settings|reports|billing|users?/\:?[a-zA-Z_]+|tenants?/\:?[a-zA-Z_]+)", re.I)


class JSEndpointsRecon(Plugin):
    name = "js-endpoints"
    category = "recon"

    async def run(self, base_url: str, target_id: int) -> List[str]:
        # fetch homepage and linked JS (limited)
        start = base_url if base_url.endswith("/") else base_url + "/"
        collected: Set[str] = set()
        # Step 1: homepage
        r = await self.http.get(start)
        self.db.save_page(target_id, start, r.status_code, r.headers.get("content-type"), r.content)
        if r.status_code == 200 and r.text:
            collected |= self._extract_paths(r.text, base_url)
            # find linked JS files
            for src in re.findall(r"<script[^>]+src=\"([^\"]+)\"", r.text, flags=re.I):
                full = urljoin(base_url, src)
                try:
                    jr = await self.http.get(full)
                    self.db.save_page(target_id, full, jr.status_code, jr.headers.get("content-type"), jr.content)
                    if jr.status_code == 200 and jr.text:
                        collected |= self._extract_paths(jr.text, base_url)
                except Exception:
                    continue
        # Normalize, dedup, skip recursive nonsense
        try:
            from ...utils import normalize_url, is_recursive_duplicate_path
        except Exception:
            from utils import normalize_url, is_recursive_duplicate_path
        final = []
        seen = set()
        for u in sorted(collected):
            un = normalize_url(u)
            if is_recursive_duplicate_path(un.split('://',1)[-1].split('/',1)[-1] if '://' in un else un):
                if getattr(self.settings, 'smart_dedup_enabled', False):
                    log.info("[SKIP] Duplicate endpoint %s", un)
                continue
            if un in seen:
                if getattr(self.settings, 'smart_dedup_enabled', False):
                    log.info("[SKIP] Duplicate endpoint %s", un)
                continue
            seen.add(un)
            final.append(un)
            # priority score based on admin hints
            score = 0.35 if ADMIN_HINT_RE.search(un) else 0.3
            self.db.add_finding(target_id, "endpoint", un, evidence="js-scan", score=score)
        log.info("%s -> %d endpoints", self.name, len(final))
        return final

    def _extract_paths(self, text: str, base_url: str) -> Set[str]:
        out: Set[str] = set()
        for m in JS_PATH_RE.finditer(text):
            path = m.group(1)
            if not path:
                continue
            out.add(urljoin(base_url, path))
        for m in API_HINT_RE.finditer(text):
            out.add(urljoin(base_url, m.group(1)))
        # SPA router route strings
        for m in ROUTER_PATH_RE.finditer(text):
            for i in range(1, 4):
                val = m.group(i)
                if val and val.startswith('/'):
                    out.add(urljoin(base_url, val))
        # Next.js app router chunks imply routes (best effort)
        for m in NEXT_CHUNK_PATH_RE.finditer(text):
            chunk = m.group(0)
            if chunk:
                try:
                    # Derive path from chunk path
                    p = '/' + '/'.join(chunk.split('/')[2:-1])
                    out.add(urljoin(base_url, p))
                except Exception:
                    pass
        return out

