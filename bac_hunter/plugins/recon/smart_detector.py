from __future__ import annotations
import logging
import re
from typing import List, Set
from urllib.parse import urljoin

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

log = logging.getLogger("recon.smart")

# Common sensitive/admin paths and API patterns
ADMIN_CANDIDATES = [
    "/admin", "/admin/", "/administrator/", "/admin/login", "/admin/dashboard",
    "/wp-admin/", "/user/admin", "/manage/", "/management/", "/dashboard/",
    "/internal/", "/console/", "/actuator/", "/_admin",
]
API_CANDIDATES = [
    "/api/", "/api/v1/", "/api/v2/", "/v1/", "/v2/", "/graphql",
]

# Regex to extract likely endpoints from HTML/JS content
ENDPOINT_RE = re.compile(r"['\"](/?(?:[A-Za-z0-9_\-/.]*?(?:/admin[^'\"\s]*|/api/[^'\"\s]+|/v[0-9]+/[^'\"\s]+|[A-Za-z0-9_\-]+\.(?:php|aspx|jsp))))['\"]")


class SmartEndpointDetector(Plugin):
    name = "smart-endpoints"
    category = "recon"

    async def run(self, base_url: str, target_id: int) -> List[str]:
        collected: Set[str] = set()
        start_url = base_url if base_url.endswith("/") else base_url + "/"

        # 1) Fetch homepage and extract candidates
        try:
            r = await self.http.get(start_url)
            self.db.save_page(target_id, start_url, r.status_code, r.headers.get("content-type"), r.content)
            if r.status_code == 200 and r.text:
                for m in ENDPOINT_RE.finditer(r.text):
                    u = urljoin(base_url, m.group(1))
                    # normalize and skip recursive duplicates like /admin/admin
                    try:
                        from ...utils import normalize_url, is_recursive_duplicate_path
                    except Exception:
                        from utils import normalize_url, is_recursive_duplicate_path
                    u_n = normalize_url(u)
                    if is_recursive_duplicate_path(u_n.split('://',1)[-1].split('/',1)[-1] if '://' in u_n else u_n):
                        if getattr(self.settings, 'smart_dedup_enabled', False):
                            log.info("[SKIP] Duplicate endpoint %s", u_n)
                        continue
                    collected.add(u_n)
        except Exception as e:
            log.debug("homepage fetch failed: %s", e)

        # 2) Probe known admin/API candidates conservatively
        for path in ADMIN_CANDIDATES + API_CANDIDATES:
            url = urljoin(base_url, path)
            try:
                from ...utils import normalize_url, is_recursive_duplicate_path
            except Exception:
                from utils import normalize_url, is_recursive_duplicate_path
            url_n = normalize_url(url)
            if is_recursive_duplicate_path(url_n.split('://',1)[-1].split('/',1)[-1] if '://' in url_n else url_n):
                if getattr(self.settings, 'smart_dedup_enabled', False):
                    log.info("[SKIP] Duplicate endpoint %s", url_n)
                continue
            if url_n in collected:
                continue
            try:
                resp = await self.http.get(url_n)
                # Record pages lightly; only store body for 2xx text to avoid bloat
                content_type = resp.headers.get("content-type", "")
                body_bytes = resp.content if (resp.status_code < 400 and content_type.lower().startswith("text/")) else b""
                self.db.save_page(target_id, url_n, resp.status_code, content_type, body_bytes)
                if resp.status_code in (200, 401, 403):
                    collected.add(url_n)
                if getattr(self.settings, 'smart_backoff_enabled', False) and resp.status_code == 429:
                    log.warning("[!] Rate limited (429) on %s, backing off", url_n)
                    import asyncio as _aio
                    await _aio.sleep(2.0)
            except Exception:
                continue

        # 3) Persist findings with basic risk scoring
        for u in sorted(collected):
            score = 0.6 if any(seg in u.lower() for seg in ("/admin", "/manage", "/dashboard", "/internal")) else 0.4
            self.db.add_finding(target_id, "endpoint", u, evidence="smart-detector", score=score)
        log.info("%s -> %d endpoints", self.name, len(collected))
        return sorted(collected)