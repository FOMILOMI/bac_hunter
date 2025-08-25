from __future__ import annotations
import logging
import re
from typing import List, Set
from urllib.parse import urljoin, urlparse

from ...core.storage import Storage
from ...core.http_client import HttpClient
from ...config import Settings
from ..base import Plugin

log = logging.getLogger("recon.js")

JS_PATH_RE = re.compile(r"['\"](/?[A-Za-z0-9_\-/\.]+?(?:\.php|\.aspx|\.jsp|/api/[^'\"\s]+|/v1/[^'\"\s]+|/v2/[^'\"\s]+|/admin[^'\"\s]*))['\"]")
API_HINT_RE = re.compile(r"['\"](/api/[^'\"]+)['\"]")


class JSEndpointsRecon(Plugin):
    name = "js-endpoints"
    category = "recon"

    async def run(self, base_url: str, target_id: int) -> List[str]:
        start = base_url if base_url.endswith("/") else base_url + "/"
        collected: Set[str] = set()
        r = await self.http.get(start)
        self.db.save_page(target_id, start, r.status_code, r.headers.get("content-type"), r.content)
        if r.status_code == 200 and r.text:
            collected |= self._extract_paths(r.text, base_url)
            for src in re.findall(r"<script[^>]+src=\"([^\"]+)\"", r.text, flags=re.I):
                full = urljoin(base_url, src)
                try:
                    jr = await self.http.get(full)
                    self.db.save_page(target_id, full, jr.status_code, jr.headers.get("content-type"), jr.content)
                    if jr.status_code == 200 and jr.text:
                        collected |= self._extract_paths(jr.text, base_url)
                except Exception:
                    continue
        for url in sorted(collected):
            self.db.add_finding(target_id, "endpoint", url, evidence="js-scan", score=0.3)
        log.info("%s -> %d endpoints", self.name, len(collected))
        return sorted(collected)

    def _extract_paths(self, text: str, base_url: str) -> Set[str]:
        out: Set[str] = set()
        for m in JS_PATH_RE.finditer(text):
            path = m.group(1)
            if not path:
                continue
            out.add(urljoin(base_url, path))
        for m in API_HINT_RE.finditer(text):
            out.add(urljoin(base_url, m.group(1)))
        return out

